"""Clients list page."""

from __future__ import annotations

from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

import customtkinter as ctk

from src.mecanica.config import MIN_LINHAS_CLIENTES
from src.mecanica.database.repositories import ClienteRepo
from src.mecanica.theme import (
    COR_AZUL_CARD, COR_CARD, COR_FUNDO, COR_LARANJA_CARD,
    COR_PERIGO, COR_SIDEBAR, COR_SIDEBAR_HOVER, COR_TEXTO_ESCURO,
    COR_VERDE_CARD, FONTE_BTN, FONTE_LABEL_NORMAL, FONTE_TITULO,
)
from src.mecanica.ui.modais import ModalNovoCliente
from src.mecanica.ui.widgets import CardEstatistica

if TYPE_CHECKING:
    from src.mecanica.app import AppOficina


class PaginaClientes:
    def __init__(self, app: "AppOficina"):
        self.app = app
        self.tree_cli = None
        self.entry_busca = None
        self.card_total = None
        self.card_pagos = None
        self.card_abertos = None

    def montar(self, container: ctk.CTkFrame) -> None:
        main = ctk.CTkFrame(container, fg_color=COR_FUNDO, corner_radius=0)
        main.grid(row=0, column=0, sticky="nsew", padx=28, pady=24)
        main.grid_rowconfigure(3, weight=1)
        main.grid_columnconfigure(0, weight=1)

        linha_titulo = ctk.CTkFrame(main, fg_color="transparent")
        linha_titulo.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ctk.CTkLabel(linha_titulo, text="Meus Clientes", font=FONTE_TITULO,
                     text_color=COR_TEXTO_ESCURO).pack(side="left")
        ctk.CTkButton(linha_titulo, text="🗑️  Excluir Cliente", font=FONTE_BTN,
                      fg_color=COR_PERIGO, hover_color="#C0392B",
                      height=44, corner_radius=10,
                      command=self._excluir).pack(side="right", padx=(10, 0))
        ctk.CTkButton(linha_titulo, text="➕  Novo Cliente", font=FONTE_BTN,
                      fg_color=COR_SIDEBAR, hover_color=COR_SIDEBAR_HOVER,
                      height=44, corner_radius=10,
                      command=lambda: ModalNovoCliente(self.app, self._carregar)).pack(
                          side="right", padx=(0, 10))

        row_cards = ctk.CTkFrame(main, fg_color="transparent")
        row_cards.grid(row=1, column=0, sticky="ew", pady=(0, 22))

        self.card_total   = CardEstatistica(row_cards, "👥", "Total Clientes", "0", COR_VERDE_CARD)
        self.card_pagos   = CardEstatistica(row_cards, "✅", "Serviços Pagos",  "0", COR_AZUL_CARD)
        self.card_abertos = CardEstatistica(row_cards, "⏳", "Em Aberto",       "0", COR_LARANJA_CARD)
        self.card_total.pack(side="left", padx=(0, 14))
        self.card_pagos.pack(side="left", padx=(0, 14))
        self.card_abertos.pack(side="left")

        row_busca = ctk.CTkFrame(main, fg_color=COR_CARD, corner_radius=12)
        row_busca.grid(row=2, column=0, sticky="ew", pady=(0, 16), ipady=10)
        row_busca.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(row_busca, text="🔍", font=("Segoe UI", 18)).grid(row=0, column=0, padx=(16, 6))
        self.entry_busca = ctk.CTkEntry(row_busca, placeholder_text="Buscar cliente por nome...",
                                        font=FONTE_LABEL_NORMAL, height=42, border_width=0,
                                        fg_color="transparent")
        self.entry_busca.grid(row=0, column=1, sticky="ew", pady=6, padx=(0, 16))
        self.entry_busca.bind("<KeyRelease>", lambda e: self._carregar())

        frame_tab = ctk.CTkFrame(main, fg_color=COR_CARD, corner_radius=14,
                                  border_width=2, border_color="#888888")
        frame_tab.grid(row=3, column=0, sticky="nsew")
        frame_tab.grid_rowconfigure(0, weight=1)
        frame_tab.grid_columnconfigure(0, weight=1)

        colunas = ("ID", "Nome", "CPF", "Placa", "Endereço", "Cidade", "Telefone")
        self.tree_cli = ttk.Treeview(frame_tab, columns=colunas, show="headings", selectmode="browse")
        configs = [("ID", 50, "center"), ("Nome", 210, "w"), ("CPF", 120, "center"),
                   ("Placa", 90, "center"), ("Endereço", 200, "w"),
                   ("Cidade", 120, "w"), ("Telefone", 120, "center")]
        for col, larg, anc in configs:
            self.tree_cli.heading(col, text=col)
            self.tree_cli.column(col, width=larg, minwidth=larg, anchor=anc)

        self.tree_cli.grid(row=0, column=0, sticky="nsew", padx=(4, 0), pady=4)
        self.tree_cli.bind("<Double-1>", self._abrir_cliente)

        sb = ctk.CTkScrollbar(frame_tab, orientation="vertical", command=self.tree_cli.yview)
        self.tree_cli.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns", pady=4, padx=(0, 4))

        self.tree_cli.tag_configure("par",   background=COR_CARD)
        self.tree_cli.tag_configure("impar", background="#EFF3F1")

        self._carregar()

    def _carregar(self) -> None:
        for r in self.tree_cli.get_children():
            self.tree_cli.delete(r)

        termo = self.entry_busca.get() if self.entry_busca else ""
        clientes = ClienteRepo.listar(termo)
        pagos, abertos = ClienteRepo.contar_servicos_status()

        self.card_total.atualizar(len(clientes))
        self.card_pagos.atualizar(pagos)
        self.card_abertos.atualizar(abertos)

        for i, cli in enumerate(clientes):
            tag = "par" if i % 2 == 0 else "impar"
            self.tree_cli.insert("", "end",
                                 values=(cli.id, cli.nome, cli.cpf, cli.placa or "",
                                         cli.endereco, cli.cidade, cli.telefone),
                                 tags=(tag,))

        # Keep spreadsheet appearance with a minimum number of rows
        for i in range(len(clientes), MIN_LINHAS_CLIENTES):
            tag = "par" if i % 2 == 0 else "impar"
            self.tree_cli.insert("", "end", values=("", "", "", "", "", "", ""), tags=(tag,))

    def _abrir_cliente(self, event) -> None:
        item = self.tree_cli.selection()
        if not item:
            return
        vals = self.tree_cli.item(item, "values")
        id_, nome, cpf, placa, endereco, cidade, telefone = vals
        if not str(id_).strip().isdigit():
            return
        self.app.cliente_selecionado = (id_, nome, cpf, endereco, cidade, telefone)
        self.app.navegar_detalhes()

    def _excluir(self) -> None:
        sel = self.tree_cli.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um cliente na tabela para excluir.")
            return

        vals = self.tree_cli.item(sel, "values")
        id_cli  = str(vals[0]).strip()
        nome_cli = str(vals[1]).strip()

        if not id_cli.isdigit():
            messagebox.showwarning("Aviso", "Selecione um cliente válido na tabela para excluir.")
            return

        if not messagebox.askyesno(
            "Confirmar",
            f"Excluir o cliente:\n\n\"{nome_cli}\"?\n\n"
            "Todos os serviços vinculados a este cliente também serão excluídos.\n\n"
            "Esta ação não pode ser desfeita.",
        ):
            return

        ClienteRepo.excluir(id_cli)
        self._carregar()
