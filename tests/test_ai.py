import unittest
from datetime import datetime

from app.ai import get_chat_response, get_daily_suggestion
from app.models import Task


class FakeTaskManager:
    def __init__(self, tasks, completed_tasks=None):
        self.tasks = tasks
        self.completed_tasks = completed_tasks or []

    def list_pending_tasks(self):
        return self.tasks

    def list_completed_tasks(self):
        return self.completed_tasks


class FakeMoneyManager:
    def __init__(self, summary):
        self.summary = summary
        self.last_kwargs = None

    def compute_summary(self, year=None, month=None):
        self.last_kwargs = {"year": year, "month": month}
        return self.summary


class AiSuggestionTests(unittest.TestCase):
    def test_get_daily_suggestion_without_pending_tasks(self):
        fake_money = FakeMoneyManager({'net_balance': 1000, 'salary': 5000, 'expenses': 3000})
        suggestion = get_daily_suggestion(FakeTaskManager([]), fake_money)

        self.assertIn(
            "You have no pending tasks. This is a good day to rest or plan ahead.",
            suggestion,
        )

    def test_get_daily_suggestion_counts_high_priority_tasks(self):
        tasks = [
            Task(id=1, title="Deep work", priority="High"),
            Task(id=2, title="Inbox cleanup", priority="Low"),
            Task(id=3, title="Review PR", priority="High"),
        ]
        fake_money = FakeMoneyManager({'net_balance': 1000, 'salary': 5000, 'expenses': 3000})

        suggestion = get_daily_suggestion(FakeTaskManager(tasks), fake_money)

        self.assertIn("3 pending tasks", suggestion)
        self.assertIn("2 marked High priority", suggestion)

    def test_get_chat_response_prioritizes_top_task(self):
        tasks = [
            Task(id=1, title="Inbox cleanup", priority="Low"),
            Task(id=2, title="Deep work", priority="High"),
            Task(id=3, title="Review PR", priority="High"),
        ]
        money_manager = FakeMoneyManager(
            {
                "salary": 0,
                "expenses": 0,
                "emi": 0,
                "credit": 0,
                "owes_you": 0,
                "net_balance": 0,
            }
        )

        response = get_chat_response(
            "What should I focus on first today?",
            FakeTaskManager(tasks),
            money_manager,
            reference_date=datetime(2026, 4, 1),
        )

        self.assertIn("Start with 'Deep work' first.", response)
        self.assertIn("3 pending tasks", response)

    def test_get_chat_response_reports_money_summary_for_reference_month(self):
        money_manager = FakeMoneyManager(
            {
                "salary": 45000,
                "expenses": 12200,
                "emi": 7800,
                "credit": 1200,
                "owes_you": 900,
                "net_balance": 32800,
            }
        )

        response = get_chat_response(
            "How is my money looking this month?",
            FakeTaskManager([]),
            money_manager,
            reference_date=datetime(2026, 4, 1),
        )

        self.assertIn("April 2026", response)
        self.assertIn("Rs 45,000", response)
        self.assertIn("Rs 32,800", response)
        self.assertEqual(money_manager.last_kwargs, {"year": 2026, "month": 4})

    def test_get_chat_response_for_blank_message_explains_capabilities(self):
        money_manager = FakeMoneyManager(
            {
                "salary": 30000,
                "expenses": 2500,
                "emi": 0,
                "credit": 0,
                "owes_you": 0,
                "net_balance": 27500,
            }
        )

        response = get_chat_response(
            "",
            FakeTaskManager([Task(id=1, title="Finish report", priority="High")]),
            money_manager,
            reference_date=datetime(2026, 4, 1),
        )

        self.assertIn("prioritize tasks", response)
        self.assertIn("1 pending tasks", response)
        self.assertIn("Rs 27,500", response)
