"""Modal windows: new client and new/edit service."""

from __future__ import annotations

from datetime import datetime
from tkinter import messagebox
from typing import Callable, Optional

import customtkinter as ctk

from src.mecanica.database.repositories import ClienteRepo, ServicoRepo
from src.mecanica.domain.formatters import normalizar_placa
from src.mecanica.theme import (
    COR_BRANCO, COR_CAMPO_BORDA, COR_CARD, COR_FUNDO, COR_INPUT_BG, COR_LABEL_FORM,
    COR_SIDEBAR, COR_SIDEBAR_HOVER,
    FONTE_BTN, FONTE_LABEL, FONTE_LABEL_NORMAL, FONTE_SUBTITULO,
)
from src.mecanica.ui.masks import aplicar_mascara_cpf, aplicar_mascara_telefone, aplicar_mascara_ano


def _posicionar_modal(modal: ctk.CTkToplevel, master) -> None:
    modal.update_idletasks()
    w = modal.winfo_width()
    h = modal.winfo_height()
    mx = master.winfo_rootx() + master.winfo_width() // 2
    x = max(0, mx - w // 2)
    y = max(0, master.winfo_rooty() + 40)
    modal.geometry(f"{w}x{h}+{x}+{y}")


class ModalNovoCliente(ctk.CTkToplevel):
    def __init__(self, master, callback_atualizar: Callable, editar=None):
        super().__init__(master)
        self.withdraw()  # hide while building — prevents blank flash on Windows
        self._editar = editar
        eh_edicao = editar is not None
        self.title("Editar Cliente" if eh_edicao else "Novo Cliente")
        self.geometry("500x720")
        self.resizable(False, False)
        self.transient(master)
        self.configure(fg_color=COR_FUNDO)
        self.callback = callback_atualizar

        cab = ctk.CTkFrame(self, fg_color=COR_SIDEBAR, corner_radius=0, height=70)
        cab.pack(fill="x")
        titulo_cab = "✏️  Editar Cliente" if eh_edicao else "➕  Cadastrar Novo Cliente"
        ctk.CTkLabel(cab, text=titulo_cab, font=FONTE_SUBTITULO,
                     text_color=COR_BRANCO).place(relx=0.5, rely=0.5, anchor="center")

        frame_form = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=14)
        frame_form.pack(fill="both", padx=30, pady=25, expand=True)

        def campo(parent, icone, label):
            ctk.CTkLabel(parent, text=f"{icone}  {label}", font=FONTE_LABEL,
                         text_color=COR_LABEL_FORM).pack(anchor="w", padx=20, pady=(14, 2))
            e = ctk.CTkEntry(parent, font=FONTE_LABEL_NORMAL, height=42,
                             fg_color=COR_INPUT_BG,
                             border_width=2, border_color=COR_CAMPO_BORDA)
            e.pack(fill="x", padx=20)
            return e

        self.nome     = campo(frame_form, "👤", "Nome Completo *")
        self.cpf      = campo(frame_form, "🪪", "CPF")
        self.telefone = campo(frame_form, "📱", "Celular / Telefone")
        self.placa    = campo(frame_form, "🚗", "Placa do Veículo")
        self.endereco = campo(frame_form, "📍", "Endereço")
        self.cidade   = campo(frame_form, "🏙️", "Cidade")

        # Live masks
        cpf_var = ctk.StringVar()
        self.cpf.configure(textvariable=cpf_var)
        cpf_var.trace_add("write", lambda *a: aplicar_mascara_cpf(cpf_var, self.cpf))

        tel_var = ctk.StringVar()
        self.telefone.configure(textvariable=tel_var)
        tel_var.trace_add("write", lambda *a: aplicar_mascara_telefone(tel_var, self.telefone))

        # Pre-fill fields when editing
        if eh_edicao:
            self.nome.insert(0, editar.nome)
            cpf_var.set(editar.cpf)
            tel_var.set(editar.telefone)
            self.placa.insert(0, editar.placa or "")
            self.endereco.insert(0, editar.endereco)
            self.cidade.insert(0, editar.cidade)

        frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        frame_btns.pack(pady=(0, 20))
        ctk.CTkButton(frame_btns, text="Cancelar", font=FONTE_BTN, fg_color="#AAAAAA",
                      hover_color="#888888", command=self.destroy,
                      width=140, height=44, corner_radius=10).pack(side="left", padx=10)
        ctk.CTkButton(frame_btns, text="💾  Salvar", font=FONTE_BTN, fg_color=COR_SIDEBAR,
                      hover_color=COR_SIDEBAR_HOVER, command=self.salvar,
                      width=140, height=44, corner_radius=10).pack(side="left", padx=10)

        # Show only after all widgets are ready — grab_set works reliably on Windows and Linux
        self.deiconify()
        _posicionar_modal(self, master)
        self.lift()
        self.focus_force()
        self.grab_set()

    def salvar(self) -> None:
        if not self.nome.get().strip():
            messagebox.showwarning("Aviso", "O nome do cliente é obrigatório!")
            return
        if self._editar is not None:
            ClienteRepo.atualizar(
                cliente_id=self._editar.id,
                nome=self.nome.get().strip(),
                cpf=self.cpf.get().strip(),
                endereco=self.endereco.get().strip(),
                cidade=self.cidade.get().strip(),
                telefone=self.telefone.get().strip(),
                placa=normalizar_placa(self.placa.get()),
            )
        else:
            ClienteRepo.inserir(
                nome=self.nome.get().strip(),
                cpf=self.cpf.get().strip(),
                endereco=self.endereco.get().strip(),
                cidade=self.cidade.get().strip(),
                telefone=self.telefone.get().strip(),
                placa=normalizar_placa(self.placa.get()),
            )
        self.callback()
        self.destroy()


