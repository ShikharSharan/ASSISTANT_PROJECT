import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.backup import export_backup, import_backup


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


if __name__ == "__main__":
    unittest.main()
