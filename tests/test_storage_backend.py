from app.backend import MoneyManager, TaskManager
from tests.test_support import IsolatedDatabaseTestCase


class SQLiteStorageTests(IsolatedDatabaseTestCase):
    def test_init_creates_expected_tables(self):
        rows = self.storage.conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()

        self.assertEqual([row["name"] for row in rows], ["money_entries", "tasks"])

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

    def test_money_manager_returns_expected_summary_dict(self):
        manager = MoneyManager()
        manager.add_entry("Income", 30000, "Monthly salary", "")
        manager.add_entry("Expense", 2500, "Utilities", "")
        manager.add_entry("Given", 1000, "Lunch split", "Ari")

        summary = manager.compute_summary()

        self.assertEqual(
            summary,
            {
                "salary": 30000,
                "expenses": 2500,
                "emi": 0,
                "credit": 0,
                "owes_you": 1000,
            },
        )
