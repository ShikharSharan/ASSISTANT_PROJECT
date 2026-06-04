from __future__ import annotations

import base64
import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from config import DB_PATH
from .sqlite_storage import _SQLCIPHER_AVAILABLE, sqlite3

APP_VERSION = "0.1.0"
BACKUP_EXTENSION = ".assistantbackup"
BACKUP_FORMAT = "assistant.snapshot.v1"
ENCRYPTED_MAGIC = b"ASSISTANTBACKUP1\n"
KDF_ITERATIONS = 390_000


class BackupError(Exception):
    pass


@dataclass
class BackupPreview:
    created_at: str
    app_version: str
    record_counts: dict[str, int]
    encrypted: bool = False

    def summary(self) -> str:
        counts = ", ".join(f"{key}: {value}" for key, value in self.record_counts.items())
        return (
            f"Backup date: {self.created_at}\n"
            f"App version: {self.app_version}\n"
            f"Records: {counts or 'none'}"
        )


def _derive_fernet_key(pin: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(pin.encode("utf-8")))


def _quote_sqlcipher_key(db_key: str) -> str:
    return db_key.replace("'", "''")


def _connect_database(db_path: Path, db_key: str = ""):
    conn = sqlite3.connect(str(db_path))
    if _SQLCIPHER_AVAILABLE and db_key:
        conn.execute(f"PRAGMA key = \"x'{_quote_sqlcipher_key(db_key)}'\"")
        conn.execute("PRAGMA cipher_page_size = 4096")
        conn.execute("PRAGMA kdf_iter = 256000")
        conn.execute("PRAGMA cipher_hmac_algorithm = HMAC_SHA512")
        conn.execute("PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512")
    return conn


def _record_counts(db_path: Path) -> dict[str, int]:
    if not db_path.exists():
        return {"tasks": 0, "completed_tasks": 0, "money_entries": 0, "budget_goals": 0}

    conn = sqlite3.connect(str(db_path))
    try:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }

        def count_table(table_name: str) -> int:
            if table_name not in tables:
                return 0
            return int(conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])

        return {
            "tasks": count_table("task_active"),
            "completed_tasks": count_table("task_completed"),
            "money_entries": count_table("money_entries"),
            "budget_goals": count_table("budget_goals"),
        }
    finally:
        conn.close()


def _make_snapshot_copy(
    source_db: Path,
    target_db: Path,
    source_db_key: str = "",
    target_db_key: str = "",
) -> None:
    if not source_db.exists():
        raise BackupError("Database file does not exist yet.")

    source = _connect_database(source_db, source_db_key)
    target = _connect_database(target_db, target_db_key)
    try:
        source.backup(target)
    except sqlite3.DatabaseError as exc:
        raise BackupError("Unable to read the database for backup. Check that it is unlocked.") from exc
    finally:
        target.close()
        source.close()


def _make_zip_bytes(db_path: Path, db_key: str = "") -> tuple[bytes, dict]:
    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        snapshot_db = temp_dir / "assistant.db"
        _make_snapshot_copy(db_path, snapshot_db, source_db_key=db_key)

        metadata = {
            "format": BACKUP_FORMAT,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "app_version": APP_VERSION,
            "record_counts": _record_counts(snapshot_db),
            "database_file": "assistant.db",
        }

        zip_path = temp_dir / "snapshot.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(snapshot_db, "assistant.db")
            archive.writestr("metadata.json", json.dumps(metadata, indent=2))
        return zip_path.read_bytes(), metadata


def _encrypt_payload(zip_bytes: bytes, pin: str) -> bytes:
    salt = os.urandom(16)
    token = Fernet(_derive_fernet_key(pin, salt)).encrypt(zip_bytes)
    header = {
        "format": BACKUP_FORMAT,
        "encrypted": True,
        "kdf": "PBKDF2HMAC-SHA256",
        "iterations": KDF_ITERATIONS,
        "salt": base64.b64encode(salt).decode("ascii"),
    }
    return ENCRYPTED_MAGIC + json.dumps(header).encode("utf-8") + b"\n" + token


