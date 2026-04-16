# Projeto Mecânica — Documentação e Decisões

## Status atual

Refatoração completa concluída (Fases 0-6):
- **Arquitetura**: monólito de 1261 linhas → 16 módulos organizados em `src/mecanica/`
- **Design visual**: atualizado com paleta verde mais profunda e tipografia ajustada
- **Bugs corrigidos**:
  1. ✅ Exclusão de cliente em transação SQL única (não mais 2 queries soltas)
  2. ✅ Lock de banco durante backup do Drive (evita read de arquivo parcialmente gravado)
  3. ✅ Formatação monetária centralizada em `domain/formatters.py`
  4. ✅ Normalização de placa em repositório (sempre `.upper()`)
  5. ✅ Status de pagamento extraído para `domain/pagamento.py`
  6. ✅ **Máscaras de entrada (CPF/telefone)** — resolvido o bug de dígitos em ordem invertida

## Bug das máscaras resolvido

**Problema original:** ao digitar `140` e continuar com `322`, o resultado era `140.223` em vez de `140.322`.

**Causa raiz:** o event trace de `StringVar` dispara **antes** do cursor do tkinter se mover para a posição pós-keystroke. A máscara lia o cursor na posição antiga e o restaurava antes do novo dígito ser inserido — então o caractere seguinte ia para o lugar errado.

**Solução (em `src/mecanica/ui/masks.py`):**
- Usar `entry.after(0, _run)` para adiar a execução da máscara até após o loop de eventos (cursor já está na posição correta)
- Guard `_pending` evita agendar múltiplas execuções redundantes em keystrokes rápidos
- Refatorar em função genérica `_make_mask(formatter)` para reutilização com CPF e telefone

**Código-chave:**
```python
_pending[vid] = True
def _run():
    _pending.pop(vid, None)
    # Agora cursor já está na posição post-keystroke
    cursor_pos = entry._entry.index("insert")
    # ... aplica máscara com cursor correto
entry.after(0, _run)
```

## Estrutura do projeto pós-refatoração

```
mecanica/
├── app.py                    # entry point
├── .env, oficina.db, credentials.json, token.json
├── app_mecanica.spec         # PyInstaller (atualizado)
├── scripts/
│   └── seed.py              # data population
└── src/mecanica/
    ├── config.py             # caminhos, constantes de config
    ├── theme.py              # paleta + tipografia (centralizado)
    ├── app.py                # AppOficina (orquestração + sidebar)
    ├── database/
    │   ├── connection.py     # get_conn() + db_lock
    │   ├── schema.py         # iniciar_db()
    │   └── repositories.py   # ClienteRepo, ServicoRepo
    ├── domain/
    │   ├── models.py         # dataclasses Cliente, Servico
    │   ├── formatters.py     # fmt_moeda(), normalizar_placa()
    │   └── pagamento.py      # status_pagamento()
    ├── integracoes/
    │   └── drive_backup.py   # DriveBackup (com db_lock)
    ├── ui/
    │   ├── masks.py          # aplicar_mascara_cpf/telefone (CORRIGIDO)
    │   ├── widgets.py        # CardEstatistica
    │   ├── modais.py         # ModalNovoCliente, ModalServico
    │   └── pages/
    │       ├── clientes.py   # PaginaClientes
    │       ├── detalhes.py   # PaginaDetalhes
    │       └── ordem.py      # PaginaOrdem
    └── relatorios/
        └── ordem_html.py     # gerar_html(), abrir_impressao()
```

## Mudanças de design visual

| Elemento | Antes | Depois |
|---|---|---|
| COR_SIDEBAR | `#1E7A48` | `#166534` (verde mais profundo) |
| COR_SIDEBAR_ATIVO | `#28A05E` | `#16A34A` |
| COR_FUNDO | `#F0F2F5` | `#F1F5F9` (cinza-azulado) |
| COR_TEXTO_ESCURO | `#1A1A2E` | `#0F172A` (contraste maior) |
| COR_TEXTO_MEDIO | `#555770` | `#475569` |
| COR_PERIGO | `#E74C3C` | `#DC2626` |
| COR_VERDE_CARD | `#2D8C56` | `#16A34A` |
| COR_AZUL_CARD | `#2980B9` | `#2563EB` |
| COR_LARANJA_CARD | `#E67E22` | `#D97706` |
| FONTE_TITULO | 26pt | 24pt |
| FONTE_SUBTITULO | 20pt | 18pt |
| FONTE_CARD | 28pt | 26pt |

## Como rodar

```bash
python app.py
```

Para seed com dados de teste:
```bash
python scripts/seed.py
```

Para build com PyInstaller:
```bash
pyinstaller app_mecanica.spec
```

## Próximos passos (fora do escopo desta refatoração)

- Testes automatizados (unit + integration)
- Migração de schema: adicionar índices, ON DELETE CASCADE nas FKs, datas em ISO 8601
- Aprimoramentos de UX: undo/redo, relatórios em PDF, sync offline, dark mode
