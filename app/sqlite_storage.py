import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
from .errors import AssistantDataError, RecordNotFoundError, ValidationError
from .storage_base import StorageBase
from .models import Task, MoneyEntry
from .validation import (
    MONEY_ENTRY_TYPES,
    normalize_money_entry_input,
    normalize_period,
    normalize_record_id,
    normalize_task_input,
)
from config import DB_PATH

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

class SQLiteStorage(StorageBase):
    def __init__(self):
        self.db_path = Path(DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, timeout=5.0)
        self.conn.row_factory = sqlite3.Row
        self._configure_connection()
        self._init_db()

    def _configure_connection(self):
        self.conn.execute("PRAGMA busy_timeout = 5000")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA foreign_keys = ON")

    def _init_db(self):
        try:
            with self.conn:
                cur = self.conn.cursor()
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL CHECK (length(trim(title)) > 0),
                        description TEXT NOT NULL DEFAULT '',
                        date TEXT NOT NULL,
                        priority TEXT NOT NULL DEFAULT 'Medium'
                            CHECK (priority IN ('Low', 'Medium', 'High')),
                        done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1))
                    );
                    """
                )
                columns = {
                    row["name"]
                    for row in cur.execute("PRAGMA table_info(tasks)").fetchall()
                }
                if "completed_at" not in columns:
                    cur.execute("ALTER TABLE tasks ADD COLUMN completed_at TEXT")
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS money_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entry_type TEXT NOT NULL
                            CHECK (entry_type IN ('Income', 'Expense', 'EMI', 'Credit', 'Given', 'Taken')),
                        amount REAL NOT NULL CHECK (amount > 0),
                        date TEXT NOT NULL,
                        note TEXT NOT NULL DEFAULT '',
                        person TEXT NOT NULL DEFAULT ''
                    );
                    """
                )
                cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_done_id ON tasks (done, id DESC)")
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_money_entries_date_type "
                    "ON money_entries (date DESC, entry_type, id DESC)"
                )
        except sqlite3.Error as exc:
            raise AssistantDataError("Unable to initialize the local database.") from exc

    def _execute_read(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        try:
            return self.conn.execute(query, params).fetchall()
        except sqlite3.Error as exc:
            raise AssistantDataError("Unable to read data from the local database.") from exc

    def _execute_write(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        try:
            with self.conn:
                return self.conn.execute(query, params)
        except sqlite3.Error as exc:
            raise AssistantDataError("Unable to save data to the local database.") from exc

    def _row_exists(self, table_name: str, record_id: int) -> bool:
        try:
            row = self.conn.execute(
                f"SELECT 1 FROM {table_name} WHERE id = ? LIMIT 1",
                (record_id,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise AssistantDataError("Unable to read data from the local database.") from exc
        return row is not None

    # ---- tasks ----
    def insert_task(self, title: str, description: str, priority: str) -> int:
        normalized_title, normalized_description, normalized_priority = normalize_task_input(
            title,
            description,
            priority,
        )
        now_str = datetime.now().strftime(DATE_FORMAT)
        cur = self._execute_write(
            "INSERT INTO tasks (title, description, date, priority, done) VALUES (?, ?, ?, ?, ?)",
            (normalized_title, normalized_description, now_str, normalized_priority, 0),
        )
        return cur.lastrowid

    def get_tasks(self, done: int) -> List[Task]:
        if done not in (0, 1):
            raise ValidationError("Task status filter must be 0 or 1.")
        rows = self._execute_read("SELECT * FROM tasks WHERE done = ? ORDER BY id DESC", (done,))
        tasks: List[Task] = []
        for r in rows:
            tasks.append(
                Task(
                    id=r["id"],
                    title=r["title"],
                    description=r["description"] or "",
                    date=datetime.fromisoformat(r["date"]) if r["date"] else None,
                    completed_at=datetime.fromisoformat(r["completed_at"]) if r["completed_at"] else None,
                    priority=r["priority"] or "Medium",
                    done=bool(r["done"]),
                )
            )
        return tasks

    def mark_task_done(self, task_id: int) -> None:
        normalized_task_id = normalize_record_id(task_id, "Task")
        now_str = datetime.now().strftime(DATE_FORMAT)
        cur = self._execute_write(
            "UPDATE tasks SET done = 1, completed_at = COALESCE(completed_at, ?) WHERE id = ?",
            (now_str, normalized_task_id),
        )
        if cur.rowcount == 0 and not self._row_exists("tasks", normalized_task_id):
            raise RecordNotFoundError("Task not found.")

    # ---- money ----
    def insert_money_entry(self, entry_type: str, amount: float, note: str, person: str) -> int:
        normalized_type, normalized_amount, normalized_note, normalized_person = normalize_money_entry_input(
            entry_type,
            amount,
            note,
            person,
        )
        now_str = datetime.now().strftime(DATE_FORMAT)
        cur = self._execute_write(
            "INSERT INTO money_entries (entry_type, amount, date, note, person) "
            "VALUES (?, ?, ?, ?, ?)",
            (normalized_type, normalized_amount, now_str, normalized_note, normalized_person),
        )
        return cur.lastrowid

    def update_money_entry(self, entry_id: int, entry_type: str, amount: float, note: str, person: str) -> None:
        normalized_entry_id = normalize_record_id(entry_id, "Money entry")
        normalized_type, normalized_amount, normalized_note, normalized_person = normalize_money_entry_input(
            entry_type,
            amount,
            note,
            person,
        )
        cur = self._execute_write(
            """
            UPDATE money_entries
            SET entry_type = ?, amount = ?, note = ?, person = ?
            WHERE id = ?
            """,
            (
                normalized_type,
                normalized_amount,
                normalized_note,
                normalized_person,
                normalized_entry_id,
            ),
        )
        if cur.rowcount == 0 and not self._row_exists("money_entries", normalized_entry_id):
            raise RecordNotFoundError("Money entry not found.")

    def delete_money_entry(self, entry_id: int) -> None:
        normalized_entry_id = normalize_record_id(entry_id, "Money entry")
        cur = self._execute_write("DELETE FROM money_entries WHERE id = ?", (normalized_entry_id,))
        if cur.rowcount == 0:
            raise RecordNotFoundError("Money entry not found.")

    def _money_where_clause(
        self,
        year: int | None = None,
        month: int | None = None,
        entry_type: str | None = None,
    ) -> tuple[str, list]:
        normalized_year, normalized_month = normalize_period(year=year, month=month)
        conditions = []
        params = []

        if normalized_year is not None and normalized_month is not None:
            start = datetime(normalized_year, normalized_month, 1)
            if normalized_month == 12:
                end = datetime(normalized_year + 1, 1, 1)
            else:
                end = datetime(normalized_year, normalized_month + 1, 1)
            conditions.extend(["date >= ?", "date < ?"])
            params.extend(
                [
                    start.strftime(DATE_FORMAT),
                    end.strftime(DATE_FORMAT),
                ]
            )

        if entry_type:
            if entry_type not in MONEY_ENTRY_TYPES:
                raise ValidationError("Money entry type is invalid.")
            conditions.append("entry_type = ?")
            params.append(entry_type)

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        return where_clause, params

    def get_money_entries(
        self,
        year: int | None = None,
        month: int | None = None,
        entry_type: str | None = None,
    ) -> List[MoneyEntry]:
        where_clause, params = self._money_where_clause(year, month, entry_type)
        rows = self._execute_read(
            f"SELECT * FROM money_entries{where_clause} ORDER BY date DESC, id DESC",
            tuple(params),
        )
        entries: List[MoneyEntry] = []
        for r in rows:
            entries.append(
                MoneyEntry(
                    id=r["id"],
                    entry_type=r["entry_type"],
                    amount=r["amount"],
                    date=datetime.fromisoformat(r["date"]),
                    note=r["note"] or "",
                    person=r["person"] or "",
                )
            )
        return entries

    def get_money_summary(
        self,
        year: int | None = None,
        month: int | None = None,
    ) -> Tuple[float, float, float, float, float]:
        def sum_for(types):
            if not types:
                return 0.0
            entry_type_clause = ",".join("?" * len(types))
            where_clause, params = self._money_where_clause(year, month)
            connector = " AND " if where_clause else " WHERE "
            q = (
                "SELECT COALESCE(SUM(amount), 0) AS total "
                "FROM money_entries"
                f"{where_clause}{connector}entry_type IN ({entry_type_clause})"
            )
            try:
                row = self.conn.execute(q, [*params, *types]).fetchone()
            except sqlite3.Error as exc:
                raise AssistantDataError("Unable to read data from the local database.") from exc
            return row["total"] if row else 0.0

        salary = sum_for(["Income"])
        expenses = sum_for(["Expense", "EMI", "Credit"])
        emi = sum_for(["EMI"])
        credit = sum_for(["Credit"])
        owes_you = sum_for(["Given"])
        return salary, expenses, emi, credit, owes_you
