"""Main application window — orchestration and sidebar only."""

from __future__ import annotations

import threading

import customtkinter as ctk

from src.mecanica.config import BACKUP_INTERVALO_MIN
from src.mecanica.database.schema import iniciar_db
from src.mecanica.integracoes.drive_backup import DRIVE_DISPONIVEL, DriveBackup
from src.mecanica.theme import (
    COR_BRANCO, COR_FUNDO, COR_SIDEBAR,
    COR_SIDEBAR_HOVER, COR_TEXTO_ESCURO,
    FONTE_LOGO, FONTE_SIDEBAR, FONTE_SMALL,
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
        self.after(100, lambda: self.wm_attributes("-zoomed", True))
        self.configure(fg_color=COR_FUNDO)

        iniciar_db()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.cliente_selecionado = None
        self._pagina_atual = None
        self.ordem_rascunho: dict | None = None

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

    def _salvar_rascunho_ordem(self) -> None:
        if isinstance(self._pagina_atual, PaginaOrdem):
            self.ordem_rascunho = self._pagina_atual._capturar_estado()

    def navegar_clientes(self) -> None:
        self._salvar_rascunho_ordem()
        self._limpar()
        pagina = PaginaClientes(self)
        pagina.montar(self.area)
        self._pagina_atual = pagina

    def navegar_detalhes(self) -> None:
        self._salvar_rascunho_ordem()
        self._limpar()
        pagina = PaginaDetalhes(self)
        pagina.montar(self.area)
        self._pagina_atual = pagina

    def navegar_ordem(self) -> None:
        self._limpar()
        pagina = PaginaOrdem(self)
        pagina.montar(self.area)
        if self.ordem_rascunho:
            pagina._restaurar_estado(self.ordem_rascunho)
        self._pagina_atual = pagina

    # ------------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------------

    def _criar_sidebar(self) -> None:
        sb = ctk.CTkFrame(self, fg_color=COR_SIDEBAR, corner_radius=0, width=200)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(sb, fg_color="transparent")
        logo_frame.pack(pady=(32, 0), padx=20, fill="x")
        ctk.CTkLabel(
            logo_frame,
            text="Mecânica SP",
            font=FONTE_LOGO,
            text_color=COR_BRANCO,
            justify="center",
        ).pack(anchor="center")

        # Nav buttons
        def btn_nav(texto, comando, ativo=False):
            b = ctk.CTkButton(
                sb, text=texto, font=FONTE_SIDEBAR, anchor="w",
                fg_color=COR_BRANCO if ativo else "transparent",
                text_color=COR_SIDEBAR if ativo else COR_BRANCO,
                hover_color=COR_SIDEBAR_HOVER,
                height=46, corner_radius=8,
                command=comando,
            )
            b.pack(fill="x", padx=14, pady=(14, 0))
            return b

        btn_nav("  👥  Clientes", self.navegar_clientes, ativo=False)
        btn_nav("  📋  Ordem",    self.navegar_ordem,    ativo=False)

        # Drive status card
        drive_frame = ctk.CTkFrame(sb, fg_color="#207244", corner_radius=10)
        drive_frame.pack(fill="x", padx=14, pady=(24, 6))

        ctk.CTkLabel(drive_frame, text="Google Drive", font=FONTE_SIDEBAR,
                     text_color=COR_BRANCO).pack(pady=(10, 2))

        self._lbl_drive_status = ctk.CTkLabel(
            drive_frame,
            text="⏳ Aguardando…" if DRIVE_DISPONIVEL else "❌ Libs não instaladas",
            font=FONTE_SMALL,
            text_color="#A8D5B5",
            wraplength=160,
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

        ctk.CTkLabel(sb, text="v3.0 · Oficina Pro", font=("Arial Bold", 10),
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
