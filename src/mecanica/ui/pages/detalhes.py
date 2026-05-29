"""Client service history page."""

from __future__ import annotations

import json
from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk
from CTkTable import CTkTable

from src.mecanica.database.repositories import ServicoRepo
from src.mecanica.domain.formatters import fmt_moeda
from src.mecanica.domain.pagamento import FILTRO_STATUS_MAP, status_pagamento
from src.mecanica.relatorios.ordem_html import abrir_impressao
from src.mecanica.theme import (
    COR_FUNDO, COR_PERIGO,
    COR_SIDEBAR, COR_SIDEBAR_HOVER, COR_TEXTO_ESCURO,
    COR_INPUT_BG, COR_SELECIONADA,
    FONTE_BTN, FONTE_LABEL, FONTE_LABEL_NORMAL, FONTE_TITULO,
)
from src.mecanica.ui.modais import ModalServico

if TYPE_CHECKING:
    from src.mecanica.app import AppOficina

_HEADERS = ["ID", "Data", "Placa", "Veículo", "Ano", "Total (R$)", "Pago (R$)", "Status"]
_COL_WIDTHS = [45, 90, 85, 150, 60, 100, 100, 115]
_STATUS_COL = 7   # index of "Status" column (0-based)

# Status text colors
_STATUS_COLORS = {
    "pago":    "#1A7A3C",
    "naopago": "#C0392B",
    "parcial": "#B45309",
}