class ModalServico(ctk.CTkToplevel):
    """Create or edit a service record for a given client."""

    def __init__(
        self,
        master,
        cliente_id: int | str,
        callback_atualizar: Callable,
        editar: Optional[tuple] = None,
    ):
        """
        editar — tuple of row values from the Treeview when editing,
                 or None when creating a new service.
        """
        super().__init__(master)
        self.withdraw()  # hide while building — prevents blank flash on Windows
        eh_edicao = editar is not None
        self.title("Editar Serviço" if eh_edicao else "Novo Serviço")
        self.geometry("520x880")
        self.resizable(False, False)
        self.transient(master)
        self.configure(fg_color=COR_FUNDO)

        titulo_cab = "✏️  Editar Serviço" if eh_edicao else "🔧  Adicionar Serviço"
        cab = ctk.CTkFrame(self, fg_color=COR_SIDEBAR, corner_radius=0, height=70)
        cab.pack(fill="x")
        ctk.CTkLabel(cab, text=titulo_cab, font=FONTE_SUBTITULO,
                     text_color=COR_BRANCO).place(relx=0.5, rely=0.5, anchor="center")

        frame_form = ctk.CTkFrame(self, fg_color=COR_CARD, corner_radius=14)
        frame_form.pack(fill="both", padx=30, pady=22, expand=True)

        def campo(icone, label, valor_inicial=""):
            ctk.CTkLabel(frame_form, text=f"{icone}  {label}", font=FONTE_LABEL,
                         text_color=COR_LABEL_FORM).pack(anchor="w", padx=20, pady=(14, 2))
            e = ctk.CTkEntry(frame_form, font=FONTE_LABEL_NORMAL, height=42,
                             fg_color=COR_INPUT_BG,
                             border_width=2, border_color=COR_CAMPO_BORDA)
            e.pack(fill="x", padx=20)
            if valor_inicial:
                e.insert(0, str(valor_inicial))
            return e

        # editar tuple indices: 0=id, 1=data, 2=placa, 3=veiculo, 4=ano,
        #                       5=servico, 6=saldo, 7=pago, 8=status, 9=comentario
        v_placa   = editar[2] if eh_edicao else ""
        v_veiculo = editar[3] if eh_edicao else ""
        v_ano     = editar[4] if eh_edicao else ""
        v_servico = editar[5] if eh_edicao else ""
        v_saldo   = editar[6].replace("R$ ", "").strip() if eh_edicao else ""
        v_pago    = editar[7].replace("R$ ", "").strip() if eh_edicao else ""
        v_coment  = editar[9] if eh_edicao else ""
        v_data    = editar[1] if eh_edicao else datetime.now().strftime("%d/%m/%Y")

        self._placa   = campo("🚗", "Placa do Veículo  (Obrigatório)", v_placa)
        self._veiculo = campo("🚙", "Veículo / Modelo", v_veiculo)
        self._ano     = campo("📅", "Ano do Veículo", v_ano)
        _ano_var = ctk.StringVar(value=v_ano)
        self._ano.configure(textvariable=_ano_var)
        _ano_var.trace_add("write", lambda *a: aplicar_mascara_ano(_ano_var, self._ano))
        self._servico = campo("🔧", "Serviço Prestado  (Obrigatório)", v_servico)
        self._saldo   = campo("💰", "Valor Total (R$)", v_saldo)
        self._pago    = campo("💵", "Valor Pago (R$)", v_pago)
        self._coment  = campo("📝", "Comentário / Observação", v_coment)

        self._data_entry = None
        if eh_edicao:
            self._data_entry = campo("🗓️", "Data", v_data)

        def salvar():
            if not self._placa.get().strip() or not self._servico.get().strip():
                messagebox.showwarning("Aviso", "Placa e Serviço são obrigatórios!")
                return
            try:
                v_s = float(self._saldo.get().replace(",", ".") or 0)
                v_p = float(self._pago.get().replace(",", ".") or 0)
            except ValueError:
                messagebox.showerror("Erro", "Os valores financeiros devem ser numéricos.")
                return

            placa_norm = normalizar_placa(self._placa.get())

            if eh_edicao:
                nova_data = self._data_entry.get().strip() or v_data
                ServicoRepo.atualizar(
                    servico_id=editar[0],
                    placa=placa_norm,
                    servico=self._servico.get(),
                    saldo=v_s,
                    pago=v_p,
                    comentario=self._coment.get(),
                    data=nova_data,
                    veiculo=self._veiculo.get().strip(),
                    ano=self._ano.get().strip(),
                )
            else:
                ServicoRepo.inserir(
                    cliente_id=cliente_id,
                    data=datetime.now().strftime("%d/%m/%Y"),
                    placa=placa_norm,
                    servico=self._servico.get(),
                    saldo=v_s,
                    pago=v_p,
                    comentario=self._coment.get(),
                    veiculo=self._veiculo.get().strip(),
                    ano=self._ano.get().strip(),
                )
            callback_atualizar()
            self.destroy()

        frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        frame_btns.pack(pady=(0, 20))
        ctk.CTkButton(frame_btns, text="Cancelar", font=FONTE_BTN, fg_color="#AAAAAA",
                      hover_color="#888888", command=self.destroy,
                      width=140, height=44, corner_radius=10).pack(side="left", padx=10)
        ctk.CTkButton(frame_btns, text="💾  Salvar", font=FONTE_BTN, fg_color=COR_SIDEBAR,
                      hover_color=COR_SIDEBAR_HOVER, command=salvar,
                      width=140, height=44, corner_radius=10).pack(side="left", padx=10)

        # Show only after all widgets are ready — grab_set works reliably on Windows and Linux
        self.deiconify()
        _posicionar_modal(self, master)
        self.lift()
        self.focus_force()
        self.grab_set()
