"""Reusable UI widgets."""

import customtkinter as ctk

from src.mecanica.theme import COR_BRANCO, FONTE_CARD, FONTE_CARD_LABEL


class CardEstatistica(ctk.CTkFrame):
    """Small stat card with an icon on the left and a value + label on the right."""

    def __init__(self, master, icone: str, titulo: str, valor, cor_fundo: str, **kwargs):
        super().__init__(master, fg_color=cor_fundo, corner_radius=14, **kwargs)
        self.configure(width=190, height=100)
        self.grid_propagate(False)
        self.pack_propagate(False)

        frame_icone = ctk.CTkFrame(self, fg_color="#2A7A4A", corner_radius=10, width=52, height=52)
        frame_icone.place(relx=0.08, rely=0.5, anchor="w")
        ctk.CTkLabel(frame_icone, text=icone, font=("Segoe UI", 24),
                     text_color=COR_BRANCO).place(relx=0.5, rely=0.5, anchor="center")

        self.lbl_valor = ctk.CTkLabel(self, text=str(valor), font=FONTE_CARD, text_color=COR_BRANCO)
        self.lbl_valor.place(relx=0.62, rely=0.32, anchor="center")

        ctk.CTkLabel(self, text=titulo, font=FONTE_CARD_LABEL,
                     text_color="#D5ECD8").place(relx=0.62, rely=0.70, anchor="center")

    def atualizar(self, valor) -> None:
        self.lbl_valor.configure(text=str(valor))
