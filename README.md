<div align="center">

# 🔧 Oficina Pro

**Sistema de gerenciamento para oficinas mecânicas**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2-green?style=for-the-badge)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/Licença-MIT-yellow?style=for-the-badge)

</div>

---

## Sobre

O **Oficina Pro** é um sistema desktop para gerenciamento de clientes, serviços e ordens de serviço em oficinas mecânicas. Desenvolvido com Python e interface gráfica moderna via CustomTkinter, conta com backup automático no Google Drive.

---

## Funcionalidades

- **Cadastro de clientes** com máscara de CPF e telefone
- **Ordens de serviço** com controle de status e pagamento
- **Relatório em HTML** pronto para impressão
- **Backup automático** no Google Drive via OAuth2
- **Interface moderna** com tema verde personalizado

---

## Pré-requisitos

- Python **3.10** ou superior
- Conta Google (para backup no Drive — opcional)

---

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/mecanica.git
cd mecanica
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais Google (veja a seção [Configurar Google Drive](#configurar-google-drive)).

---

## Como rodar

```bash
python app.py
```

Para popular o banco com dados de teste:

```bash
python scripts/seed.py
```

---

## Configurar Google Drive

O backup é **opcional**. Sem ele, o sistema funciona normalmente — apenas sem sincronização em nuvem.

Para ativar:

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto e habilite a **Google Drive API**
3. Em **Credenciais**, crie um *OAuth 2.0 Client ID* do tipo **Desktop App**
4. Baixe o arquivo `credentials.json` e coloque na raiz do projeto
5. Na primeira execução, um navegador abrirá para autorização — o `token.json` será gerado automaticamente

> **Atenção:** nunca suba `credentials.json` ou `token.json` para o repositório.

---

## Estrutura do projeto

```
mecanica/
├── app.py                    # Entry point
├── requirements.txt
├── .env.example
├── app_mecanica.spec         # Build PyInstaller
├── scripts/
│   └── seed.py               # Dados de teste
└── src/mecanica/
    ├── config.py             # Caminhos e constantes
    ├── theme.py              # Paleta de cores e tipografia
    ├── app.py                # Orquestração principal + sidebar
    ├── database/
    │   ├── connection.py     # Conexão SQLite + lock
    │   ├── schema.py         # Criação do banco
    │   └── repositories.py  # ClienteRepo, ServicoRepo
    ├── domain/
    │   ├── models.py         # Dataclasses Cliente, Servico
    │   ├── formatters.py     # fmt_moeda(), normalizar_placa()
    │   └── pagamento.py      # status_pagamento()
    ├── integracoes/
    │   └── drive_backup.py   # Backup automático no Drive
    ├── ui/
    │   ├── masks.py          # Máscaras CPF e telefone
    │   ├── widgets.py        # CardEstatistica
    │   ├── modais.py         # ModalNovoCliente, ModalServico
    │   └── pages/
    │       ├── clientes.py   # Listagem de clientes
    │       ├── detalhes.py   # Detalhes do cliente
    │       └── ordem.py      # Ordem de serviço
    └── relatorios/
        └── ordem_html.py     # Geração de relatório HTML
```

---

## Build (executável)

Para gerar um `.exe` standalone com PyInstaller:

```bash
pip install pyinstaller
pyinstaller app_mecanica.spec
```

O executável será gerado em `dist/`.

---

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
