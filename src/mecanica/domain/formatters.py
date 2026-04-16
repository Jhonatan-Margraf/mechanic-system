"""Formatting helpers for display values."""


def fmt_moeda(valor: float) -> str:
    """Format a float as Brazilian currency string, e.g. 'R$ 1.250,00'."""
    return f"R$ {valor:.2f}"


def normalizar_placa(placa: str) -> str:
    """Return plate in uppercase, stripped of extra whitespace."""
    return placa.strip().upper()