class PaginaDetalhes:
    def __init__(self, app: "AppOficina"):
        self.app = app
        self.table: CTkTable | None = None
        self.frame_tab: ctk.CTkScrollableFrame | None = None
        self.filtro_busca = None
        self.filtro_status = None
        self._servicos: list = []
        self._status_tags: list[str] = []       # "pago" | "naopago" | "parcial" per row
        self._selected_row: int | None = None
        self._row_colors: list[str] = []
        self._cliente_id = None
        self._debounce_busca = None

    def montar(self, container: ctk.CTkFrame) -> None:
        id_cli, nome, cpf, end, cid, tel = self.app.cliente_selecionado
        self._cliente_id = id_cli

        main = ctk.CTkFrame(container, fg_color=COR_FUNDO, corner_radius=0)
        main.grid(row=0, column=0, sticky="nsew", padx=27, pady=29)
        main.grid_rowconfigure(2, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # Title row — right-side buttons packed FIRST to prevent long names from pushing them off
        topo = ctk.CTkFrame(main, fg_color="transparent")
        topo.grid(row=0, column=0, sticky="ew", pady=(0, 24))

        ctk.CTkButton(topo, text="🗑️  Excluir", font=FONTE_BTN,
                      fg_color=COR_PERIGO, hover_color="#C0392B",
                      height=40, corner_radius=8,
                      command=self._excluir).pack(side="right", padx=(8, 0))
        ctk.CTkButton(topo, text="✏️  Editar", font=FONTE_BTN,
                      fg_color="#6B7280", hover_color="#4B5563",
                      height=40, corner_radius=8,
                      command=self._abrir_edicao).pack(side="right", padx=(8, 0))
        ctk.CTkButton(topo, text="📄  Ver OS", font=FONTE_BTN,
                      fg_color="#2563EB", hover_color="#1D4ED8",
                      text_color="#fff",
                      height=40, corner_radius=8,
                      command=self._ver_os).pack(side="right", padx=(8, 0))
        ctk.CTkButton(topo, text="+ Novo Serviço", font=FONTE_BTN,
                      fg_color=COR_SIDEBAR, hover_color=COR_SIDEBAR_HOVER,
                      text_color="#fff",
                      height=40, corner_radius=8,
                      command=lambda: ModalServico(
                          self.app, id_cli, self._carregar
                      )).pack(side="right")
        ctk.CTkButton(topo, text="⬅  Voltar", font=FONTE_BTN, fg_color="#6B7280",
                      hover_color="#4B5563", height=40, corner_radius=8,
                      command=self.app.navegar_clientes).pack(side="left")
        nome_exibido = nome if len(nome) <= 24 else nome[:21] + "..."
        ctk.CTkLabel(topo, text=f"Histórico — {nome_exibido}", font=FONTE_TITULO,
                     text_color=COR_SIDEBAR).pack(side="left", padx=20)

        # Filter bar
        filtros = ctk.CTkFrame(main, fg_color=COR_INPUT_BG, corner_radius=0, height=50)
        filtros.grid(row=1, column=0, sticky="ew", pady=(0, 21))
        filtros.grid_propagate(False)

        ctk.CTkLabel(filtros, text="🔍", font=("Arial Bold", 20)).pack(
            side="left", padx=(13, 0), pady=15)
        self.filtro_busca = ctk.CTkEntry(
            filtros, placeholder_text="Buscar por Placa ou Serviço...",
            font=FONTE_LABEL_NORMAL, width=260, height=36,
            border_color=COR_SIDEBAR, border_width=2,
            fg_color=COR_INPUT_BG,
        )
        self.filtro_busca.pack(side="left", pady=7, padx=(8, 0))
        self.filtro_busca.bind("<KeyRelease>", self._on_busca_key)

        ctk.CTkLabel(filtros, text="  Status:", font=FONTE_LABEL,
                     text_color="#475569").pack(side="left", padx=(18, 4))
        self.filtro_status = ctk.CTkOptionMenu(
            filtros, font=FONTE_LABEL_NORMAL,
            values=["Todos", "Pago", "Parcial", "Não Pago"],
            fg_color=COR_INPUT_BG, text_color=COR_TEXTO_ESCURO,
            button_color=COR_SIDEBAR, button_hover_color=COR_SIDEBAR_HOVER,
            dropdown_fg_color="#fff", dropdown_text_color=COR_TEXTO_ESCURO,
            dropdown_hover_color=COR_SELECIONADA,
            command=lambda e: self._carregar(), height=36,
        )
        self.filtro_status.pack(side="left", pady=7)

        # Scrollable table container
        self.frame_tab = ctk.CTkScrollableFrame(main, fg_color="transparent")
        self.frame_tab.grid(row=2, column=0, sticky="nsew")

        self._carregar()

    # ------------------------------------------------------------------

    def _on_busca_key(self, event=None) -> None:
        if self._debounce_busca:
            self.app.after_cancel(self._debounce_busca)
        self._debounce_busca = self.app.after(400, self._carregar)

    def _carregar(self) -> None:
        termo = self.filtro_busca.get() if self.filtro_busca else ""
        status_filtro = self.filtro_status.get() if self.filtro_status else "Todos"

        servicos = ServicoRepo.listar(self._cliente_id, termo)

        self._servicos = []
        self._status_tags = []

        rows_data = []
        for s in servicos:
            label, s_tag = status_pagamento(s.saldo, s.pago)
            if status_filtro != "Todos":
                if label != FILTRO_STATUS_MAP.get(status_filtro, ""):
                    continue
            self._servicos.append(s)
            self._status_tags.append(s_tag)
            rows_data.append([
                s.id, s.data, s.placa, s.veiculo or "", s.ano or "",
                fmt_moeda(s.saldo), fmt_moeda(s.pago), label,
            ])

        self._selected_row = None

        if self.table:
            self.table.destroy()
            self.table = None

        data = [_HEADERS] + rows_data

        # Cache alternating row bg colors
        self._row_colors = []
        for i in range(1, len(data)):
            self._row_colors.append("#E6E6E6" if (i % 2 == 1) else "#EEEEEE")

        self.table = CTkTable(
            master=self.frame_tab,
            values=data,
            colors=["#E6E6E6", "#EEEEEE"],
            header_color=COR_SIDEBAR,
            hover_color="#B4B4B4",
            command=self._ao_clicar,
            height=45,
            wraplength=0,
        )
        self.table.edit_row(0, text_color="#fff", hover_color=COR_SIDEBAR)
        self.table.pack(expand=True, fill="x")

        for col_idx, width in enumerate(_COL_WIDTHS):
            self.table.grid_columnconfigure(col_idx, minsize=width)

        # Per-row status color (Status column)
        for i, tag in enumerate(self._status_tags, start=1):
            color = _STATUS_COLORS.get(tag)
            if color:
                try:
                    cell = self.table.grid_slaves(row=i, column=_STATUS_COL)
                    if cell:
                        cell[0].configure(text_color=color)
                except Exception:
                    pass

    def _ao_clicar(self, cell_info: dict) -> None:
        row = cell_info["row"]
        if row == 0 or not self.table:
            return

        idx = row - 1
        if idx >= len(self._servicos):
            return

        # De-highlight previous
        if self._selected_row is not None and self._selected_row != row:
            prev_color = self._row_colors[self._selected_row - 1]
            self.table.edit_row(self._selected_row,
                                fg_color=prev_color, hover_color="#B4B4B4",
                                text_color="#000000")
            # Restore status color on previously selected row
            prev_idx = self._selected_row - 1
            if prev_idx < len(self._status_tags):
                tag = self._status_tags[prev_idx]
                color = _STATUS_COLORS.get(tag)
                if color:
                    try:
                        cell = self.table.grid_slaves(
                            row=self._selected_row, column=_STATUS_COL)
                        if cell:
                            cell[0].configure(text_color=color)
                    except Exception:
                        pass

        # Highlight selected
        self.table.edit_row(row, fg_color=COR_SELECIONADA,
                            hover_color=COR_SELECIONADA, text_color="#166534")
        self._selected_row = row

    def _abrir_edicao(self) -> None:
        if self._selected_row is None:
            messagebox.showinfo("Aviso", "Clique em uma linha para selecionar o serviço.")
            return
        idx = self._selected_row - 1
        if idx >= len(self._servicos):
            return
        s = self._servicos[idx]
        label, _ = status_pagamento(s.saldo, s.pago)
        # indices: 0=id, 1=data, 2=placa, 3=veiculo, 4=ano,
        #          5=servico, 6=saldo, 7=pago, 8=status, 9=comentario
        vals = (s.id, s.data, s.placa, s.veiculo or "", s.ano or "",
                s.servico, fmt_moeda(s.saldo), fmt_moeda(s.pago), label, s.comentario)
        ModalServico(self.app, self._cliente_id, self._carregar, editar=vals)

    def _ver_os(self) -> None:
        if self._selected_row is None:
            messagebox.showinfo("Aviso", "Clique em uma linha para selecionar um serviço.")
            return
        idx = self._selected_row - 1
        if idx >= len(self._servicos):
            return
        s = self._servicos[idx]
        if not s.ordem_json:
            messagebox.showinfo(
                "Sem OS vinculada",
                "Este serviço não possui Ordem de Serviço vinculada.\n\n"
                "Apenas serviços criados pela aba Ordem de Serviço têm esse vínculo.",
            )
            return
        try:
            dados = json.loads(s.ordem_json)
            abrir_impressao(dados)
        except Exception:
            messagebox.showerror("Erro", "Não foi possível abrir a Ordem de Serviço.")

    def _excluir(self) -> None:
        if self._selected_row is None:
            messagebox.showinfo("Aviso", "Clique em uma linha para selecionar o serviço.")
            return
        idx = self._selected_row - 1
        if idx >= len(self._servicos):
            return
        s = self._servicos[idx]
        if messagebox.askyesno("Confirmar",
                               f"Excluir o serviço:\n\n\"{s.servico}\"?\n\nEsta ação não pode ser desfeita."):
            ServicoRepo.excluir(s.id)
            self._carregar()
