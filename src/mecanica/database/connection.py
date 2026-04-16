"""
Shared database connection and write lock.

The lock must be acquired by any write operation AND by DriveBackup.fazer_backup()
to prevent reading a partially-written database file.
"""

import sqlite3
import threading
from contextlib import contextmanager
from src.mecanica.config import DB_PATH

# Single lock shared across all modules (imported as a singleton)
db_lock = threading.Lock()


@contextmanager
def get_conn(write: bool = False):
    """Context-manager that yields an open SQLite connection.

    If *write* is True, acquires db_lock before connecting so that backup
    threads cannot read the file mid-transaction.
    """
    if write:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        try:
            yield conn
        finally:
            conn.close()