def _decrypt_payload(path: Path, pin: str) -> bytes:
    raw = path.read_bytes()
    if not raw.startswith(ENCRYPTED_MAGIC):
        return raw
    if not pin:
        raise BackupError("This backup is encrypted. Enter the backup PIN.")

    try:
        header_line, token = raw[len(ENCRYPTED_MAGIC):].split(b"\n", 1)
        header = json.loads(header_line.decode("utf-8"))
        salt = base64.b64decode(header["salt"])
        return Fernet(_derive_fernet_key(pin, salt)).decrypt(token)
    except (ValueError, KeyError, json.JSONDecodeError, InvalidToken) as exc:
        raise BackupError("Unable to unlock this backup. Check the PIN and try again.") from exc


def export_backup(
    destination: Path,
    pin: str = "",
    db_path: Path | None = None,
    db_key: str = "",
) -> BackupPreview:
    destination = Path(destination)
    if destination.suffix != BACKUP_EXTENSION:
        destination = destination.with_suffix(BACKUP_EXTENSION)

    zip_bytes, metadata = _make_zip_bytes(Path(db_path or DB_PATH), db_key=db_key)
    payload = _encrypt_payload(zip_bytes, pin) if pin else zip_bytes
    destination.write_bytes(payload)
    return BackupPreview(
        created_at=metadata["created_at"],
        app_version=metadata["app_version"],
        record_counts=metadata["record_counts"],
        encrypted=bool(pin),
    )


def inspect_backup(path: Path, pin: str = "") -> BackupPreview:
    path = Path(path)
    try:
        zip_bytes = _decrypt_payload(path, pin)
        encrypted = path.read_bytes().startswith(ENCRYPTED_MAGIC)
        with tempfile.TemporaryDirectory() as temp_dir_name:
            zip_path = Path(temp_dir_name) / "snapshot.zip"
            zip_path.write_bytes(zip_bytes)
            with zipfile.ZipFile(zip_path) as archive:
                names = set(archive.namelist())
                if {"assistant.db", "metadata.json"} - names:
                    raise BackupError("This file is not a valid Assistant backup.")
                metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        if metadata.get("format") != BACKUP_FORMAT:
            raise BackupError("This backup format is not supported.")
        return BackupPreview(
            created_at=str(metadata.get("created_at", "Unknown")),
            app_version=str(metadata.get("app_version", "Unknown")),
            record_counts=dict(metadata.get("record_counts") or {}),
            encrypted=encrypted,
        )
    except zipfile.BadZipFile as exc:
        raise BackupError("This file is not a valid Assistant backup.") from exc


def import_backup(
    path: Path,
    pin: str = "",
    db_path: Path | None = None,
    db_key: str = "",
) -> BackupPreview:
    target_db = Path(db_path or DB_PATH)
    zip_bytes = _decrypt_payload(Path(path), pin)
    preview = inspect_backup(path, pin)

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        zip_path = temp_dir / "snapshot.zip"
        zip_path.write_bytes(zip_bytes)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extract("assistant.db", temp_dir)

        replacement_db = temp_dir / "assistant.db"
        restored_db = temp_dir / "assistant-restored.db"
        if _SQLCIPHER_AVAILABLE and db_key:
            _make_snapshot_copy(replacement_db, restored_db, target_db_key=db_key)
        else:
            restored_db = replacement_db

        target_db.parent.mkdir(parents=True, exist_ok=True)
        backup_current = target_db.with_suffix(".db.before-import")
        if target_db.exists():
            shutil.copy2(target_db, backup_current)
        for sidecar in (
            target_db.with_name(f"{target_db.name}-wal"),
            target_db.with_name(f"{target_db.name}-shm"),
        ):
            if sidecar.exists():
                sidecar.unlink()
        shutil.copy2(restored_db, target_db)
        for sidecar in (
            target_db.with_name(f"{target_db.name}-wal"),
            target_db.with_name(f"{target_db.name}-shm"),
        ):
            if sidecar.exists():
                sidecar.unlink()

    return preview
