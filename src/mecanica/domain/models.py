"""Domain models — thin data containers used across UI and repositories."""

from dataclasses import dataclass


@dataclass
class Cliente:
    id: int
    nome: str
    cpf: str
    endereco: str
    cidade: str
    telefone: str
    placa: str


@dataclass
class Servico:
    id: int
    cliente_id: int
    data: str
    placa: str
    servico: str
    saldo: float
    pago: float
    comentario: str
