"""Service order page (form + print)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

import tkinter as tk
import customtkinter as ctk

from src.mecanica.database.repositories import ClienteRepo, ServicoRepo
from src.mecanica.relatorios.ordem_html import abrir_impressao
from src.mecanica.ui.masks import aplicar_mascara_ano
from src.mecanica.theme import (
    COR_CAMPO_BORDA, COR_CARD, COR_FUNDO, COR_SIDEBAR, COR_SIDEBAR_HOVER,
    COR_TEXTO_ESCURO, COR_INPUT_BG, COR_LINHA_IMPAR,
    FONTE_BTN, FONTE_CABECALHO, FONTE_LABEL, FONTE_LABEL_NORMAL,
    FONTE_SUBTITULO, FONTE_TITULO,
)

if TYPE_CHECKING:
    from src.mecanica.app import AppOficina

_MAX_SUGESTOES = 6


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
        # OS ↔ client linking state
        self._cliente_id_selecionado: int | None = None
        self._os_id_salvo: int | None = None
        self._popup: tk.Toplevel | None = None
        self._lbl_vinculo: ctk.CTkLabel | None = None

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

        # Header card
        card_cab = ctk.CTkFrame(main, fg_color=COR_CARD, corner_radius=14)
        card_cab.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        card_cab.grid_columnconfigure((0, 1, 2, 3), weight=1)

        def lbl(parent, texto, row, col, colspan=1):
            ctk.CTkLabel(parent, text=texto, font=FONTE_LABEL,
                         text_color="#52A476").grid(
                row=row * 2, column=col, columnspan=colspan,
                sticky="w", padx=14, pady=(12, 1))

        def entry_cab(parent, row, col, colspan=1):
            e = ctk.CTkEntry(parent, font=FONTE_LABEL_NORMAL, height=38,
                             corner_radius=8, fg_color=COR_INPUT_BG,
                             border_width=2, border_color=COR_CAMPO_BORDA)
            e.grid(row=row * 2 + 1, column=col, columnspan=colspan,
                   sticky="ew", padx=14, pady=(0, 10))
            return e

        lbl(card_cab, "🚗  Veículo",  0, 0, 2);  self.ord_veiculo = entry_cab(card_cab, 0, 0, 2)
        lbl(card_cab, "📅  Ano",       0, 2);     self.ord_ano     = entry_cab(card_cab, 0, 2)
        lbl(card_cab, "🔢  Placa",     0, 3);     self.ord_placa   = entry_cab(card_cab, 0, 3)
        lbl(card_cab, "📆  Data",      1, 0);     self.ord_data    = entry_cab(card_cab, 1, 0)
        lbl(card_cab, "👤  Cliente",   1, 1, 2);  self.ord_cliente = entry_cab(card_cab, 1, 1, 2)
        lbl(card_cab, "📱  Fone",      1, 3);     self.ord_fone    = entry_cab(card_cab, 1, 3)

        _ano_var = ctk.StringVar()
        self.ord_ano.configure(textvariable=_ano_var)
        _ano_var.trace_add("write", lambda *a: aplicar_mascara_ano(_ano_var, self.ord_ano))

        self.ord_data.insert(0, datetime.now().strftime("%d/%m/%Y"))

        # Vinculo status label — row 4, spans all columns
        self._lbl_vinculo = ctk.CTkLabel(
            card_cab, text="", font=("Arial Bold", 13), text_color=COR_SIDEBAR,
        )
        self._lbl_vinculo.grid(row=4, column=0, columnspan=4, sticky="w", padx=14, pady=(0, 8))

        # Autocomplete bindings on the Cliente field
        self.ord_cliente.bind("<KeyRelease>", self._on_nome_key)
        self.ord_cliente.bind("<FocusOut>",
                              lambda e: self.app.after(200, self._fechar_popup))

        # Items card
        card_itens = ctk.CTkFrame(main, fg_color=COR_CARD, corner_radius=12,
                                   border_width=1, border_color="#D1FAE5")
        card_itens.grid(row=2, column=0, sticky="nsew", pady=(0, 14))
        card_itens.grid_columnconfigure(1, weight=1)

        COR_SEP = "#D1D5DB"

        hdr_frame = ctk.CTkFrame(card_itens, fg_color=COR_SIDEBAR, corner_radius=8)
        hdr_frame.grid(row=0, column=0, columnspan=4, sticky="ew", padx=10, pady=(10, 0))
        hdr_frame.grid_columnconfigure(2, weight=1)
        headers = [("Qtd", 60, 0), ("Descrição / Serviço", 0, 2),
                   ("P. Unitário", 110, 4), ("TOTAL", 100, 6)]
        for txt, w, col in headers:
            ctk.CTkLabel(hdr_frame, text=txt, font=FONTE_CABECALHO,
                         text_color="#FFFFFF", width=w if w else 0).grid(
                row=0, column=col, sticky="ew" if col == 2 else "",
                padx=8, pady=7)

        NUM_LINHAS = 20
        self.ord_itens = []

        scroll_itens = ctk.CTkScrollableFrame(card_itens, height=480, fg_color="transparent")
        scroll_itens.grid(row=1, column=0, columnspan=4, sticky="ew", padx=10, pady=0)
        scroll_itens.grid_columnconfigure(2, weight=1)

        for i in range(NUM_LINHAS):
            row_conteudo  = i * 2
            row_separador = i * 2 + 1

            bg = COR_CARD if i % 2 == 0 else COR_LINHA_IMPAR
            row_f = ctk.CTkFrame(scroll_itens, fg_color=bg, corner_radius=0, height=42)
            row_f.grid(row=row_conteudo, column=0, columnspan=4, sticky="ew", pady=0)
            row_f.grid_columnconfigure(2, weight=1)
            row_f.grid_propagate(False)

            def vsep(col, parent=row_f):
                tk.Frame(parent, bg=COR_SEP, width=2).grid(row=0, column=col, sticky="ns", pady=0)

            e_qtd  = ctk.CTkEntry(row_f, width=60,  height=34, font=FONTE_LABEL_NORMAL,
                                   fg_color=COR_INPUT_BG, border_width=2,
                                   border_color=COR_CAMPO_BORDA, corner_radius=4, justify="center")
            vsep(1)
            e_disc = ctk.CTkEntry(row_f, height=34, font=FONTE_LABEL_NORMAL,
                                   fg_color=COR_INPUT_BG, border_width=2,
                                   border_color=COR_CAMPO_BORDA, corner_radius=4)
            vsep(3)
            e_unit = ctk.CTkEntry(row_f, width=110, height=34, font=FONTE_LABEL_NORMAL,
                                   fg_color=COR_INPUT_BG, border_width=2,
                                   border_color=COR_CAMPO_BORDA, corner_radius=4, justify="center")
            vsep(5)
            e_tot  = ctk.CTkEntry(row_f, width=100, height=34, font=FONTE_LABEL_NORMAL,
                                   fg_color=COR_INPUT_BG, border_width=2,
                                   border_color=COR_CAMPO_BORDA, corner_radius=4, justify="center")

            e_qtd.grid( row=0, column=0, padx=(6, 3), pady=3)
            e_disc.grid(row=0, column=2, sticky="ew", padx=6, pady=3)
            e_unit.grid(row=0, column=4, padx=6, pady=3)
            e_tot.grid( row=0, column=6, padx=(3, 6), pady=3)

            tk.Frame(scroll_itens, bg=COR_SEP, height=2).grid(
                row=row_separador, column=0, columnspan=4, sticky="ew")

            def _calc(event, eq=e_qtd, eu=e_unit, et=e_tot):
                try:
                    q = float(eq.get().replace(",", ".") or 0)
                    u = float(eu.get().replace(",", ".") or 0)
                    et.delete(0, "end")
                    et.insert(0, f"{q * u:.2f}")
                except Exception:
                    pass

            e_unit.bind("<KeyRelease>", _calc)
            e_unit.bind("<FocusOut>",   _calc)
            e_qtd.bind("<KeyRelease>",  _calc)
            e_qtd.bind("<FocusOut>",    _calc)

            self.ord_itens.append((e_qtd, e_disc, e_unit, e_tot))

        # Enter key navigation: qtd → disc → unit → qtd da próxima linha
        for i, (e_qtd, e_disc, e_unit, e_tot) in enumerate(self.ord_itens):
            e_qtd.bind("<Return>", lambda e, t=e_disc: t.focus_set())
            e_disc.bind("<Return>", lambda e, t=e_unit: t.focus_set())
            if i + 1 < len(self.ord_itens):
                nxt = self.ord_itens[i + 1][0]
                e_unit.bind("<Return>", lambda e, t=nxt: t.focus_set())

        rod = ctk.CTkFrame(card_itens, fg_color=COR_FUNDO, corner_radius=8)
        rod.grid(row=2, column=0, columnspan=4, sticky="e", padx=10, pady=(4, 10))
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

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def _capturar_estado(self) -> dict:
        itens = [
            (e_qtd.get(), e_disc.get(), e_unit.get(), e_tot.get())
            for e_qtd, e_disc, e_unit, e_tot in self.ord_itens
        ]
        return {
            "veiculo":   self.ord_veiculo.get(),
            "ano":       self.ord_ano.get(),
            "placa":     self.ord_placa.get(),
            "data":      self.ord_data.get(),
            "cliente":   self.ord_cliente.get(),
            "fone":      self.ord_fone.get(),
            "total":     self.ord_total_lbl.get() if self.ord_total_lbl else "",
            "itens":     itens,
            "cliente_id": self._cliente_id_selecionado,
            "os_id":     self._os_id_salvo,
            "vinculo":   self._lbl_vinculo.cget("text") if self._lbl_vinculo else "",
        }

    def _restaurar_estado(self, estado: dict) -> None:
        self.ord_veiculo.insert(0, estado.get("veiculo", ""))
        self.ord_ano.insert(0, estado.get("ano", ""))
        self.ord_placa.insert(0, estado.get("placa", ""))
        self.ord_data.delete(0, "end")
        self.ord_data.insert(0, estado.get("data", datetime.now().strftime("%d/%m/%Y")))
        self.ord_cliente.insert(0, estado.get("cliente", ""))
        self.ord_fone.insert(0, estado.get("fone", ""))

        for i, (qtd, disc, unit, tot) in enumerate(estado.get("itens", [])):
            if i >= len(self.ord_itens):
                break
            e_qtd, e_disc, e_unit, e_tot = self.ord_itens[i]
            e_qtd.insert(0, qtd)
            e_disc.insert(0, disc)
            e_unit.insert(0, unit)
            e_tot.insert(0, tot)

        total = estado.get("total", "")
        if total:
            self.ord_total_lbl.configure(state="normal")
            self.ord_total_lbl.delete(0, "end")
            self.ord_total_lbl.insert(0, total)
            self.ord_total_lbl.configure(state="disabled")

        self._cliente_id_selecionado = estado.get("cliente_id")
        self._os_id_salvo = estado.get("os_id")
        vinculo = estado.get("vinculo", "")
        if vinculo and self._lbl_vinculo:
            self._lbl_vinculo.configure(text=vinculo)

    # ------------------------------------------------------------------
    # Autocomplete
    # ------------------------------------------------------------------

    def _on_nome_key(self, event) -> None:
        if event.keysym in ("Return", "Tab", "Escape", "Up", "Down"):
            self._fechar_popup()
            return

        # Any typing clears a previously selected client
        if self._cliente_id_selecionado is not None:
            self._cliente_id_selecionado = None
            self._os_id_salvo = None
            if self._lbl_vinculo:
                self._lbl_vinculo.configure(text="")

        termo = self.ord_cliente.get().strip()
        if not termo:
            self._fechar_popup()
            return

        resultados = ClienteRepo.listar(termo)[:_MAX_SUGESTOES]
        if resultados:
            self._mostrar_popup(resultados)
        else:
            self._fechar_popup()

    def _mostrar_popup(self, resultados) -> None:
        entry = self.ord_cliente
        try:
            x = entry.winfo_rootx()
            y = entry.winfo_rooty() + entry.winfo_height()
            w = entry.winfo_width()
        except Exception:
            return

        if self._popup is None or not self._popup.winfo_exists():
            self._popup = tk.Toplevel(self.app)
            self._popup.wm_overrideredirect(True)

        for widget in self._popup.winfo_children():
            widget.destroy()

        frame = ctk.CTkFrame(self._popup, fg_color="#FFFFFF", corner_radius=8,
                             border_width=1, border_color=COR_SIDEBAR)
        frame.pack(fill="both", expand=True, padx=1, pady=1)

        for cli in resultados:
            linha = cli.nome
            if cli.placa:
                linha += f"  ·  {cli.placa}"
            ctk.CTkButton(
                frame,
                text=linha,
                font=("Arial Bold", 14),
                anchor="w",
                fg_color="transparent",
                text_color="#0F172A",
                hover_color="#D1FAE5",
                height=36,
                corner_radius=4,
                command=lambda c=cli: self._selecionar_cliente(c),
            ).pack(fill="x", padx=4, pady=(2, 0))

        altura = len(resultados) * 40 + 8
        self._popup.geometry(f"{w}x{altura}+{x}+{y}")
        self._popup.lift()
        self._popup.deiconify()

    def _selecionar_cliente(self, cli) -> None:
        self._cliente_id_selecionado = cli.id

        self.ord_cliente.delete(0, "end")
        self.ord_cliente.insert(0, cli.nome)

        if cli.telefone:
            self.ord_fone.delete(0, "end")
            self.ord_fone.insert(0, cli.telefone)
        if cli.placa:
            self.ord_placa.delete(0, "end")
            self.ord_placa.insert(0, cli.placa)

        if self._lbl_vinculo:
            self._lbl_vinculo.configure(
                text=f"✅  Cliente cadastrado vinculado — será salvo no histórico ao imprimir"
            )
        self._fechar_popup()

    def _fechar_popup(self) -> None:
        if self._popup and self._popup.winfo_exists():
            self._popup.withdraw()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

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
        # Reset OS ↔ client state
        self._cliente_id_selecionado = None
        self._os_id_salvo = None
        self._fechar_popup()
        if self._lbl_vinculo:
            self._lbl_vinculo.configure(text="")
        self.app.ordem_rascunho = None

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

        # Save / update in client history when a known client is linked
        if self._cliente_id_selecionado is None:
            return

        try:
            total = float(dados["total"].replace(",", ".") or 0)
        except ValueError:
            total = 0.0

        ordem_json = json.dumps(dados, ensure_ascii=False)

        if self._os_id_salvo is None:
            self._os_id_salvo = ServicoRepo.inserir(
                cliente_id=self._cliente_id_selecionado,
                data=dados["data"],
                placa=dados["placa"],
                servico="Ordem de Serviço",
                saldo=total,
                pago=0.0,
                comentario="",
                veiculo=dados["veiculo"],
                ano=dados["ano"],
                ordem_json=ordem_json,
            )
        else:
            ServicoRepo.atualizar(
                servico_id=self._os_id_salvo,
                placa=dados["placa"],
                servico="Ordem de Serviço",
                saldo=total,
                pago=0.0,
                comentario="",
                data=dados["data"],
                veiculo=dados["veiculo"],
                ano=dados["ano"],
                ordem_json=ordem_json,
            )

        if self._lbl_vinculo:
            self._lbl_vinculo.configure(
                text=f"✅  Salvo no histórico de {dados['cliente']}"
            )
