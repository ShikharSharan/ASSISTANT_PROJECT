import os
import unittest
from datetime import datetime
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QMessageBox

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
        self.window.tasks_page.refresh_lists()

        first_item = self.window.tasks_page.pending_list.item(0)
        self.window.tasks_page.pending_list.setCurrentItem(first_item)
        self.window.tasks_page.view_task_btn.click()
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
            self.window.tasks_page.view_task_btn.click()

        info_mock.assert_called_once()
        self.assertIs(self.window.stack.currentWidget(), self.window.home_page)

    def test_mark_done_from_details_page_returns_tasks_page_and_updates_lists(self):
        self.window.task_manager.add_task("Book dentist", "Call clinic", "Medium")
        self.window.tasks_page.refresh_lists()

        first_item = self.window.tasks_page.pending_list.item(0)
        self.window.tasks_page.pending_list.setCurrentItem(first_item)
        self.window.tasks_page.view_selected_task()
        self.window.task_details_page.mark_done_btn.click()
        self.app.processEvents()

        self.assertIs(self.window.stack.currentWidget(), self.window.tasks_page)
        self.assertEqual(self.window.tasks_page.pending_list.count(), 0)
        self.assertEqual(self.window.home_page.stat_values["pending"].text(), "0")
        self.assertEqual(len(self.window.task_manager.list_completed_tasks()), 1)

    def test_add_task_page_rejects_duplicate_pending_task(self):
        self.window.task_manager.add_task("Submit taxes", "Upload forms", "High")
        self.window.show_add_task_page(return_page=self.window.tasks_page)

        self.window.add_task_page.title_edit.setText("Submit taxes")
        self.window.add_task_page.details_edit.setPlainText("Upload forms")
        self.window.add_task_page.priority_combo.setCurrentText("High")

        with patch("app.ui.QMessageBox.warning") as warning_mock:
            self.window.add_task_page.save_btn.click()
        self.app.processEvents()

        warning_mock.assert_called_once()
        self.assertIn("already in your pending list", warning_mock.call_args.args[2])
        self.assertEqual(len(self.window.task_manager.list_pending_tasks()), 1)
        self.assertIs(self.window.stack.currentWidget(), self.window.add_task_page)
        self.assertTrue(self.window.add_task_page.save_btn.isEnabled())

    def test_home_page_stat_cards_show_task_counts(self):
        self.window.task_manager.add_task("Deep work", "Focus block", "High")
        self.window.task_manager.add_task("Pay bills", "Before 6pm", "Medium")
        latest_task = self.window.task_manager.add_task("Plan week", "Outline goals", "High")
        self.window.task_manager.mark_done(latest_task.id)
        self.window.home_page.refresh_lists()

        self.assertEqual(self.window.home_page.stat_values["pending"].text(), "2")
        self.assertEqual(self.window.home_page.stat_values["done_today"].text(), "1")
        self.assertEqual(self.window.home_page.stat_values["high_priority"].text(), "1")
        self.assertEqual(self.window.home_page.stat_values["focus_hours"].text(), "~2h")

    def test_money_page_stat_cards_show_grouped_amounts(self):
        self.window.money_manager.add_entry("Income", 45000, "Salary", "")
        self.window.money_manager.add_entry("Expense", 3200, "Groceries", "")
        self.window.money_manager.add_entry("EMI", 7800, "Bike EMI", "")
        self.window.money_manager.add_entry("Credit", 1200, "Card payment", "")
        self.window.money_manager.add_entry("Given", 900, "Split dinner", "Kai")
        self.window.money_page.refresh_summary()

        self.assertEqual(self.window.money_page.stat_values["net_balance"].text(), "₹32,800")
        self.assertEqual(self.window.money_page.stat_values["salary"].text(), "₹45,000")
        self.assertEqual(self.window.money_page.stat_values["expenses"].text(), "₹12,200")
        self.assertEqual(self.window.money_page.stat_values["emi"].text(), "₹7,800")
        self.assertEqual(self.window.money_page.stat_values["credit"].text(), "₹1,200")
        self.assertEqual(self.window.money_page.stat_values["owes_you"].text(), "₹900")

    def test_money_page_month_navigation_filters_summary(self):
        april_income = self.window.money_manager.add_entry("Income", 45000, "April salary", "")
        march_expense = self.window.money_manager.add_entry("Expense", 1800, "March groceries", "")
        self.storage.conn.execute(
            "UPDATE money_entries SET date = ? WHERE id = ?",
            (datetime(2026, 3, 15, 9, 0, 0).isoformat(timespec="seconds"), march_expense.id),
        )
        self.storage.conn.execute(
            "UPDATE money_entries SET date = ? WHERE id = ?",
            (datetime(2026, 4, 10, 9, 0, 0).isoformat(timespec="seconds"), april_income.id),
        )
        self.storage.conn.commit()

        self.window.money_page.selected_month = datetime(2026, 4, 1)
        self.window.money_page.refresh_month_header()
        self.window.money_page.refresh_summary()
        self.assertEqual(self.window.money_page.stat_values["net_balance"].text(), "₹45,000")

        self.window.money_page.change_month(-1)
        self.assertEqual(self.window.money_page.month_label.text(), "March 2026")
        self.assertEqual(self.window.money_page.stat_values["expenses"].text(), "₹1,800")
        self.assertEqual(self.window.money_page.stat_values["net_balance"].text(), "-₹1,800")

    def test_money_page_filter_buttons_reduce_visible_entries(self):
        self.window.money_manager.add_entry("Income", 45000, "Salary", "")
        self.window.money_manager.add_entry("Expense", 3200, "Groceries", "")
        self.window.money_page.set_entry_filter("Expense")

        self.assertEqual(self.window.money_page.entries_list.count(), 1)
        first_item = self.window.money_page.entries_list.item(0)
        row_widget = self.window.money_page.entries_list.itemWidget(first_item)
        self.assertEqual(row_widget.title_label.text(), "Groceries")

    def test_money_page_edit_and_delete_actions_work(self):
        self.window.money_manager.add_entry("Expense", 3200, "Groceries", "")
        self.window.money_page.refresh_entries()

        first_item = self.window.money_page.entries_list.item(0)
        row_widget = self.window.money_page.entries_list.itemWidget(first_item)
        row_widget.edit_btn.click()
        self.app.processEvents()

        self.window.money_page.note_edit.setText("Groceries and snacks")
        self.window.money_page.amount_spin.setValue(3600)
        self.window.money_page.save_entry_btn.click()
        self.app.processEvents()

        updated_item = self.window.money_page.entries_list.item(0)
        updated_row_widget = self.window.money_page.entries_list.itemWidget(updated_item)
        self.assertEqual(updated_row_widget.title_label.text(), "Groceries and snacks")
        self.assertEqual(updated_row_widget.amount_label.text(), "-₹3,600")

        with patch("app.ui.QMessageBox.question", return_value=QMessageBox.StandardButton.Yes):
            updated_row_widget.delete_btn.click()
        self.app.processEvents()

        self.assertEqual(self.window.money_page.entries_list.count(), 0)
        self.assertEqual(self.window.money_page.empty_state_title.text(), "No entries for this month")

    def test_money_page_entry_buttons_stay_inside_card(self):
        self.window.resize(1200, 800)
        self.window.money_manager.add_entry("Expense", 3200, "Groceries and household stuff", "")
        self.window.show_money_page()
        self.window.money_page.refresh_entries()
        self.window.show()
        self.app.processEvents()

        first_item = self.window.money_page.entries_list.item(0)
        row_widget = self.window.money_page.entries_list.itemWidget(first_item)

        self.assertGreaterEqual(first_item.sizeHint().height(), row_widget.sizeHint().height())
        self.assertLessEqual(row_widget.edit_btn.geometry().bottom(), row_widget.rect().bottom())
        self.assertLessEqual(row_widget.delete_btn.geometry().bottom(), row_widget.rect().bottom())

    def test_money_page_add_form_uses_two_column_layout(self):
        self.window.resize(1200, 800)
        self.window.show_money_page()
        self.window.show()
        self.app.processEvents()

        type_top = self.window.money_page.type_combo.geometry().top()
        amount_top = self.window.money_page.amount_spin.geometry().top()
        note_top = self.window.money_page.note_edit.geometry().top()
        person_top = self.window.money_page.person_edit.geometry().top()

        self.assertLess(abs(type_top - amount_top), 12)
        self.assertLess(abs(note_top - person_top), 12)
        self.assertGreater(note_top, type_top)

    def test_home_ai_chat_button_opens_chat_page(self):
        self.window.task_manager.add_task("Deep work", "Focus block", "High")
        self.window.home_page.refresh_lists()

        self.window.home_page.ai_chat_btn.click()
        self.app.processEvents()

        self.assertIs(self.window.stack.currentWidget(), self.window.ai_chat_page)
        self.assertEqual(self.window.ai_chat_page.stat_values["pending"].text(), "1")
        self.assertIn("Deep work", self.window.ai_chat_page.chat_history.toPlainText())

    def test_ai_chat_page_sends_message_and_receives_reply(self):
        self.window.task_manager.add_task("Deep work", "Focus block", "High")
        self.window.show_ai_chat_page()

        self.window.ai_chat_page.prompt_edit.setText("What should I focus on first today?")
        self.window.ai_chat_page.send_btn.click()
        self.app.processEvents()

        transcript = self.window.ai_chat_page.chat_history.toPlainText()
        self.assertIn("What should I focus on first today?", transcript)
        self.assertIn("Start with 'Deep work' first.", transcript)

    def test_money_page_ai_chat_uses_selected_month_context(self):
        april_income = self.window.money_manager.add_entry("Income", 45000, "April salary", "")
        march_expense = self.window.money_manager.add_entry("Expense", 1800, "March groceries", "")
        self.storage.conn.execute(
            "UPDATE money_entries SET date = ? WHERE id = ?",
            (datetime(2026, 3, 15, 9, 0, 0).isoformat(timespec="seconds"), march_expense.id),
        )
        self.storage.conn.execute(
            "UPDATE money_entries SET date = ? WHERE id = ?",
            (datetime(2026, 4, 10, 9, 0, 0).isoformat(timespec="seconds"), april_income.id),
        )
        self.storage.conn.commit()

        self.window.money_page.selected_month = datetime(2026, 3, 1)
        self.window.money_page.refresh_month_header()
        self.window.money_page.ai_chat_btn.click()
        self.app.processEvents()

        self.window.ai_chat_page.prompt_edit.setText("How is my money looking this month?")
        self.window.ai_chat_page.send_btn.click()
        self.app.processEvents()

        transcript = self.window.ai_chat_page.chat_history.toPlainText()
        self.assertIn("March 2026", transcript)
        self.assertIn("-Rs 1,800", transcript)

    def test_home_focus_prefers_high_priority_task(self):
        self.window.task_manager.add_task("Medium task", "Routine work", "Medium")
        self.window.task_manager.add_task("High task", "Start here", "High")
        self.window.home_page.refresh_lists()

        self.assertEqual(self.window.home_page.focus_title_label.text(), "High task")
        self.assertIn("High priority", self.window.home_page.focus_meta_label.text())

    def test_home_open_tasks_button_shows_dedicated_tasks_page(self):
        self.window.home_page.open_tasks_btn.click()
        self.app.processEvents()

        self.assertIs(self.window.stack.currentWidget(), self.window.tasks_page)

    def test_home_focus_task_details_back_returns_to_home(self):
        self.window.task_manager.add_task("High task", "Critical", "High")
        self.window.home_page.refresh_lists()

        self.window.home_page.focus_open_btn.click()
        self.app.processEvents()
        self.window.task_details_page.back_btn.click()
        self.app.processEvents()

        self.assertIs(self.window.stack.currentWidget(), self.window.home_page)

    def test_tasks_page_filter_buttons_reduce_visible_tasks(self):
        self.window.task_manager.add_task("High task", "Critical", "High")
        self.window.task_manager.add_task("Low task", "Later", "Low")
        self.window.tasks_page.set_active_filter("High")

        self.assertEqual(self.window.tasks_page.pending_list.count(), 1)
        first_item = self.window.tasks_page.pending_list.item(0)
        row_widget = self.window.tasks_page.pending_list.itemWidget(first_item)
        self.assertEqual(row_widget.title_label.text(), "High task")

    def test_tasks_page_empty_state_appears_when_filter_has_no_match(self):
        self.window.task_manager.add_task("Low task", "Later", "Low")
        self.window.tasks_page.set_active_filter("High")

        self.assertEqual(self.window.tasks_page.pending_list.count(), 0)
        self.assertEqual(self.window.tasks_page.empty_state_title.text(), "No tasks match this filter")
        self.assertEqual(self.window.tasks_page.empty_state_action_btn.text(), "Show all tasks")

    def test_tasks_page_task_row_done_button_marks_task_complete(self):
        self.window.task_manager.add_task("Stretch break", "Quick win", "Low")
        self.window.tasks_page.refresh_lists()

        first_item = self.window.tasks_page.pending_list.item(0)
        row_widget = self.window.tasks_page.pending_list.itemWidget(first_item)
        row_widget.done_btn.click()
        self.app.processEvents()

        self.assertEqual(self.window.tasks_page.pending_list.count(), 0)
        self.assertEqual(self.window.home_page.stat_values["done_today"].text(), "1")

    def test_tasks_page_task_row_buttons_stay_inside_card_for_wrapped_content(self):
        self.window.resize(1200, 800)
        self.window.task_manager.add_task(
            "need to study half hours need to study half hours need to study half hours",
            "study coding " * 20,
            "Medium",
        )
        self.window.tasks_page.refresh_lists()
        self.window.show()
        self.app.processEvents()

        first_item = self.window.tasks_page.pending_list.item(0)
        row_widget = self.window.tasks_page.pending_list.itemWidget(first_item)

        self.assertGreaterEqual(first_item.sizeHint().height(), row_widget.sizeHint().height())
        self.assertLessEqual(row_widget.open_btn.geometry().bottom(), row_widget.rect().bottom())
        self.assertLessEqual(row_widget.done_btn.geometry().bottom(), row_widget.rect().bottom())
