import sqlite3
from datetime import datetime

import app.backend as backend_module
from app.sqlite_storage import SQLiteStorage
from app.backend import MoneyManager, TaskManager
from app.errors import RecordNotFoundError, ValidationError
from tests.test_support import IsolatedDatabaseTestCase


class SQLiteStorageTests(IsolatedDatabaseTestCase):
    def test_init_creates_expected_tables(self):
        rows = self.storage.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()

        self.assertEqual(
            [row["name"] for row in rows],
            [
                "money_counterparties",
                "money_entries",
                "money_entry_facts",
                "money_entry_kinds",
                "task_active",
                "task_completed",
                "task_core",
                "task_events",
            ],
        )

        view_rows = self.storage.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'view' ORDER BY name"
        ).fetchall()
        self.assertEqual(
            [row["name"] for row in view_rows],
            [
                "money_analysis_view",
                "money_monthly_breakdown_view",
                "task_analysis_view",
                "task_daily_stats_view",
            ],
        )

    def test_task_round_trip_and_completion(self):
        task_id = self.storage.insert_task("Pay rent", "Before 5pm", "High")

        pending_tasks = self.storage.get_tasks(done=0)
        self.assertEqual(len(pending_tasks), 1)
        self.assertEqual(pending_tasks[0].id, task_id)
        self.assertEqual(pending_tasks[0].title, "Pay rent")
        self.assertEqual(pending_tasks[0].description, "Before 5pm")
        self.assertEqual(pending_tasks[0].priority, "High")
        self.assertFalse(pending_tasks[0].done)
        self.assertIsNotNone(pending_tasks[0].date)

        self.storage.mark_task_done(task_id)

        self.assertEqual(self.storage.get_tasks(done=0), [])
        completed_tasks = self.storage.get_tasks(done=1)
        self.assertEqual(len(completed_tasks), 1)
        self.assertTrue(completed_tasks[0].done)
        self.assertIsNotNone(completed_tasks[0].completed_at)

        active_row = self.storage.conn.execute(
            "SELECT 1 FROM task_active WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        self.assertIsNone(active_row)

        completed_row = self.storage.conn.execute(
            "SELECT priority, completed_at FROM task_completed WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        self.assertEqual(completed_row["priority"], "High")
        self.assertIsNotNone(completed_row["completed_at"])

    def test_task_analysis_tables_store_lifecycle_data(self):
        task_id = self.storage.insert_task("Pay rent", "Before 5pm", "High")

        analysis_row = self.storage.conn.execute(
            """
            SELECT lifecycle_stage, priority, title_clean, description_clean
            FROM task_analysis_view
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()
        self.assertEqual(analysis_row["lifecycle_stage"], "active")
        self.assertEqual(analysis_row["priority"], "High")
        self.assertEqual(analysis_row["title_clean"], "Pay rent")
        self.assertEqual(analysis_row["description_clean"], "Before 5pm")

        event_rows = self.storage.conn.execute(
            "SELECT event_type, to_state FROM task_events WHERE task_id = ? ORDER BY id",
            (task_id,),
        ).fetchall()
        self.assertEqual(
            [(row["event_type"], row["to_state"]) for row in event_rows],
            [("created", "pending")],
        )

    def test_legacy_tasks_table_is_migrated_into_lifecycle_tables(self):
        self.storage.conn.close()

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL CHECK (length(trim(title)) > 0),
                description TEXT NOT NULL DEFAULT '',
                date TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'Medium'
                    CHECK (priority IN ('Low', 'Medium', 'High')),
                done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1)),
                completed_at TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO tasks (id, title, description, date, priority, done, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (1, "Deep work", "Focus block", "2026-04-08T09:00:00", "High", 0, None),
        )
        conn.execute(
            """
            INSERT INTO tasks (id, title, description, date, priority, done, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (2, "Pay rent", "Before 5pm", "2026-04-07T18:00:00", "Medium", 1, "2026-04-08T07:30:00"),
        )
        conn.commit()
        conn.close()

        self.storage = SQLiteStorage()
        backend_module.storage = self.storage

        pending_tasks = self.storage.get_tasks(done=0)
        completed_tasks = self.storage.get_tasks(done=1)

        self.assertEqual([task.title for task in pending_tasks], ["Deep work"])
        self.assertEqual([task.title for task in completed_tasks], ["Pay rent"])

        legacy_tables = self.storage.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'tasks_legacy'"
        ).fetchall()
        self.assertEqual(len(legacy_tables), 1)

        migrated_events = self.storage.conn.execute(
            "SELECT event_type FROM task_events WHERE task_id = 2 ORDER BY id"
        ).fetchall()
        self.assertEqual(
            [row["event_type"] for row in migrated_events],
            ["created", "completed"],
        )

    def test_task_validation_rejects_blank_title_and_unknown_task(self):
        with self.assertRaisesRegex(ValidationError, "Task title cannot be empty"):
            self.storage.insert_task("   ", "Before 5pm", "High")

        with self.assertRaisesRegex(RecordNotFoundError, "Task not found"):
            self.storage.mark_task_done(999)

    def test_money_summary_groups_entries_correctly(self):
        self.storage.insert_money_entry("Income", 50000, "Salary", "")
        self.storage.insert_money_entry("Expense", 1200, "Groceries", "")
        self.storage.insert_money_entry("EMI", 7000, "Bike EMI", "")
        self.storage.insert_money_entry("Credit", 2500, "Card bill", "")
        self.storage.insert_money_entry("Given", 1800, "Loan to Sam", "Sam")
        self.storage.insert_money_entry("Taken", 900, "Borrowed from Lee", "Lee")

        entries = self.storage.get_money_entries()
        self.assertEqual(len(entries), 6)
        self.assertCountEqual(
            [entry.entry_type for entry in entries],
            ["Income", "Expense", "EMI", "Credit", "Given", "Taken"],
        )

        salary, expenses, emi, credit, owes_you = self.storage.get_money_summary()
        self.assertEqual(salary, 50000)
        self.assertEqual(expenses, 10700)
        self.assertEqual(emi, 7000)
        self.assertEqual(credit, 2500)
        self.assertEqual(owes_you, 1800)

    def test_money_entries_can_be_filtered_updated_and_deleted(self):
        income_id = self.storage.insert_money_entry("Income", 50000, "Salary", "")
        expense_id = self.storage.insert_money_entry("Expense", 1200, "Groceries", "")

        previous_month = datetime(2026, 3, 20, 10, 0, 0).isoformat(timespec="seconds")
        self.storage.conn.execute(
            "UPDATE money_entries SET date = ? WHERE id = ?",
            (previous_month, income_id),
        )
        self.storage.conn.commit()

        current_month_expenses = self.storage.get_money_entries(year=2026, month=4, entry_type="Expense")
        self.assertEqual(len(current_month_expenses), 1)
        self.assertEqual(current_month_expenses[0].id, expense_id)

        self.storage.update_money_entry(expense_id, "Expense", 1500, "Groceries and fuel", "")
        updated_expense = self.storage.get_money_entries(year=2026, month=4, entry_type="Expense")[0]
        self.assertEqual(updated_expense.amount, 1500)
        self.assertEqual(updated_expense.note, "Groceries and fuel")

        self.storage.delete_money_entry(expense_id)
        self.assertEqual(self.storage.get_money_entries(year=2026, month=4), [])

    def test_money_analysis_tables_store_ai_friendly_money_facts(self):
        entry_id = self.storage.insert_money_entry("Given", 1800, "Loan to Sam", "Sam")

        fact_row = self.storage.conn.execute(
            """
            SELECT
                kind_key,
                flow_direction,
                analysis_group,
                amount_minor,
                signed_amount_minor,
                currency_code,
                counterparty_name,
                counterparty_kind,
                month_key
            FROM money_entry_facts
            WHERE entry_id = ?
            """,
            (entry_id,),
        ).fetchone()

        self.assertEqual(fact_row["kind_key"], "Given")
        self.assertEqual(fact_row["flow_direction"], "outflow")
        self.assertEqual(fact_row["analysis_group"], "loan")
        self.assertEqual(fact_row["amount_minor"], 180000)
        self.assertEqual(fact_row["signed_amount_minor"], -180000)
        self.assertEqual(fact_row["currency_code"], "INR")
        self.assertEqual(fact_row["counterparty_name"], "Sam")
        self.assertEqual(fact_row["counterparty_kind"], "person")
        self.assertRegex(fact_row["month_key"], r"^\d{4}-\d{2}$")

        analysis_row = self.storage.conn.execute(
            """
            SELECT counts_as_receivable, counts_as_expense, counts_as_income
            FROM money_analysis_view
            WHERE entry_id = ?
            """,
            (entry_id,),
        ).fetchone()
        self.assertEqual(analysis_row["counts_as_receivable"], 1)
        self.assertEqual(analysis_row["counts_as_expense"], 0)
        self.assertEqual(analysis_row["counts_as_income"], 0)

    def test_money_analysis_rows_stay_synced_when_money_entries_change(self):
        entry_id = self.storage.insert_money_entry("Expense", 1200, "Groceries", "")
        self.storage.conn.execute(
            """
            UPDATE money_entries
            SET entry_type = ?, amount = ?, note = ?, person = ?, date = ?
            WHERE id = ?
            """,
            ("Taken", 900, "Borrowed from Lee", "Lee", datetime(2026, 3, 18, 18, 0, 0).isoformat(timespec="seconds"), entry_id),
        )
        self.storage.conn.commit()

        fact_row = self.storage.conn.execute(
            """
            SELECT
                kind_key,
                flow_direction,
                analysis_group,
                amount_minor,
                signed_amount_minor,
                counterparty_name,
                counterparty_kind,
                month_key
            FROM money_entry_facts
            WHERE entry_id = ?
            """,
            (entry_id,),
        ).fetchone()

        self.assertEqual(fact_row["kind_key"], "Taken")
        self.assertEqual(fact_row["flow_direction"], "inflow")
        self.assertEqual(fact_row["analysis_group"], "loan")
        self.assertEqual(fact_row["amount_minor"], 90000)
        self.assertEqual(fact_row["signed_amount_minor"], 90000)
        self.assertEqual(fact_row["counterparty_name"], "Lee")
        self.assertEqual(fact_row["counterparty_kind"], "person")
        self.assertEqual(fact_row["month_key"], "2026-03")

    def test_money_entry_validation_rejects_bad_payloads(self):
        with self.assertRaisesRegex(ValidationError, "Amount must be greater than zero"):
            self.storage.insert_money_entry("Expense", 0, "Groceries", "")

        with self.assertRaisesRegex(ValidationError, "Money entry type is invalid"):
            self.storage.insert_money_entry("Bonus", 5000, "Unexpected", "")

        with self.assertRaisesRegex(ValidationError, "Person is required"):
            self.storage.insert_money_entry("Given", 1200, "Loan", "")

    def test_money_entry_update_and_delete_require_existing_rows(self):
        with self.assertRaisesRegex(RecordNotFoundError, "Money entry not found"):
            self.storage.update_money_entry(999, "Expense", 1500, "Groceries", "")

        with self.assertRaisesRegex(RecordNotFoundError, "Money entry not found"):
            self.storage.delete_money_entry(999)

    def test_money_summary_can_be_limited_to_a_month(self):
        april_income_id = self.storage.insert_money_entry("Income", 50000, "April salary", "")
        march_expense_id = self.storage.insert_money_entry("Expense", 2000, "Old expense", "")

        self.storage.conn.execute(
            "UPDATE money_entries SET date = ? WHERE id = ?",
            (datetime(2026, 4, 12, 9, 0, 0).isoformat(timespec="seconds"), april_income_id),
        )
        self.storage.conn.execute(
            "UPDATE money_entries SET date = ? WHERE id = ?",
            (datetime(2026, 3, 18, 18, 0, 0).isoformat(timespec="seconds"), march_expense_id),
        )
        self.storage.conn.commit()

        april_summary = self.storage.get_money_summary(year=2026, month=4)
        march_summary = self.storage.get_money_summary(year=2026, month=3)

        self.assertEqual(april_summary, (50000, 0, 0, 0, 0))
        self.assertEqual(march_summary, (0, 2000, 0, 0, 0))


class ManagerTests(IsolatedDatabaseTestCase):
    def test_task_manager_adds_lists_and_marks_done(self):
        manager = TaskManager()

        task = manager.add_task("Finish report", "Share draft", "Medium")
        pending_tasks = manager.list_pending_tasks()

        self.assertEqual(task.title, "Finish report")
        self.assertEqual(len(pending_tasks), 1)
        self.assertEqual(pending_tasks[0].id, task.id)
        self.assertFalse(pending_tasks[0].done)

        manager.mark_done(task.id)

        self.assertEqual(len(manager.list_pending_tasks()), 0)
        completed_tasks = manager.list_completed_tasks()
        self.assertEqual(len(completed_tasks), 1)
        self.assertTrue(completed_tasks[0].done)

    def test_task_manager_rejects_invalid_priority(self):
        manager = TaskManager()

        with self.assertRaisesRegex(ValidationError, "Task priority must be Low, Medium, or High"):
            manager.add_task("Finish report", "Share draft", "Urgent")

    def test_task_manager_rejects_duplicate_pending_task(self):
        manager = TaskManager()
        manager.add_task("Finish report", "Share draft", "Medium")

        with self.assertRaisesRegex(ValidationError, "already in your pending list"):
            manager.add_task("Finish report", "Share draft", "Medium")

        self.assertEqual(len(manager.list_pending_tasks()), 1)

    def test_task_manager_allows_readding_completed_task(self):
        manager = TaskManager()
        task = manager.add_task("Finish report", "Share draft", "Medium")
        manager.mark_done(task.id)

        recreated_task = manager.add_task("Finish report", "Share draft", "Medium")

        self.assertEqual(recreated_task.title, "Finish report")
        self.assertEqual(len(manager.list_pending_tasks()), 1)
        self.assertEqual(len(manager.list_completed_tasks()), 1)

    def test_money_manager_returns_expected_summary_dict(self):
        manager = MoneyManager()
        manager.add_entry("Income", 30000, "Monthly salary", "")
        manager.add_entry("Expense", 2500, "Utilities", "")
        manager.add_entry("Given", 1000, "Lunch split", "Ari")

        summary = manager.compute_summary()

        self.assertEqual(
            summary,
            {
                "net_balance": 27500,
                "salary": 30000,
                "expenses": 2500,
                "emi": 0,
                "credit": 0,
                "owes_you": 1000,
            },
        )

    def test_money_manager_requires_complete_period_filters(self):
        manager = MoneyManager()

        with self.assertRaisesRegex(ValidationError, "Year and month must be provided together"):
            manager.list_entries(year=2026)

        with self.assertRaisesRegex(ValidationError, "Year and month must be provided together"):
            manager.compute_summary(month=4)
