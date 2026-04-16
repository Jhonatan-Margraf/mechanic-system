"""
Data-access layer.

All SQL lives here — UI and domain code must never import sqlite3 directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.mecanica.database.connection import get_conn


# ---------------------------------------------------------------------------
# Value objects (lightweight, no behaviour)
# ---------------------------------------------------------------------------

@dataclass
class ClienteRow:
    id: int
    nome: str
    cpf: str
    endereco: str
    cidade: str
    telefone: str
    placa: str


@dataclass
class ServicoRow:
    id: int
    cliente_id: int
    data: str
    placa: str
    servico: str
    saldo: float
    pago: float
    comentario: str


# ---------------------------------------------------------------------------
# ClienteRepo
# ---------------------------------------------------------------------------

class ClienteRepo:
    @staticmethod
    def listar(termo: str = "") -> list[ClienteRow]:
        """Return all clients, optionally filtered by name or plate."""
        with get_conn() as conn:
            cur = conn.cursor()
            if termo:
                cur.execute(
                    "SELECT * FROM clientes WHERE nome LIKE ? OR placa LIKE ?",
                    (f"%{termo}%", f"%{termo}%"),
                )
            else:
                cur.execute("SELECT * FROM clientes")
            return [ClienteRow(*row) for row in cur.fetchall()]

    @staticmethod
    def contar_servicos_status() -> tuple[int, int]:
        """Return (total_pagos, total_abertos) across all clients."""
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM servicos WHERE pago >= saldo")
            pagos = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM servicos WHERE pago < saldo")
            abertos = cur.fetchone()[0]
        return pagos, abertos

    @staticmethod
    def inserir(
        nome: str,
        cpf: str,
        endereco: str,
        cidade: str,
        telefone: str,
        placa: str,
    ) -> None:
        with get_conn(write=True) as conn:
            conn.execute(
                "INSERT INTO clientes (nome, cpf, endereco, cidade, telefone, placa) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (nome, cpf, endereco, cidade, telefone, placa),
            )

    @staticmethod
    def excluir(cliente_id: int | str) -> None:
        """Delete client and all their services atomically."""
        with get_conn(write=True) as conn:
            conn.execute("DELETE FROM servicos WHERE cliente_id = ?", (cliente_id,))
            conn.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))


# ---------------------------------------------------------------------------
# ServicoRepo
# ---------------------------------------------------------------------------

class ServicoRepo:
    @staticmethod
    def listar(cliente_id: int | str, termo: str = "") -> list[ServicoRow]:
        """Return services for a client, optionally filtered by plate or description."""
        with get_conn() as conn:
            cur = conn.cursor()
            q = "SELECT * FROM servicos WHERE cliente_id = ?"
            params: list = [cliente_id]
            if termo:
                q += " AND (placa LIKE ? OR servico LIKE ?)"
                params += [f"%{termo}%", f"%{termo}%"]
            q += " ORDER BY id DESC"
            cur.execute(q, params)
            return [ServicoRow(*row) for row in cur.fetchall()]

    @staticmethod
    def inserir(
        cliente_id: int | str,
        data: str,
        placa: str,
        servico: str,
        saldo: float,
        pago: float,
        comentario: str,
    ) -> None:
        with get_conn(write=True) as conn:
            conn.execute(
                "INSERT INTO servicos "
                "(cliente_id, data, placa, servico, saldo, pago, comentario) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (cliente_id, data, placa.upper(), servico, saldo, pago, comentario),
            )

    @staticmethod
    def atualizar(
        servico_id: int | str,
        placa: str,
        servico: str,
        saldo: float,
        pago: float,
        comentario: str,
        data: str,
    ) -> None:
        with get_conn(write=True) as conn:
            conn.execute(
                "UPDATE servicos "
                "SET placa=?, servico=?, saldo=?, pago=?, comentario=?, data=? "
                "WHERE id=?",
                (placa.upper(), servico, saldo, pago, comentario, data, servico_id),
            )

    @staticmethod
    def excluir(servico_id: int | str) -> None:
        with get_conn(write=True) as conn:
            conn.execute("DELETE FROM servicos WHERE id = ?", (servico_id,))
