# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Rodar o app

```bash
python app.py
```

Não há testes automatizados nem linter configurado. Para popular o banco com dados de teste:

```bash
python scripts/seed.py
```

## Stack

- **GUI:** CustomTkinter 5.2.2 + **CTkTable 1.1** (tabelas — NÃO usar ttk.Treeview)
- **Banco:** SQLite 3 via `src/mecanica/database/connection.py` (thread-safe com lock)
- **Backup:** Google Drive API v2 (opcional; requer `credentials.json` na raiz)
- **Build:** PyInstaller (`app_mecanica.spec`)

## Arquitetura

```
app.py                        ← entry point; adiciona raiz ao sys.path
src/mecanica/
  app.py                      ← AppOficina(CTk): janela principal, sidebar, navegação
  theme.py                    ← ÚNICA fonte de cores e fontes — editar aqui primeiro
  config.py                   ← caminhos de arquivo e constantes (DB_PATH, etc.)
  database/
    schema.py                 ← CREATE TABLE + migrations via ALTER TABLE no startup
    repositories.py           ← ClienteRepo, ServicoRepo (todo SQL fica aqui)
  domain/
    models.py                 ← dataclasses Cliente, Servico (não têm comportamento)
    pagamento.py              ← status_pagamento() → (label, tag)
    formatters.py             ← fmt_moeda(), normalizar_placa()
  ui/
    widgets.py                ← CardEstatistica (card de estatística reutilizável)
    modais.py                 ← ModalNovoCliente, ModalServico (CTkToplevel)
    masks.py                  ← máscaras CPF/telefone via StringVar.trace
    pages/
      clientes.py             ← lista de clientes com CTkTable
      detalhes.py             ← histórico de serviços do cliente com CTkTable
      ordem.py                ← ordem de serviço (grid de CTkEntry, sem CTkTable)
  relatorios/
    ordem_html.py             ← gera HTML e abre no navegador para impressão
```

## Fluxo de navegação

`AppOficina` controla um único `self.area` (CTkFrame). Navegar entre páginas = destruir filhos de `self.area` e montar a nova página. Não há roteador — apenas `navegar_clientes()`, `navegar_detalhes()`, `navegar_ordem()`. O cliente selecionado é passado via `self.app.cliente_selecionado`.

## Tabelas (CTkTable)

As tabelas são **destruídas e recriadas** em cada `_carregar()`. Seleção de linha é manual:

```python
self.table.edit_row(row, fg_color=COR_SELECIONADA, hover_color=COR_SELECIONADA, text_color="#166534")
```

O header sempre recebe `edit_row(0, text_color="#fff", hover_color=COR_SIDEBAR)` após a criação. Larguras de coluna são aplicadas via `self.table.grid_columnconfigure(col_idx, minsize=width)`.

## Banco de dados

`SELECT *` + `ServicoRow(*row)` — a ordem dos campos no dataclass deve bater com a ordem das colunas no CREATE TABLE:

```
id, cliente_id, data, placa, servico, saldo, pago, comentario, veiculo, ano
```

Novas colunas: sempre adicionar no fim do dataclass com default `""` e criar migration em `schema.py`:

```python
try:
    cur.execute("ALTER TABLE servicos ADD COLUMN nova_col TEXT")
except Exception:
    pass
```

## Design system

Paleta centralizada em `theme.py`. Cores-chave:

| Token | Valor | Uso |
|---|---|---|
| `COR_SIDEBAR` | `#2A8C55` | Verde primário, headers de tabela, botões |
| `COR_SIDEBAR_HOVER` | `#207244` | Hover de botões verdes |
| `COR_INPUT_BG` | `#F0F0F0` | Fundo de entradas e barras de busca |
| `COR_LABEL_FORM` | `#52A476` | Labels em formulários/modais |
| `COR_SELECIONADA` | `#BBF7D0` | Linha selecionada na tabela |

Fontes: `Arial Black` (títulos), `Arial Bold` (labels, botões, corpo).
