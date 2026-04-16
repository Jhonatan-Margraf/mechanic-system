"""Client service history page."""

from __future__ import annotations

from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

import customtkinter as ctk

from src.mecanica.database.repositories import ServicoRepo
from src.mecanica.domain.formatters import fmt_moeda
from src.mecanica.domain.pagamento import FILTRO_STATUS_MAP, status_pagamento
from src.mecanica.theme import (
    COR_CARD, COR_FUNDO, COR_PERIGO,
    COR_SIDEBAR, COR_SIDEBAR_HOVER, COR_TEXTO_ESCURO, COR_TEXTO_MEDIO,
    FONTE_BTN, FONTE_LABEL, FONTE_LABEL_NORMAL, FONTE_TITULO,
)
from src.mecanica.ui.modais import ModalServico

if TYPE_CHECKING:
    from src.mecanica.app import AppOficina


class PaginaDetalhes:
    def __init__(self, app: "AppOficina"):
        self.app = app
        self.tree_serv = None
        self.filtro_busca = None
        self.filtro_status = None

    def montar(self, container: ctk.CTkFrame) -> None:
        id_cli, nome, cpf, end, cid, tel = self.app.cliente_selecionado

        main = ctk.CTkFrame(container, fg_color=COR_FUNDO, corner_radius=0)
        main.grid(row=0, column=0, sticky="nsew", padx=28, pady=24)
        main.grid_rowconfigure(2, weight=1)
        main.grid_columnconfigure(0, weight=1)

        topo = ctk.CTkFrame(main, fg_color="transparent")
        topo.grid(row=0, column=0, sticky="ew", pady=(0, 18))

        ctk.CTkButton(topo, text="⬅  Voltar", font=FONTE_BTN, fg_color="#AAAAAA",
                      hover_color="#888888", height=42, corner_radius=10,
                      command=self.app.navegar_clientes).pack(side="left")
        ctk.CTkLabel(topo, text=f"Histórico — {nome}", font=FONTE_TITULO,
                     text_color=COR_TEXTO_ESCURO).pack(side="left", padx=20)
        ctk.CTkButton(topo, text="🗑️  Excluir Serviço", font=FONTE_BTN,
                      fg_color=COR_PERIGO, hover_color="#C0392B",
                      height=42, corner_radius=10,
                      command=self._excluir).pack(side="right")
        ctk.CTkButton(topo, text="➕  Novo Serviço", font=FONTE_BTN,
                      fg_color=COR_SIDEBAR, hover_color=COR_SIDEBAR_HOVER,
                      height=42, corner_radius=10,
                      command=lambda: ModalServico(
                          self.app, id_cli, self._carregar
                      )).pack(side="right", padx=(0, 10))

        filtros = ctk.CTkFrame(main, fg_color=COR_CARD, corner_radius=12)
        filtros.grid(row=1, column=0, sticky="ew", pady=(0, 16), ipady=8)

        ctk.CTkLabel(filtros, text="🔍", font=("Segoe UI", 18)).pack(side="left", padx=(16, 4), pady=8)
        self.filtro_busca = ctk.CTkEntry(filtros, placeholder_text="Buscar por Placa ou Serviço...",
                                         font=FONTE_LABEL_NORMAL, width=280, height=40, border_width=0,
                                         fg_color="transparent")
        self.filtro_busca.pack(side="left", pady=8)
        self.filtro_busca.bind("<KeyRelease>", lambda e: self._carregar())

        ctk.CTkLabel(filtros, text="  Status:", font=FONTE_LABEL,
                     text_color=COR_TEXTO_MEDIO).pack(side="left", padx=(18, 4))
        self.filtro_status = ctk.CTkOptionMenu(
            filtros, font=FONTE_LABEL_NORMAL,
            values=["Todos", "Pago", "Parcial", "Não Pago"],
            fg_color="#F0F2F5", text_color=COR_TEXTO_ESCURO,
            button_color=COR_SIDEBAR, button_hover_color=COR_SIDEBAR_HOVER,
            command=lambda e: self._carregar(), height=40)
        self.filtro_status.pack(side="left", pady=8)

        frame_tab = ctk.CTkFrame(main, fg_color=COR_CARD, corner_radius=14,
                                  border_width=2, border_color="#888888")
        frame_tab.grid(row=2, column=0, sticky="nsew")
        frame_tab.grid_rowconfigure(0, weight=1)
        frame_tab.grid_columnconfigure(0, weight=1)

        colunas = ("ID", "Data", "Placa", "Serviço", "Total (R$)", "Pago (R$)", "Status", "Comentário")
        self.tree_serv = ttk.Treeview(frame_tab, columns=colunas, show="headings", selectmode="browse")
        configs = [("ID", 45, "center"), ("Data", 95, "center"), ("Placa", 90, "center"),
                   ("Serviço", 210, "w"), ("Total (R$)", 95, "center"), ("Pago (R$)", 95, "center"),
                   ("Status", 115, "center"), ("Comentário", 230, "w")]
        for col, larg, anc in configs:
            self.tree_serv.heading(col, text=col)
            self.tree_serv.column(col, width=larg, minwidth=larg, anchor=anc)

        self.tree_serv.grid(row=0, column=0, sticky="nsew", padx=(4, 0), pady=4)
        self.tree_serv.bind("<Double-1>", self._abrir_edicao)

        sb = ctk.CTkScrollbar(frame_tab, orientation="vertical", command=self.tree_serv.yview)
        self.tree_serv.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns", pady=4, padx=(0, 4))

        self.tree_serv.tag_configure("par",     background=COR_CARD)
        self.tree_serv.tag_configure("impar",   background="#EFF3F1")
        self.tree_serv.tag_configure("pago",    foreground="#1A7A3C")
        self.tree_serv.tag_configure("naopago", foreground="#C0392B")
        self.tree_serv.tag_configure("parcial", foreground="#D68910")

        self._carregar()

    def _carregar(self) -> None:
        for r in self.tree_serv.get_children():
            self.tree_serv.delete(r)

        cliente_id = self.app.cliente_selecionado[0]
        termo = self.filtro_busca.get() if self.filtro_busca else ""
        status_filtro = self.filtro_status.get() if self.filtro_status else "Todos"

        servicos = ServicoRepo.listar(cliente_id, termo)

        idx = 0
        for s in servicos:
            label, s_tag = status_pagamento(s.saldo, s.pago)

            if status_filtro != "Todos":
                if label != FILTRO_STATUS_MAP.get(status_filtro, ""):
                    continue

            tag_linha = "par" if idx % 2 == 0 else "impar"
            self.tree_serv.insert("", "end",
                                  values=(s.id, s.data, s.placa, s.servico,
                                          fmt_moeda(s.saldo), fmt_moeda(s.pago),
                                          label, s.comentario),
                                  tags=(tag_linha, s_tag))
            idx += 1

    def _abrir_edicao(self, event) -> None:
        sel = self.tree_serv.selection()
        if not sel:
            return
        vals = self.tree_serv.item(sel, "values")
        cliente_id = self.app.cliente_selecionado[0]
        ModalServico(self.app, cliente_id, self._carregar, editar=vals)

    def _excluir(self) -> None:
        sel = self.tree_serv.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um serviço na tabela para excluir.")
            return
        vals = self.tree_serv.item(sel, "values")
        if messagebox.askyesno("Confirmar",
                               f"Excluir o serviço:\n\n\"{vals[3]}\"?\n\nEsta ação não pode ser desfeita."):
            ServicoRepo.excluir(vals[0])
            self._carregar()
