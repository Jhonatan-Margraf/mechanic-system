"""Reusable UI widgets."""

import customtkinter as ctk

from src.mecanica.theme import COR_BRANCO, FONTE_CARD, FONTE_CARD_LABEL


class CardEstatistica(ctk.CTkFrame):
    """Stat card matching the reference design: icon left, value+label right."""

    def __init__(self, master, icone: str, titulo: str, valor, cor_fundo: str, **kwargs):
        super().__init__(master, fg_color=cor_fundo, corner_radius=8, **kwargs)
        self.configure(width=200, height=60)
        self.grid_propagate(False)
        self.pack_propagate(False)

        # Icon column
        ctk.CTkLabel(
            self, text=icone, font=("Arial Black", 26), text_color=COR_BRANCO,
        ).grid(row=0, column=0, rowspan=2, padx=(12, 5), pady=10)

        # Text column
        ctk.CTkLabel(
            self, text=titulo, text_color=COR_BRANCO, font=FONTE_CARD_LABEL,
        ).grid(row=0, column=1, sticky="sw")

        self.lbl_valor = ctk.CTkLabel(
            self, text=str(valor), font=FONTE_CARD, text_color=COR_BRANCO, justify="left",
        )
        self.lbl_valor.grid(row=1, column=1, sticky="nw", pady=(0, 10))

    def atualizar(self, valor) -> None:
        self.lbl_valor.configure(text=str(valor))
