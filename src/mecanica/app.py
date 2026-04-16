"""Main application window — orchestration and sidebar only."""

from __future__ import annotations

import threading
from tkinter import ttk

import customtkinter as ctk

from src.mecanica.config import BACKUP_INTERVALO_MIN
from src.mecanica.database.schema import iniciar_db
from src.mecanica.integracoes.drive_backup import DRIVE_DISPONIVEL, DriveBackup
from src.mecanica.theme import (
    COR_BRANCO, COR_CARD, COR_FUNDO, COR_SIDEBAR, COR_SIDEBAR_ATIVO,
    COR_SIDEBAR_HOVER, COR_TEXTO_ESCURO,
    FONTE_CABECALHO, FONTE_LOGO, FONTE_SIDEBAR, FONTE_SMALL, FONTE_TABELA,
)
from src.mecanica.ui.pages.clientes import PaginaClientes
from src.mecanica.ui.pages.detalhes import PaginaDetalhes
from src.mecanica.ui.pages.ordem import PaginaOrdem


class AppOficina(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Oficina Pro — Gestão")
        self.geometry("1200x750")
        self.minsize(1000, 650)
        self.configure(fg_color=COR_FUNDO)

        iniciar_db()
        self._configurar_estilo_tabela()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.cliente_selecionado = None
        self._pagina_atual = None

        self.backup = DriveBackup(on_status_change=self._atualizar_status_drive)
        self._criar_sidebar()

        self.area = ctk.CTkFrame(self, fg_color=COR_FUNDO, corner_radius=0)
        self.area.grid(row=0, column=1, sticky="nsew")
        self.area.grid_rowconfigure(0, weight=1)
        self.area.grid_columnconfigure(0, weight=1)

        self.navegar_clientes()

        self.backup.limpar_temporarios()
        threading.Thread(target=self._iniciar_drive, daemon=True).start()
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _limpar(self) -> None:
        for w in self.area.winfo_children():
            w.destroy()

    def navegar_clientes(self) -> None:
        self._limpar()
        pagina = PaginaClientes(self)
        pagina.montar(self.area)
        self._pagina_atual = pagina

    def navegar_detalhes(self) -> None:
        self._limpar()
        pagina = PaginaDetalhes(self)
        pagina.montar(self.area)
        self._pagina_atual = pagina

    def navegar_ordem(self) -> None:
        self._limpar()
        pagina = PaginaOrdem(self)
        pagina.montar(self.area)
        self._pagina_atual = pagina

    # ------------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------------

    def _criar_sidebar(self) -> None:
        sb = ctk.CTkFrame(self, fg_color=COR_SIDEBAR, corner_radius=0, width=220)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)

        logo_frame = ctk.CTkFrame(sb, fg_color="#1A6B40", corner_radius=12, width=160, height=64)
        logo_frame.pack(pady=(30, 30), padx=30)
        logo_frame.pack_propagate(False)
        ctk.CTkLabel(logo_frame, text="🔧 OFICINA\nPRO", font=FONTE_LOGO,
                     text_color=COR_BRANCO, justify="center").place(relx=0.5, rely=0.5, anchor="center")

        def btn_nav(texto, comando):
            b = ctk.CTkButton(sb, text=texto, font=FONTE_SIDEBAR, anchor="w",
                              fg_color="transparent", hover_color=COR_SIDEBAR_HOVER,
                              text_color=COR_BRANCO, height=48, corner_radius=10,
                              command=comando)
            b.pack(fill="x", padx=15, pady=3)
            return b

        btn_nav("  👥  Clientes", self.navegar_clientes)
        btn_nav("  📋  Ordem",    self.navegar_ordem)

        drive_frame = ctk.CTkFrame(sb, fg_color="#1A6B40", corner_radius=10)
        drive_frame.pack(fill="x", padx=15, pady=(20, 6))

        ctk.CTkLabel(drive_frame, text="Google Drive", font=FONTE_SIDEBAR,
                     text_color=COR_BRANCO).pack(pady=(10, 2))

        self._lbl_drive_status = ctk.CTkLabel(
            drive_frame,
            text="⏳ Aguardando…" if DRIVE_DISPONIVEL else "❌ Libs não instaladas",
            font=FONTE_SMALL,
            text_color="#A8D5B5",
            wraplength=170,
        )
        self._lbl_drive_status.pack(pady=(0, 6), padx=8)

        ctk.CTkButton(
            drive_frame,
            text="⬆️ Salvar Agora",
            font=FONTE_SMALL,
            fg_color=COR_SIDEBAR,
            hover_color=COR_SIDEBAR_HOVER,
            height=30,
            corner_radius=8,
            command=self._backup_manual,
        ).pack(pady=(0, 10), padx=10, fill="x")

        ctk.CTkLabel(sb, text="v3.0 · Oficina Pro", font=("Segoe UI", 11),
                     text_color="#A8D5B5").pack(side="bottom", pady=18)

    # ------------------------------------------------------------------
    # Drive
    # ------------------------------------------------------------------

    def _iniciar_drive(self) -> None:
        if self.backup.autenticar():
            self.backup.fazer_backup()
            self.backup.iniciar_loop(BACKUP_INTERVALO_MIN)

    def _atualizar_status_drive(self, msg: str, cor: str) -> None:
        try:
            self.after(0, lambda: self._lbl_drive_status.configure(text=msg, text_color=cor))
        except Exception:
            pass

    def _backup_manual(self) -> None:
        threading.Thread(target=self.backup.fazer_backup, daemon=True).start()

    def _ao_fechar(self) -> None:
        self.backup.parar_loop()
        self.backup.limpar_temporarios()
        self.destroy()

    # ------------------------------------------------------------------
    # Table style (shared across pages)
    # ------------------------------------------------------------------

    def _configurar_estilo_tabela(self) -> None:
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background=COR_CARD, foreground=COR_TEXTO_ESCURO,
                        rowheight=46, fieldbackground=COR_CARD,
                        borderwidth=0, relief="flat", font=FONTE_TABELA,
                        padding=(8, 0))
        style.configure("Treeview.Heading",
                        background=COR_SIDEBAR, foreground=COR_BRANCO,
                        font=FONTE_CABECALHO, borderwidth=1, relief="raised",
                        padding=(12, 8))
        style.map("Treeview.Heading", background=[("active", COR_SIDEBAR_HOVER)])
        style.map("Treeview",
                  background=[("selected", "#C8E6C9")],
                  foreground=[("selected", COR_TEXTO_ESCURO)])
