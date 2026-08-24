<div align="center">

# 🔧 Oficina Pro

**Management system for auto repair shops**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2-green?style=for-the-badge)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

</div>

---

## About

**Oficina Pro** is a desktop system for managing customers, services, and work orders for auto repair shops. Built with Python and a modern GUI via CustomTkinter, it includes automatic backup to Google Drive.

---

## Features

- **Customer registration** with CPF and phone number masks
- **Work orders** with status and payment tracking
- **HTML report** ready for printing
- **Automatic backup** to Google Drive via OAuth2
- **Modern interface** with a custom green theme

---

## Prerequisites

- Python **3.10** or higher
- Google account (for Drive backup — optional)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/mecanica.git
cd mecanica
```

### 2. Create and activate the virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` with your Google credentials (see the [Configure Google Drive](#configure-google-drive) section).

---

## Running the app

```bash
python app.py
```

To populate the database with test data:

```bash
python scripts/seed.py
```

---

## Configure Google Drive

Backup is **optional**. Without it, the system works normally — just without cloud syncing.

To enable it:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable the **Google Drive API**
3. Under **Credentials**, create an *OAuth 2.0 Client ID* of type **Desktop App**
4. Download the `credentials.json` file and place it in the project root
5. On first run, a browser window will open for authorization — `token.json` will be generated automatically

> **Warning:** never commit `credentials.json` or `token.json` to the repository.

---

## Project structure

```
mecanica/
├── app.py                    # Entry point
├── requirements.txt
├── .env.example
├── app_mecanica.spec         # PyInstaller build
├── scripts/
│   └── seed.py               # Test data
└── src/mecanica/
    ├── config.py             # Paths and constants
    ├── theme.py              # Color palette and typography
    ├── app.py                # Main orchestration + sidebar
    ├── database/
    │   ├── connection.py     # SQLite connection + lock
    │   ├── schema.py         # Database creation
    │   └── repositories.py  # ClienteRepo, ServicoRepo
    ├── domain/
    │   ├── models.py         # Cliente, Servico dataclasses
    │   ├── formatters.py     # fmt_moeda(), normalizar_placa()
    │   └── pagamento.py      # status_pagamento()
    ├── integracoes/
    │   └── drive_backup.py   # Automatic Drive backup
    ├── ui/
    │   ├── masks.py          # CPF and phone masks
    │   ├── widgets.py        # CardEstatistica
    │   ├── modais.py         # ModalNovoCliente, ModalServico
    │   └── pages/
    │       ├── clientes.py   # Customer listing
    │       ├── detalhes.py   # Customer details
    │       └── ordem.py      # Work order
    └── relatorios/
        └── ordem_html.py     # HTML report generation
```

---

## Build (executable)

To generate a standalone `.exe` with PyInstaller:

```bash
pip install pyinstaller
pyinstaller app_mecanica.spec
```

The executable will be generated in `dist/`.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
