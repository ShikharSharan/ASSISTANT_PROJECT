import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.backup import export_backup, import_backup
from app.sqlite_storage import _SQLCIPHER_AVAILABLE, sqlite3 as cipher_sqlite3


def _connect_encrypted(path: Path, db_key: str):
    connection = cipher_sqlite3.connect(str(path))
    connection.execute(f"PRAGMA key = \"x'{db_key}'\"")
    connection.execute("PRAGMA cipher_page_size = 4096")
    connection.execute("PRAGMA kdf_iter = 256000")
    connection.execute("PRAGMA cipher_hmac_algorithm = HMAC_SHA512")
    connection.execute("PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512")
    return connection


class BackupImportTests(unittest.TestCase):
    def test_import_replaces_database_and_removes_wal_sidecars(self):
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            source_db = temp_dir / "source.db"
            target_db = temp_dir / "assistant.db"
            backup_path = temp_dir / "snapshot.assistantbackup"

            source_conn = sqlite3.connect(source_db)
            source_conn.execute("CREATE TABLE sample (value TEXT NOT NULL)")
            source_conn.execute("INSERT INTO sample (value) VALUES (?)", ("restored",))
            source_conn.commit()
            source_conn.close()

            target_conn = sqlite3.connect(target_db)
            target_conn.execute("CREATE TABLE sample (value TEXT NOT NULL)")
            target_conn.execute("INSERT INTO sample (value) VALUES (?)", ("current",))
            target_conn.commit()
            target_conn.close()

            target_db.with_name(f"{target_db.name}-wal").write_bytes(b"stale wal")
            target_db.with_name(f"{target_db.name}-shm").write_bytes(b"stale shm")

            export_backup(backup_path, db_path=source_db)
            import_backup(backup_path, db_path=target_db)

            restored_conn = sqlite3.connect(target_db)
            try:
                row = restored_conn.execute("SELECT value FROM sample").fetchone()
            finally:
                restored_conn.close()

            self.assertEqual(row[0], "restored")
            self.assertFalse(target_db.with_name(f"{target_db.name}-wal").exists())
            self.assertFalse(target_db.with_name(f"{target_db.name}-shm").exists())
            self.assertTrue(target_db.with_suffix(".db.before-import").exists())

    @unittest.skipUnless(_SQLCIPHER_AVAILABLE, "SQLCipher is not installed")
    def test_export_encrypted_database(self):
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            source_db = temp_dir / "assistant.db"
            backup_path = temp_dir / "snapshot.assistantbackup"
            db_key = "a1" * 32

            source_conn = _connect_encrypted(source_db, db_key)
            source_conn.execute("CREATE TABLE task_active (task_id INTEGER PRIMARY KEY)")
            source_conn.execute("INSERT INTO task_active (task_id) VALUES (1)")
            source_conn.commit()
            source_conn.close()

            preview = export_backup(backup_path, db_path=source_db, db_key=db_key)

            self.assertEqual(preview.record_counts["tasks"], 1)

    @unittest.skipUnless(_SQLCIPHER_AVAILABLE, "SQLCipher is not installed")
    def test_import_backup_encrypts_database_with_current_key(self):
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            source_db = temp_dir / "source.db"
            target_db = temp_dir / "assistant.db"
            backup_path = temp_dir / "snapshot.assistantbackup"
            db_key = "b2" * 32

            source_conn = sqlite3.connect(source_db)
            source_conn.execute("CREATE TABLE sample (value TEXT NOT NULL)")
            source_conn.execute("INSERT INTO sample (value) VALUES (?)", ("restored",))
            source_conn.commit()
            source_conn.close()

            target_conn = _connect_encrypted(target_db, db_key)
            target_conn.execute("CREATE TABLE old_data (value TEXT)")
            target_conn.commit()
            target_conn.close()

            export_backup(backup_path, db_path=source_db)
            import_backup(backup_path, db_path=target_db, db_key=db_key)

            restored_conn = _connect_encrypted(target_db, db_key)
            try:
                row = restored_conn.execute("SELECT value FROM sample").fetchone()
            finally:
                restored_conn.close()

            self.assertEqual(row[0], "restored")


if __name__ == "__main__":
    unittest.main()
