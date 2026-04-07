import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app.backend as backend_module
import app.sqlite_storage as sqlite_storage_module
from app.sqlite_storage import SQLiteStorage


class IsolatedDatabaseTestCase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "assistant_test.db"
        self.db_patch = patch.object(sqlite_storage_module, "DB_PATH", self.db_path)
        self.db_patch.start()

        self.storage = SQLiteStorage()
        self.original_storage = backend_module.storage
        backend_module.storage = self.storage

    def tearDown(self):
        backend_module.storage = self.original_storage
        self.storage.conn.close()
        self.db_patch.stop()
        self.temp_dir.cleanup()
        super().tearDown()
