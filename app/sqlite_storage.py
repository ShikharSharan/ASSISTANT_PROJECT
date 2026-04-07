import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
from .storage_base import StorageBase
from .models import Task, MoneyEntry
from config import DB_PATH

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

class SQLiteStorage(StorageBase):
    def __init__(self):
        self.db_path = Path(DB_PATH)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                date TEXT,
                priority TEXT,
                done INTEGER DEFAULT 0
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS money_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_type TEXT,
                amount REAL,
                date TEXT,
                note TEXT,
                person TEXT
            );
            """
        )
        self.conn.commit()

    # ---- tasks ----
    def insert_task(self, title: str, description: str, priority: str) -> int:
        now_str = datetime.now().strftime(DATE_FORMAT)
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO tasks (title, description, date, priority, done) VALUES (?, ?, ?, ?, ?)",
            (title, description, now_str, priority, 0),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_tasks(self, done: int) -> List[Task]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE done = ? ORDER BY id DESC", (done,))
        rows = cur.fetchall()
        tasks: List[Task] = []
        for r in rows:
            tasks.append(
                Task(
                    id=r["id"],
                    title=r["title"],
                    description=r["description"] or "",
                    date=datetime.fromisoformat(r["date"]) if r["date"] else None,
                    priority=r["priority"] or "Medium",
                    done=bool(r["done"]),
                )
            )
        return tasks

    def mark_task_done(self, task_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
        self.conn.commit()

    # ---- money ----
    def insert_money_entry(self, entry_type: str, amount: float, note: str, person: str) -> int:
        now_str = datetime.now().strftime(DATE_FORMAT)
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO money_entries (entry_type, amount, date, note, person) "
            "VALUES (?, ?, ?, ?, ?)",
            (entry_type, amount, now_str, note, person),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_money_entries(self) -> List[MoneyEntry]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM money_entries ORDER BY date DESC")
        rows = cur.fetchall()
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

    def get_money_summary(self) -> Tuple[float, float, float, float, float]:
        cur = self.conn.cursor()

        def sum_for(types):
            if not types:
                return 0.0
            q = (
                "SELECT COALESCE(SUM(amount), 0) AS total "
                "FROM money_entries WHERE entry_type IN (%s)"
                % ",".join("?" * len(types))
            )
            cur.execute(q, types)
            row = cur.fetchone()
            return row["total"] if row else 0.0

        salary = sum_for(["Income"])
        expenses = sum_for(["Expense", "EMI", "Credit"])
        emi = sum_for(["EMI"])
        credit = sum_for(["Credit"])
        owes_you = sum_for(["Given"])
        return salary, expenses, emi, credit, owes_you