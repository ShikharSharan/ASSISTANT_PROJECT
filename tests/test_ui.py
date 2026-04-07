import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from app.ui import MainWindow
from tests.test_support import IsolatedDatabaseTestCase


class TaskUiTests(IsolatedDatabaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        super().setUp()
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()
        self.app.processEvents()
        super().tearDown()

    def test_view_selected_task_button_opens_details_page(self):
        self.window.task_manager.add_task("Submit taxes", "Upload forms", "High")
        self.window.home_page.refresh_lists()

        first_item = self.window.home_page.pending_list.item(0)
        self.window.home_page.pending_list.setCurrentItem(first_item)
        self.window.home_page.view_task_btn.click()
        self.app.processEvents()

        self.assertIs(self.window.stack.currentWidget(), self.window.task_details_page)
        self.assertEqual(self.window.task_details_page.title_value.text(), "Submit taxes")
        self.assertEqual(self.window.task_details_page.priority_value.text(), "High")
        self.assertEqual(
            self.window.task_details_page.description_text.toPlainText(),
            "Upload forms",
        )

    def test_view_selected_task_without_selection_shows_message(self):
        with patch("app.ui.QMessageBox.information") as info_mock:
            self.window.home_page.view_task_btn.click()

        info_mock.assert_called_once()
        self.assertIs(self.window.stack.currentWidget(), self.window.home_page)

    def test_mark_done_from_details_page_returns_home_and_updates_lists(self):
        self.window.task_manager.add_task("Book dentist", "Call clinic", "Medium")
        self.window.home_page.refresh_lists()

        first_item = self.window.home_page.pending_list.item(0)
        self.window.home_page.pending_list.setCurrentItem(first_item)
        self.window.home_page.view_selected_task()
        self.window.task_details_page.mark_done_btn.click()
        self.app.processEvents()

        self.assertIs(self.window.stack.currentWidget(), self.window.home_page)
        self.assertEqual(self.window.home_page.pending_list.count(), 0)
        self.assertEqual(len(self.window.task_manager.list_completed_tasks()), 1)

    def test_home_page_stat_cards_show_task_counts(self):
        self.window.task_manager.add_task("Deep work", "Focus block", "High")
        self.window.task_manager.add_task("Pay bills", "Before 6pm", "Medium")
        latest_task = self.window.task_manager.add_task("Plan week", "Outline goals", "High")
        self.window.task_manager.mark_done(latest_task.id)
        self.window.home_page.refresh_lists()

        self.assertEqual(self.window.home_page.stat_values["pending"].text(), "2")
        self.assertEqual(self.window.home_page.stat_values["completed"].text(), "1")
        self.assertEqual(self.window.home_page.stat_values["high_priority"].text(), "1")
        self.assertEqual(self.window.home_page.stat_values["focus_hours"].text(), "~2h")

    def test_money_page_stat_cards_show_grouped_amounts(self):
        self.window.money_manager.add_entry("Income", 45000, "Salary", "")
        self.window.money_manager.add_entry("Expense", 3200, "Groceries", "")
        self.window.money_manager.add_entry("EMI", 7800, "Bike EMI", "")
        self.window.money_manager.add_entry("Credit", 1200, "Card payment", "")
        self.window.money_manager.add_entry("Given", 900, "Split dinner", "Kai")
        self.window.money_page.refresh_summary()

        self.assertEqual(self.window.money_page.stat_values["salary"].text(), "₹45,000")
        self.assertEqual(self.window.money_page.stat_values["expenses"].text(), "₹12,200")
        self.assertEqual(self.window.money_page.stat_values["emi"].text(), "₹7,800")
        self.assertEqual(self.window.money_page.stat_values["credit"].text(), "₹1,200")
        self.assertEqual(self.window.money_page.stat_values["owes_you"].text(), "₹900")
