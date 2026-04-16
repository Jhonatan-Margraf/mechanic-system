"""
Google Drive backup integration.

DriveBackup authenticates via OAuth2 and uploads a snapshot of the database
to the user's Drive every BACKUP_INTERVALO_MIN minutes.

The db_lock from database.connection is acquired before reading the database
file so that a backup never captures a partially-written state.
"""

import os
import sqlite3
import tempfile
import threading
import time
from datetime import datetime

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    DRIVE_DISPONIVEL = True
except ImportError:
    DRIVE_DISPONIVEL = False

from src.mecanica.config import (
    BACKUP_INTERVALO_MIN,
    CREDENTIALS_JSON,
    DB_PATH,
    DRIVE_FILENAME,
    DRIVE_SCOPES,
    SCRIPT_DIR,
    TOKEN_JSON,
)
from src.mecanica.database.connection import db_lock
from src.mecanica.theme import COR_AZUL_CARD, COR_BRANCO, COR_PERIGO, COR_VERDE_CARD


class DriveBackup:
    """
    Manages OAuth2 authentication and database upload to Google Drive.
    Upload runs in a background thread to avoid blocking the UI.
    """

    def __init__(self, on_status_change=None):
        """
        on_status_change(msg: str, cor: str) — callback to update the sidebar indicator.
        """
        self._creds    = None
        self._service  = None
        self._file_id  = None          # Drive file ID (reused on updates)
        self._lock     = threading.Lock()
        self._callback = on_status_change
        self._parar    = threading.Event()
        self._thread   = None

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def autenticar(self) -> bool:
        """
        Run the OAuth2 flow.
        First run opens the browser for user authorization.
        Subsequent runs reuse the token saved in token.json.
        Returns True on success.
        """
        if not DRIVE_DISPONIVEL:
            self._status("❌ Bibliotecas do Drive não instaladas", COR_PERIGO)
            return False

        if not os.path.exists(CREDENTIALS_JSON):
            self._status("⚠️ credentials.json não encontrado", "#E67E22")
            return False

        try:
            creds = None
            if os.path.exists(TOKEN_JSON):
                creds = Credentials.from_authorized_user_file(TOKEN_JSON, DRIVE_SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        CREDENTIALS_JSON, DRIVE_SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                with open(TOKEN_JSON, "w") as f:
                    f.write(creds.to_json())

            self._creds   = creds
            self._service = build("drive", "v3", credentials=creds)
            self._status("✅ Drive conectado", COR_VERDE_CARD)
            return True

        except Exception as e:
            self._status(f"❌ Erro auth: {e}", COR_PERIGO)
            return False

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    def fazer_backup(self) -> bool:
        """
        Snapshot the database to a temp file (avoids SQLite locks) and
        upload/update it on Drive. Thread-safe — acquires db_lock so that
        no write can happen while we copy the file.
        """
        if not self._service:
            self._status("⚠️ Drive não autenticado", "#E67E22")
            return False

        with self._lock:
            tmp_db = None
            try:
                self._status("⬆️ Salvando no Drive…", COR_AZUL_CARD)

                tmp_fd, tmp_db = tempfile.mkstemp(
                    prefix="oficina_backup_", suffix=".db", dir=SCRIPT_DIR
                )
                os.close(tmp_fd)

                # Acquire db_lock to prevent concurrent writes during snapshot
                with db_lock:
                    conn_origem  = sqlite3.connect(
                        f"file:{DB_PATH}?mode=ro", uri=True, timeout=30
                    )
                    conn_destino = sqlite3.connect(tmp_db, timeout=30)
                    try:
                        with conn_destino:
                            conn_origem.backup(conn_destino)
                    finally:
                        conn_origem.close()
                        conn_destino.close()

                agora = datetime.now().strftime("%d/%m/%Y %H:%M")

                with open(tmp_db, "rb") as fp:
                    media = MediaIoBaseUpload(
                        fp, mimetype="application/x-sqlite3", resumable=False
                    )

                    if self._file_id:
                        self._service.files().update(
                            fileId=self._file_id,
                            media_body=media,
                            body={"name": DRIVE_FILENAME},
                        ).execute()
                    else:
                        res = self._service.files().list(
                            q=f"name='{DRIVE_FILENAME}' and trashed=false",
                            fields="files(id)",
                        ).execute()
                        arquivos = res.get("files", [])

                        if arquivos:
                            self._file_id = arquivos[0]["id"]
                            self._service.files().update(
                                fileId=self._file_id,
                                media_body=media,
                                body={"name": DRIVE_FILENAME},
                            ).execute()
                        else:
                            arq = self._service.files().create(
                                body={"name": DRIVE_FILENAME},
                                media_body=media,
                                fields="id",
                            ).execute()
                            self._file_id = arq.get("id")

                self._status(f"☁️ Backup {agora}", COR_VERDE_CARD)
                return True

            except Exception as e:
                self._status(f"❌ Falha: {e}", COR_PERIGO)
                return False
            finally:
                self._remover_arquivo_com_retry(tmp_db)

    # ------------------------------------------------------------------
    # Automatic backup loop
    # ------------------------------------------------------------------

    def iniciar_loop(self, intervalo_min: int = BACKUP_INTERVALO_MIN) -> None:
        """Start a background thread that backs up every *intervalo_min* minutes."""
        self._parar.clear()
        self._thread = threading.Thread(
            target=self._loop_backup, args=(intervalo_min,), daemon=True
        )
        self._thread.start()

    def parar_loop(self) -> None:
        self._parar.set()

    def _loop_backup(self, intervalo_min: int) -> None:
        segundos = intervalo_min * 60
        while not self._parar.wait(timeout=segundos):
            self.fazer_backup()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _status(self, msg: str, cor: str = COR_BRANCO) -> None:
        if self._callback:
            try:
                self._callback(msg, cor)
            except Exception:
                pass

    def _remover_arquivo_com_retry(
        self, caminho: str | None, tentativas: int = 12, intervalo: float = 0.25
    ) -> None:
        """Retry file removal to handle Windows handle-release delays."""
        if not caminho or not os.path.exists(caminho):
            return
        for tentativa in range(tentativas):
            try:
                os.remove(caminho)
                return
            except PermissionError:
                if tentativa == tentativas - 1:
                    raise
                time.sleep(intervalo)

    def limpar_temporarios(self) -> None:
        """Remove leftover temp backup files from previous runs."""
        import glob
        try:
            pattern = os.path.join(SCRIPT_DIR, "oficina_backup_*.db")
            for tmp_arquivo in glob.glob(pattern):
                try:
                    os.remove(tmp_arquivo)
                except Exception:
                    pass
        except Exception:
            pass
