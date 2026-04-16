import os
import sys

# Directory resolution (works both as script and PyInstaller .exe)
if getattr(sys, "frozen", False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    # Go up from src/mecanica/ to project root
    SCRIPT_DIR = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

DB_PATH          = os.path.join(SCRIPT_DIR, "oficina.db")
CREDENTIALS_JSON = os.path.join(SCRIPT_DIR, "credentials.json")
TOKEN_JSON       = os.path.join(SCRIPT_DIR, "token.json")
DRIVE_FILENAME   = "oficina_backup.db"

DRIVE_SCOPES         = ["https://www.googleapis.com/auth/drive.file"]
BACKUP_INTERVALO_MIN = 30
MIN_LINHAS_CLIENTES  = 15
