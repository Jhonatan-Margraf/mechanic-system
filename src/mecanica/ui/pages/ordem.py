"""Service order page (form + print)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import tkinter as tk
import customtkinter as ctk

from src.mecanica.relatorios.ordem_html import abrir_impressao
from src.mecanica.theme import (
    COR_CARD, COR_FUNDO, COR_SIDEBAR, COR_SIDEBAR_HOVER,
    COR_TEXTO_ESCURO, COR_TEXTO_MEDIO,
    FONTE_BTN, FONTE_CABECALHO, FONTE_LABEL, FONTE_LABEL_NORMAL,
    FONTE_SUBTITULO, FONTE_TITULO,
)

if TYPE_CHECKING:
    from src.mecanica.app import AppOficina


class PaginaOrdem:
    def __init__(self, app: "AppOficina"):
        self.app = app
        self.ord_itens: list[tuple] = []
        self.ord_veiculo = None
        self.ord_ano     = None
        self.ord_placa   = None
        self.ord_data    = None
        self.ord_cliente = None
        self.ord_fone    = None
        self.ord_total_lbl = None

    def montar(self, container: ctk.CTkFrame) -> None:
        main = ctk.CTkFrame(container, fg_color=COR_FUNDO, corner_radius=0)
        main.grid(row=0, column=0, sticky="nsew", padx=28, pady=24)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(3, weight=1)

        linha_titulo = ctk.CTkFrame(main, fg_color="transparent")
        linha_titulo.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        ctk.CTkLabel(linha_titulo, text="📋  Ordem de Serviço", font=FONTE_TITULO,
                     text_color=COR_TEXTO_ESCURO).pack(side="left")
        ctk.CTkButton(linha_titulo, text="🖨️  Imprimir", font=FONTE_BTN,
                      fg_color=COR_SIDEBAR, hover_color=COR_SIDEBAR_HOVER,
                      height=44, corner_radius=10,
                      command=self._imprimir).pack(side="right")
        ctk.CTkButton(linha_titulo, text="🗑️  Limpar", font=FONTE_BTN,
                      fg_color="#AAAAAA", hover_color="#888888",
                      height=44, corner_radius=10,
                      command=self._limpar).pack(side="right", padx=(0, 10))

        card_cab = ctk.CTkFrame(main, fg_color=COR_CARD, corner_radius=14)
        card_cab.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        card_cab.grid_columnconfigure((0, 1, 2, 3), weight=1)

        def lbl(parent, texto, row, col, colspan=1):
            ctk.CTkLabel(parent, text=texto, font=FONTE_LABEL,
                         text_color=COR_TEXTO_MEDIO).grid(
                row=row * 2, column=col, columnspan=colspan,
                sticky="w", padx=14, pady=(12, 1))

        def entry_cab(parent, row, col, colspan=1):
            e = ctk.CTkEntry(parent, font=FONTE_LABEL_NORMAL, height=38, corner_radius=8)
            e.grid(row=row * 2 + 1, column=col, columnspan=colspan,
                   sticky="ew", padx=14, pady=(0, 10))
            return e

        lbl(card_cab, "🚗  Veículo",  0, 0, 2);  self.ord_veiculo = entry_cab(card_cab, 0, 0, 2)
        lbl(card_cab, "📅  Ano",       0, 2);     self.ord_ano     = entry_cab(card_cab, 0, 2)
        lbl(card_cab, "🔢  Placa",     0, 3);     self.ord_placa   = entry_cab(card_cab, 0, 3)
        lbl(card_cab, "📆  Data",      1, 0);     self.ord_data    = entry_cab(card_cab, 1, 0)
        lbl(card_cab, "👤  Cliente",   1, 1, 2);  self.ord_cliente = entry_cab(card_cab, 1, 1, 2)
        lbl(card_cab, "📱  Fone",      1, 3);     self.ord_fone    = entry_cab(card_cab, 1, 3)

        self.ord_data.insert(0, datetime.now().strftime("%d/%m/%Y"))

        card_itens = ctk.CTkFrame(main, fg_color=COR_CARD, corner_radius=14)
        card_itens.grid(row=2, column=0, sticky="nsew", pady=(0, 14))
        card_itens.grid_columnconfigure(1, weight=1)

        COR_SEP = "#888888"
        card_itens.configure(border_width=2, border_color=COR_SEP)

        hdr_frame = ctk.CTkFrame(card_itens, fg_color=COR_SIDEBAR, corner_radius=8)
        hdr_frame.grid(row=0, column=0, columnspan=4, sticky="ew", padx=10, pady=(10, 0))
        hdr_frame.grid_columnconfigure(2, weight=1)
        headers = [("Qtd", 60, 0), ("Discriminação / Serviço", 0, 2),
                   ("P. Unitário", 110, 4), ("TOTAL", 100, 6)]
        for txt, w, col in headers:
            ctk.CTkLabel(hdr_frame, text=txt, font=FONTE_CABECALHO,
                         text_color="#FFFFFF", width=w if w else 0).grid(
                row=0, column=col, sticky="ew" if col == 2 else "",
                padx=8, pady=7)

        NUM_LINHAS = 15
        self.ord_itens = []

        for i in range(NUM_LINHAS):
            row_conteudo  = i * 2 + 1
            row_separador = i * 2 + 2

            bg = COR_CARD if i % 2 == 0 else "#EFF3F1"
            row_f = ctk.CTkFrame(card_itens, fg_color=bg, corner_radius=0, height=36)
            row_f.grid(row=row_conteudo, column=0, columnspan=4, sticky="ew", padx=10, pady=0)
            row_f.grid_columnconfigure(2, weight=1)
            row_f.grid_propagate(False)

            def vsep(col, parent=row_f):
                tk.Frame(parent, bg=COR_SEP, width=2).grid(row=0, column=col, sticky="ns", pady=0)

            e_qtd  = ctk.CTkEntry(row_f, width=60,  height=30, font=FONTE_LABEL_NORMAL,
                                   fg_color="transparent", border_width=0, corner_radius=0, justify="center")
            vsep(1)
            e_disc = ctk.CTkEntry(row_f, height=30, font=FONTE_LABEL_NORMAL,
                                   fg_color="transparent", border_width=0, corner_radius=0)
            vsep(3)
            e_unit = ctk.CTkEntry(row_f, width=110, height=30, font=FONTE_LABEL_NORMAL,
                                   fg_color="transparent", border_width=0, corner_radius=0, justify="center")
            vsep(5)
            e_tot  = ctk.CTkEntry(row_f, width=100, height=30, font=FONTE_LABEL_NORMAL,
                                   fg_color="transparent", border_width=0, corner_radius=0, justify="center")

            e_qtd.grid( row=0, column=0, padx=(6, 3), pady=3)
            e_disc.grid(row=0, column=2, sticky="ew", padx=6, pady=3)
            e_unit.grid(row=0, column=4, padx=6, pady=3)
            e_tot.grid( row=0, column=6, padx=(3, 6), pady=3)

            tk.Frame(card_itens, bg=COR_SEP, height=2).grid(
                row=row_separador, column=0, columnspan=4, sticky="ew", padx=10)

            def _calc(event, eq=e_qtd, eu=e_unit, et=e_tot):
                try:
                    q = float(eq.get().replace(",", ".") or 0)
                    u = float(eu.get().replace(",", ".") or 0)
                    et.delete(0, "end")
                    et.insert(0, f"{q * u:.2f}")
                except Exception:
                    pass

            e_unit.bind("<FocusOut>", _calc)
            e_qtd.bind("<FocusOut>",  _calc)

            self.ord_itens.append((e_qtd, e_disc, e_unit, e_tot))

        rod = ctk.CTkFrame(card_itens, fg_color=COR_FUNDO, corner_radius=8)
        rod.grid(row=NUM_LINHAS * 2 + 1, column=0, columnspan=4, sticky="e", padx=10, pady=(4, 10))
        ctk.CTkLabel(rod, text="TOTAL  R$", font=FONTE_LABEL,
                     text_color=COR_TEXTO_ESCURO).pack(side="left", padx=(10, 6))
        self.ord_total_lbl = ctk.CTkEntry(rod, width=120, height=36, font=FONTE_SUBTITULO,
                                           state="disabled", fg_color=COR_CARD,
                                           text_color=COR_TEXTO_ESCURO, border_color=COR_SIDEBAR)
        self.ord_total_lbl.pack(side="left", padx=(0, 10))
        ctk.CTkButton(rod, text="⟳ Calcular Total", font=FONTE_LABEL_NORMAL,
                      fg_color=COR_SIDEBAR, hover_color=COR_SIDEBAR_HOVER,
                      height=36, corner_radius=8,
                      command=self._calcular_total).pack(side="left", padx=(14, 10))

    def _calcular_total(self) -> float:
        total = 0.0
        for e_qtd, _, e_unit, e_tot in self.ord_itens:
            try:
                total += float(e_tot.get().replace(",", ".") or 0)
            except Exception:
                pass
        self.ord_total_lbl.configure(state="normal")
        self.ord_total_lbl.delete(0, "end")
        self.ord_total_lbl.insert(0, f"{total:.2f}")
        self.ord_total_lbl.configure(state="disabled")
        return total

    def _limpar(self) -> None:
        for campo in [self.ord_veiculo, self.ord_ano, self.ord_placa,
                      self.ord_cliente, self.ord_fone]:
            campo.delete(0, "end")
        self.ord_data.delete(0, "end")
        self.ord_data.insert(0, datetime.now().strftime("%d/%m/%Y"))
        for e_qtd, e_disc, e_unit, e_tot in self.ord_itens:
            for e in (e_qtd, e_disc, e_unit, e_tot):
                e.delete(0, "end")
        self.ord_total_lbl.configure(state="normal")
        self.ord_total_lbl.delete(0, "end")
        self.ord_total_lbl.configure(state="disabled")

    def _imprimir(self) -> None:
        self._calcular_total()
        linhas = [
            (e_qtd.get(), e_disc.get(), e_unit.get(), e_tot.get())
            for e_qtd, e_disc, e_unit, e_tot in self.ord_itens
        ]
        dados = {
            "veiculo": self.ord_veiculo.get(),
            "ano":     self.ord_ano.get(),
            "placa":   self.ord_placa.get(),
            "data":    self.ord_data.get(),
            "cliente": self.ord_cliente.get(),
            "fone":    self.ord_fone.get(),
            "total":   self.ord_total_lbl.get() or "0.00",
            "linhas":  linhas,
        }
        abrir_impressao(dados)
