"""Database schema creation and migrations."""

from src.mecanica.database.connection import get_conn


def iniciar_db() -> None:
    """Create tables and run pending migrations. Safe to call on every startup."""
    with get_conn(write=True) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                nome     TEXT NOT NULL,
                cpf      TEXT,
                endereco TEXT,
                cidade   TEXT,
                telefone TEXT,
                placa    TEXT
            )
        """)
        # Migration: add 'placa' column if it was missing in older databases
        try:
            cur.execute("ALTER TABLE clientes ADD COLUMN placa TEXT")
        except Exception:
            pass  # Column already exists — ignore

        cur.execute("""
            CREATE TABLE IF NOT EXISTS servicos (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                data       TEXT,
                placa      TEXT,
                servico    TEXT,
                saldo      REAL,
                pago       REAL,
                comentario TEXT,
                FOREIGN KEY(cliente_id) REFERENCES clientes(id)
            )
        """)
