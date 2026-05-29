"""
Popula o banco com clientes e serviços de teste.
Uso: python scripts/seed.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mecanica.database.schema import iniciar_db
from src.mecanica.database.repositories import ClienteRepo, ServicoRepo


def _os_json(cliente, fone, veiculo, ano, placa, data, linhas: list[tuple]) -> tuple[str, float]:
    """Monta o ordem_json e retorna (json_str, total)."""
    rows = []
    total = 0.0
    for qtd, desc, unit in linhas:
        tot = round(qtd * unit, 2)
        total += tot
        rows.append((str(qtd), desc, f"{unit:.2f}", f"{tot:.2f}"))
    dados = {
        "veiculo": veiculo,
        "ano": ano,
        "placa": placa,
        "data": data,
        "cliente": cliente,
        "fone": fone,
        "total": f"{total:.2f}",
        "linhas": rows,
    }
    return json.dumps(dados, ensure_ascii=False), total


def popular():
    iniciar_db()

    clientes = [
        dict(nome="João Silva",     cpf="123.456.789-00", telefone="(45) 99999-1111", placa="ABC1234", endereco="Rua das Flores, 10",        cidade="Toledo"),
        dict(nome="Maria Oliveira", cpf="987.654.321-11", telefone="(45) 98888-2222", placa="XYZ5678", endereco="Av. Brasil, 500",            cidade="Toledo"),
        dict(nome="Carlos Souza",   cpf="444.555.666-77", telefone="(45) 97777-3333", placa="KML9090", endereco="Rua Santos Dumont, 123",     cidade="Cascavel"),
        dict(nome="Ana Beatriz",    cpf="111.222.333-44", telefone="(45) 99111-4444", placa="BRA2E19", endereco="Rua Paraná, 88",             cidade="Toledo"),
        dict(nome="Marcos Pontes",  cpf="555.444.333-22", telefone="(45) 99222-5555", placa="JHT4455", endereco="Rua XV de Novembro, 202",    cidade="Ouro Verde"),
        dict(nome="Fernanda Lima",  cpf="666.777.888-99", telefone="(45) 99333-6666", placa="OWP1020", endereco="Av. Parigot, 1500",          cidade="Toledo"),
        dict(nome="Ricardo Alves",  cpf="222.333.444-55", telefone="(45) 99444-7777", placa="QWE9988", endereco="Rua General Estilac, 45",    cidade="Toledo"),
        dict(nome="Patrícia Meira", cpf="333.444.555-66", telefone="(45) 99555-8888", placa="MKP3321", endereco="Rua Almirante Barroso, 90",  cidade="Cascavel"),
        dict(nome="Lucas Gabriel",  cpf="777.888.999-00", telefone="(45) 99666-9999", placa="LUI0011", endereco="Rua Sete de Setembro, 300",  cidade="São Pedro"),
        dict(nome="Sonia Abrão",    cpf="888.999.000-11", telefone="(45) 99777-0000", placa="BIO2024", endereco="Loteamento Biopark",         cidade="Toledo"),
    ]

    for c in clientes:
        ClienteRepo.inserir(**c)

    # Busca os IDs recém inseridos pelo nome
    todos = {c.nome: c for c in ClienteRepo.listar()}

    def cli(nome):
        return todos[nome]

    # ------------------------------------------------------------------
    # Serviços simples (sem ordem de serviço impressa)
    # ------------------------------------------------------------------
    servicos_simples = [
        (cli("Carlos Souza"),   "10/03/2026", "KML9090", "Freios Traseiros",         450.0,    0.0,  "Aguardando PIX.",          "Fiat Strada",   "2019"),
        (cli("Ana Beatriz"),    "05/03/2026", "BRA2E19", "Revisão 50k km",           850.0,  425.0,  "Metade paga.",             "VW Polo",       "2021"),
        (cli("Marcos Pontes"),  "06/03/2026", "JHT4455", "Bateria Nova",             380.0,  380.0,  "Garantia 1 ano.",          "Chevrolet S10", "2018"),
        (cli("Fernanda Lima"),  "08/03/2026", "OWP1020", "Alinhamento e Balanceam.", 150.0,  150.0,  "Sem observações.",         "Honda HR-V",    "2022"),
        (cli("Ricardo Alves"),  "10/03/2026", "QWE9988", "Lâmpada Farol",             45.0,   45.0,  "Substituição rápida.",     "Toyota Corolla","2020"),
        (cli("Patrícia Meira"), "11/03/2026", "MKP3321", "Embreagem",               1800.0, 1000.0,  "Saldo para o dia 20.",     "Ford Ka",       "2017"),
        (cli("Lucas Gabriel"),  "12/03/2026", "LUI0011", "Limpeza Radiador",         220.0,  220.0,  "Ok.",                      "Renault Kwid",  "2023"),
        (cli("Sonia Abrão"),    "13/03/2026", "BIO2024", "Filtro Ar Condicionado",   110.0,    0.0,  "Pendente.",                "Jeep Renegade", "2024"),
    ]

    for c, data, placa, servico, saldo, pago, coment, veiculo, ano in servicos_simples:
        ServicoRepo.inserir(
            cliente_id=c.id, data=data, placa=placa, servico=servico,
            saldo=saldo, pago=pago, comentario=coment, veiculo=veiculo, ano=ano,
        )

    # ------------------------------------------------------------------
    # Serviços com Ordem de Serviço completa (ordem_json preenchido)
    # ------------------------------------------------------------------
    c = cli("João Silva")
    os_json, total = _os_json(
        cliente=c.nome, fone=c.telefone, veiculo="Fiat Palio", ano="2015",
        placa="ABC1234", data="01/03/2026",
        linhas=[
            (1, "Troca de Óleo 5W30",      120.0),
            (1, "Filtro de Óleo",            35.0),
            (1, "Mão de Obra",               95.0),
        ],
    )
    ServicoRepo.inserir(
        cliente_id=c.id, data="01/03/2026", placa="ABC1234",
        servico="Ordem de Serviço", saldo=total, pago=total,
        comentario="Pago à vista.", veiculo="Fiat Palio", ano="2015",
        ordem_json=os_json,
    )

    c = cli("João Silva")
    os_json, total = _os_json(
        cliente=c.nome, fone=c.telefone, veiculo="Fiat Palio", ano="2015",
        placa="ABC1234", data="13/03/2026",
        linhas=[
            (1,  "Troca Escapamento Traseiro", 180.0),
            (1,  "Junta do Escapamento",        45.0),
            (1,  "Mão de Obra",                125.0),
        ],
    )
    ServicoRepo.inserir(
        cliente_id=c.id, data="13/03/2026", placa="ABC1234",
        servico="Ordem de Serviço", saldo=total, pago=total,
        comentario="Segunda visita do mês.", veiculo="Fiat Palio", ano="2015",
        ordem_json=os_json,
    )

    c = cli("Maria Oliveira")
    os_json, total = _os_json(
        cliente=c.nome, fone=c.telefone, veiculo="Hyundai HB20", ano="2020",
        placa="XYZ5678", data="02/03/2026",
        linhas=[
            (4, "Pneu Aro 15 Michelin",    300.0),
            (1, "Balanceamento (4 rodas)",   80.0),
            (1, "Mão de Obra",              100.0),
        ],
    )
    ServicoRepo.inserir(
        cliente_id=c.id, data="02/03/2026", placa="XYZ5678",
        servico="Ordem de Serviço", saldo=total, pago=total,
        comentario="Pago à vista.", veiculo="Hyundai HB20", ano="2020",
        ordem_json=os_json,
    )

    print("Banco populado com sucesso!")
    print(f"  {len(clientes)} clientes")
    print(f"  {len(servicos_simples)} serviços simples")
    print("  3 ordens de serviço completas (João Silva ×2, Maria Oliveira ×1)")


if __name__ == "__main__":
    popular()
