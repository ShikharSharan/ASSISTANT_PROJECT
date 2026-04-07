import unittest

from app.ai import get_daily_suggestion
from app.models import Task


class FakeTaskManager:
    def __init__(self, tasks):
        self.tasks = tasks

    def list_pending_tasks(self):
        return self.tasks


class AiSuggestionTests(unittest.TestCase):
    def test_get_daily_suggestion_without_pending_tasks(self):
        suggestion = get_daily_suggestion(FakeTaskManager([]))

        self.assertEqual(
            suggestion,
            "You have no pending tasks. This is a good day to rest or plan ahead.",
        )

    def test_get_daily_suggestion_counts_high_priority_tasks(self):
        tasks = [
            Task(id=1, title="Deep work", priority="High"),
            Task(id=2, title="Inbox cleanup", priority="Low"),
            Task(id=3, title="Review PR", priority="High"),
        ]

        suggestion = get_daily_suggestion(FakeTaskManager(tasks))

        self.assertIn("3 pending tasks", suggestion)
        self.assertIn("2 marked High priority", suggestion)
