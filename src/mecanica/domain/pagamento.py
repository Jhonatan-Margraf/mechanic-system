"""Payment status business rules."""


def status_pagamento(saldo: float, pago: float) -> tuple[str, str]:
    """
    Return (label, tag) for a service based on amounts.

    label — human-readable string shown in the UI
    tag   — short identifier used as Treeview row tag for styling
    """
    if pago >= saldo:
        return "✅ Pago", "pago"
    if pago > 0:
        return "⚠️ Parcial", "parcial"
    return "❌ Não Pago", "naopago"


# Mapping from ComboBox display values to full labels returned by status_pagamento
FILTRO_STATUS_MAP: dict[str, str] = {
    "Pago":     "✅ Pago",
    "Parcial":  "⚠️ Parcial",
    "Não Pago": "❌ Não Pago",
}
