"""Clients list page."""

from __future__ import annotations

from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk
from CTkTable import CTkTable

from src.mecanica.config import MIN_LINHAS_CLIENTES
from src.mecanica.database.repositories import ClienteRepo
from src.mecanica.theme import (
    COR_AZUL_CARD, COR_FUNDO, COR_LARANJA_CARD,
    COR_PERIGO, COR_SIDEBAR, COR_SIDEBAR_HOVER,
    COR_VERDE_CARD, COR_INPUT_BG, COR_SELECIONADA,
    FONTE_BTN, FONTE_LABEL_NORMAL, FONTE_TITULO,
)
from src.mecanica.ui.modais import ModalNovoCliente
from src.mecanica.ui.widgets import CardEstatistica

if TYPE_CHECKING:
    from src.mecanica.app import AppOficina

_HEADERS = ["ID", "Nome", "CPF", "Placa", "Endereço", "Cidade", "Telefone"]
_COL_WIDTHS = [50, 180, 110, 85, 180, 115, 110]


def _truncar(texto: str, max_chars: int) -> str:
    s = str(texto)
    return s[:max_chars] + "…" if len(s) > max_chars else s


class PaginaClientes:
    def __init__(self, app: "AppOficina"):
        self.app = app
        self.table: CTkTable | None = None
        self.frame_tab: ctk.CTkScrollableFrame | None = None
        self.entry_busca = None
        self.card_total = None
        self.card_pagos = None
        self.card_abertos = None
        self._clientes: list = []
        self._selected_row: int | None = None   # 1-based row index in table
        self._row_colors: list[str] = []        # cached row bg colors for de-select
        self._last_cell_col: int | None = None  # last clicked column index
        self._toast_lbl: ctk.CTkLabel | None = None
        self._toast_job = None
        self._debounce_busca = None

    def montar(self, container: ctk.CTkFrame) -> None:
        main = ctk.CTkFrame(container, fg_color=COR_FUNDO, corner_radius=0)
        main.grid(row=0, column=0, sticky="nsew", padx=27, pady=29)
        main.grid_rowconfigure(3, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # Title row — buttons packed side="right" FIRST to prevent label from pushing them off
        linha_titulo = ctk.CTkFrame(main, fg_color="transparent")
        linha_titulo.grid(row=0, column=0, sticky="ew", pady=(0, 36))
        ctk.CTkButton(linha_titulo, text="🗑️  Excluir", font=FONTE_BTN,
                      fg_color=COR_PERIGO, hover_color="#C0392B",
                      height=40, corner_radius=8,
                      command=self._excluir).pack(side="right", padx=(8, 0))
        ctk.CTkButton(linha_titulo, text="✏️  Editar", font=FONTE_BTN,
                      fg_color="#6B7280", hover_color="#4B5563",
                      height=40, corner_radius=8,
                      command=self._editar_selecionado).pack(side="right", padx=(8, 0))
        ctk.CTkButton(linha_titulo, text="📂  Abrir", font=FONTE_BTN,
                      fg_color="#6B7280", hover_color="#4B5563",
                      height=40, corner_radius=8,
                      command=self._abrir_selecionado).pack(side="right", padx=(8, 0))
        ctk.CTkButton(linha_titulo, text="+ Novo Cliente", font=FONTE_BTN,
                      fg_color=COR_SIDEBAR, hover_color=COR_SIDEBAR_HOVER,
                      text_color="#fff",
                      height=40, corner_radius=8,
                      command=lambda: ModalNovoCliente(self.app, self._carregar)).pack(
                          side="right")
        ctk.CTkLabel(linha_titulo, text="Meus Clientes", font=FONTE_TITULO,
                     text_color=COR_SIDEBAR).pack(side="left")

        # Stat cards
        row_cards = ctk.CTkFrame(main, fg_color="transparent")
        row_cards.grid(row=1, column=0, sticky="ew", pady=(0, 45))

        self.card_total   = CardEstatistica(row_cards, "👥", "Total Clientes", "0", COR_VERDE_CARD)
        self.card_pagos   = CardEstatistica(row_cards, "✅", "Serviços Pagos",  "0", COR_AZUL_CARD)
        self.card_abertos = CardEstatistica(row_cards, "⏳", "Em Aberto",       "0", COR_LARANJA_CARD)
        self.card_total.pack(side="left", padx=(0, 14))
        self.card_pagos.pack(side="left", padx=(0, 14))
        self.card_abertos.pack(side="left")

        # Search bar
        row_busca = ctk.CTkFrame(main, fg_color=COR_INPUT_BG, corner_radius=0, height=50)
        row_busca.grid(row=2, column=0, sticky="ew", pady=(0, 21))
        row_busca.grid_columnconfigure(1, weight=1)
        row_busca.grid_propagate(False)
        ctk.CTkLabel(row_busca, text="🔍", font=("Arial Bold", 20)).grid(
            row=0, column=0, padx=(13, 0), pady=15)
        self.entry_busca = ctk.CTkEntry(
            row_busca, placeholder_text="Buscar cliente por nome...",
            font=FONTE_LABEL_NORMAL, height=36,
            border_color=COR_SIDEBAR, border_width=2,
            fg_color=COR_INPUT_BG,
        )
        self.entry_busca.grid(row=0, column=1, sticky="ew", pady=7, padx=(8, 13))
        self.entry_busca.bind("<KeyRelease>", self._on_busca_key)

        # Scrollable table container
        self.frame_tab = ctk.CTkScrollableFrame(main, fg_color="transparent")
        self.frame_tab.grid(row=3, column=0, sticky="nsew")

        # Toast notification area (hidden by default)
        self._toast_lbl = ctk.CTkLabel(
            main, text="", font=("Arial Bold", 12),
            fg_color="#166534", text_color="#fff", corner_radius=8,
        )

        self._carregar()

    # ------------------------------------------------------------------

    def _on_busca_key(self, event=None) -> None:
        if self._debounce_busca:
            self.app.after_cancel(self._debounce_busca)
        self._debounce_busca = self.app.after(400, self._carregar)

    def _carregar(self) -> None:
        termo = self.entry_busca.get() if self.entry_busca else ""
        clientes = ClienteRepo.listar(termo)
        pagos, abertos = ClienteRepo.contar_servicos_status()

        self.card_total.atualizar(len(clientes))
        self.card_pagos.atualizar(pagos)
        self.card_abertos.atualizar(abertos)

        self._clientes = clientes
        self._selected_row = None

        if self.table:
            self.table.destroy()
            self.table = None

        data = [_HEADERS]
        for cli in clientes:
            data.append([
                cli.id, _truncar(cli.nome, 22), cli.cpf, cli.placa or "",
                _truncar(cli.endereco, 22), cli.cidade, cli.telefone,
            ])

        while len(data) - 1 < MIN_LINHAS_CLIENTES:
            data.append(["", "", "", "", "", "", ""])

        # Cache row colors for selection highlighting (alternating)
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

        self._bind_na_tabela("<Double-Button-1>", self._duplo_clique_linha)
        self._bind_na_tabela("<Button-3>", self._mostrar_menu_contexto)
        self.app.bind_all("<Control-c>", self._copiar_selecionado)

    def _bind_na_tabela(self, evento: str, callback) -> None:
        def _rec(w):
            w.bind(evento, callback)
            for child in w.winfo_children():
                _rec(child)
        if self.table:
            _rec(self.table)

    def _ao_clicar(self, cell_info: dict) -> None:
        row = cell_info["row"]
        if row == 0 or not self.table:
            return

        idx = row - 1
        if idx >= len(self._clientes):
            # Empty padding row — deselect
            self._deselect()
            return

        self._last_cell_col = cell_info.get("column")

        # De-highlight previous selection
        if self._selected_row is not None and self._selected_row != row:
            prev_color = self._row_colors[self._selected_row - 1]
            self.table.edit_row(self._selected_row,
                                fg_color=prev_color, hover_color="#B4B4B4",
                                text_color="#000000")

        # Highlight selected row
        self.table.edit_row(row, fg_color=COR_SELECIONADA,
                            hover_color=COR_SELECIONADA, text_color="#166534")
        self._selected_row = row

    def _deselect(self) -> None:
        if self._selected_row is not None and self.table:
            prev_color = self._row_colors[self._selected_row - 1]
            self.table.edit_row(self._selected_row,
                                fg_color=prev_color, hover_color="#B4B4B4",
                                text_color="#000000")
        self._selected_row = None

    def _duplo_clique_linha(self, event=None) -> None:
        if self._selected_row is not None:
            self._abrir_selecionado()

    def _mostrar_toast(self, msg: str) -> None:
        if not self._toast_lbl:
            return
        if self._toast_job:
            try:
                self.app.after_cancel(self._toast_job)
            except Exception:
                pass
        self._toast_lbl.configure(text=f"  {msg}  ")
        self._toast_lbl.place(relx=0.5, rely=0.97, anchor="s")
        self._toast_job = self.app.after(2000, self._esconder_toast)

    def _esconder_toast(self) -> None:
        if self._toast_lbl:
            self._toast_lbl.place_forget()
        self._toast_job = None

    def _copiar_selecionado(self, event=None) -> None:
        import tkinter as tk
        focused = self.app.focus_get()
        if isinstance(focused, tk.Entry):
            return
        if self._selected_row is None or not self.table:
            return
        try:
            if not self.table.winfo_exists():
                return
        except Exception:
            return
        idx = self._selected_row - 1
        if idx >= len(self._clientes):
            return
        cli = self._clientes[idx]
        texto = "\t".join([
            cli.nome, cli.cpf or "", cli.placa or "",
            cli.endereco or "", cli.cidade or "", cli.telefone or "",
        ])
        self.app.clipboard_clear()
        self.app.clipboard_append(texto)
        self._mostrar_toast("✅ Linha copiada")

    def _mostrar_menu_contexto(self, event=None) -> None:
        import tkinter as tk
        if self._selected_row is None:
            return
        idx = self._selected_row - 1
        if idx >= len(self._clientes):
            return
        cli = self._clientes[idx]

        _CAMPOS = [
            str(cli.id), cli.nome, cli.cpf or "", cli.placa or "",
            cli.endereco or "", cli.cidade or "", cli.telefone or "",
        ]
        col = self._last_cell_col
        valor_celula = _CAMPOS[col] if col is not None and col < len(_CAMPOS) else ""

        def copiar_linha():
            texto = "\t".join([
                cli.nome, cli.cpf or "", cli.placa or "",
                cli.endereco or "", cli.cidade or "", cli.telefone or "",
            ])
            self.app.clipboard_clear()
            self.app.clipboard_append(texto)
            self._mostrar_toast("✅ Linha copiada")

        def copiar_celula():
            self.app.clipboard_clear()
            self.app.clipboard_append(valor_celula)
            self._mostrar_toast(f"✅ Copiado: {valor_celula[:30]}")

        menu = tk.Menu(self.app, tearoff=0)
        menu.add_command(label="Copiar linha (Ctrl+C)", command=copiar_linha)
        menu.add_command(label=f"Copiar célula: {valor_celula[:25]}", command=copiar_celula)
        menu.tk_popup(event.x_root, event.y_root)

    def _editar_selecionado(self) -> None:
        if self._selected_row is None:
            messagebox.showinfo("Aviso", "Clique em uma linha da tabela para selecionar um cliente.")
            return
        idx = self._selected_row - 1
        if idx >= len(self._clientes):
            return
        cli = self._clientes[idx]
        ModalNovoCliente(self.app, self._carregar, editar=cli)

    def _abrir_selecionado(self) -> None:
        if self._selected_row is None:
            messagebox.showinfo("Aviso", "Clique em uma linha da tabela para selecionar um cliente.")
            return
        idx = self._selected_row - 1
        if idx >= len(self._clientes):
            return
        cli = self._clientes[idx]
        self.app.cliente_selecionado = (
            cli.id, cli.nome, cli.cpf, cli.endereco, cli.cidade, cli.telefone
        )
        self.app.navegar_detalhes()

    def _excluir(self) -> None:
        if self._selected_row is None:
            messagebox.showinfo("Aviso", "Clique em uma linha da tabela para selecionar um cliente.")
            return
        idx = self._selected_row - 1
        if idx >= len(self._clientes):
            return
        cli = self._clientes[idx]

        if not messagebox.askyesno(
            "Confirmar",
            f"Excluir o cliente:\n\n\"{cli.nome}\"?\n\n"
            "Todos os serviços vinculados também serão excluídos.\n\n"
            "Esta ação não pode ser desfeita.",
        ):
            return

        ClienteRepo.excluir(cli.id)
        self._carregar()
