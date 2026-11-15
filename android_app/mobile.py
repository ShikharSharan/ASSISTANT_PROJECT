from __future__ import annotations

import os
from pathlib import Path

from kivy.app import App
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

BACKGROUND = (1.0, 0.97, 0.92, 1)
TEXT = (0.32, 0.15, 0.03, 1)
MUTED = (0.55, 0.33, 0.14, 1)
ACCENT = (0.95, 0.48, 0.0, 1)
ACCENT_DARK = (0.42, 0.18, 0.0, 1)
CARD = (1.0, 0.99, 0.96, 1)
GREEN = (0.86, 0.97, 0.90, 1)


class AssistantMobileApp(App):
    title = "Assistant Pro"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chat_history: list[tuple[str, str]] = []
        self.current_page = "home"

    def build(self):
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)
        os.environ["APP_DATA_DIR"] = self.user_data_dir

        from app.ai import get_chat_response
        from app.backend import MoneyManager, SQLiteStorage, TaskManager
        from app.errors import AssistantDataError
        from app.validation import MONEY_ENTRY_TYPES, SPENDING_CATEGORIES, TASK_PRIORITIES

        self.get_chat_response = get_chat_response
        self.AssistantDataError = AssistantDataError
        self.task_priorities = TASK_PRIORITIES
        self.money_entry_types = MONEY_ENTRY_TYPES
        self.spending_categories = SPENDING_CATEGORIES
        self.storage = SQLiteStorage()
        self.task_manager = TaskManager(storage=self.storage)
        self.money_manager = MoneyManager(storage=self.storage)

        root = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        with root.canvas.before:
            from kivy.graphics import Color, Rectangle

            self._background_color = Color(*BACKGROUND)
            self._background_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_background, size=self._update_background)

        heading = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(72),
            spacing=dp(2),
        )
        heading.add_widget(
            self._label("Assistant Pro", height=dp(38), size=sp(24), color=ACCENT_DARK, bold=True)
        )
        heading.add_widget(
            self._label("Tasks, money, and daily guidance", height=dp(28), size=sp(13), color=MUTED)
        )
        root.add_widget(heading)

        self.page_area = BoxLayout()
        root.add_widget(self.page_area)
        root.add_widget(self._build_navigation())
        self.show_page("home")
        return root

    @staticmethod
    def _update_background(widget, _value):
        widget._background_rect.pos = widget.pos
        widget._background_rect.size = widget.size

    @staticmethod
    def _label(text, height=dp(32), size=sp(15), color=TEXT, bold=False):
        label = Label(
            text=text,
            size_hint_y=None,
            height=height,
            font_size=size,
            color=color,
            bold=bold,
            halign="left",
            valign="middle",
        )
        label.bind(width=lambda item, width: setattr(item, "text_size", (width, None)))
        return label

    @staticmethod
    def _input(hint, multiline=False):
        return TextInput(
            hint_text=hint,
            multiline=multiline,
            size_hint_y=None,
            height=dp(48 if not multiline else 82),
            padding=(dp(12), dp(12)),
            background_color=CARD,
            foreground_color=TEXT,
            cursor_color=ACCENT_DARK,
            hint_text_color=MUTED,
            font_size=sp(15),
        )

    @staticmethod
    def _button(text, callback, color=ACCENT):
        return Button(
            text=text,
            on_release=callback,
            size_hint_y=None,
            height=dp(48),
            background_normal="",
            background_down="",
            background_color=color,
            color=TEXT,
            font_size=sp(14),
            bold=True,
        )

    def _build_navigation(self):
        navigation = BoxLayout(
            size_hint_y=None,
            height=dp(54),
            spacing=dp(4),
        )
        for page, title in (
            ("home", "Home"),
            ("tasks", "Tasks"),
            ("money", "Money"),
            ("ai", "AI"),
            ("info", "Info"),
        ):
            button = self._button(
                title,
                lambda _button, selected=page: self.show_page(selected),
                color=GREEN if page == self.current_page else CARD,
            )
            button.font_size = sp(12)
            navigation.add_widget(button)
        self.navigation = navigation
        return navigation

    def _page_body(self, title, subtitle=""):
        body = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(10),
            padding=(dp(4), dp(8)),
        )
        body.bind(minimum_height=body.setter("height"))
        body.add_widget(
            self._label(title, height=dp(36), size=sp(21), color=ACCENT_DARK, bold=True)
        )
        if subtitle:
            body.add_widget(
                self._label(subtitle, height=dp(42), size=sp(13), color=MUTED)
            )
        return body

    def show_page(self, page):
        self.current_page = page
        self.page_area.clear_widgets()
        if page == "home":
            content = self._home_page()
        elif page == "tasks":
            content = self._tasks_page()
        elif page == "money":
            content = self._money_page()
        elif page == "ai":
            content = self._ai_page()
        else:
            content = self._info_page()
        self.page_area.add_widget(content)
        self._refresh_navigation()

    def _refresh_navigation(self):
        for page, button in zip(
            ("home", "tasks", "money", "ai", "info"),
            self.navigation.children[::-1],
        ):
            button.background_color = GREEN if page == self.current_page else CARD

    def _home_page(self):
        body = self._page_body("Your overview", "A quick view of your tasks and this month's money.")
        pending = self.task_manager.list_pending_tasks()
        completed = self.task_manager.list_completed_tasks()
        from datetime import datetime

        now = datetime.now()
        summary = self.money_manager.compute_summary(year=now.year, month=now.month)
        cards = (
            ("Pending tasks", str(len(pending))),
            ("Completed tasks", str(len(completed))),
            ("Income", f"₹{summary['salary']:,.2f}"),
            ("Expenses", f"₹{summary['expenses']:,.2f}"),
            ("Net balance", f"₹{summary['net_balance']:,.2f}"),
        )
        for title, value in cards:
            body.add_widget(
                self._label(f"{title}    {value}", height=dp(48), size=sp(16))
            )
        if pending:
            body.add_widget(self._label("Next up", height=dp(30), size=sp(17), bold=True))
            for task in pending[:3]:
                body.add_widget(
                    self._label(f"• {task.title}  ·  {task.priority}", height=dp(34), size=sp(14))
                )
        return self._wrap_body(body)

    def _tasks_page(self):
        body = self._page_body("Tasks", "Add work to do, then mark it complete when finished.")
        self.task_title = self._input("Task title")
        self.task_description = self._input("Notes (optional)")
        self.task_priority = Spinner(
            text="Medium",
            values=self.task_priorities,
            size_hint_y=None,
            height=dp(46),
            background_normal="",
            background_color=CARD,
            color=TEXT,
        )
        body.add_widget(self.task_title)
        body.add_widget(self.task_description)
        body.add_widget(self.task_priority)
        body.add_widget(self._button("Add task", self._add_task))
        body.add_widget(self._label("Pending", height=dp(32), size=sp(17), bold=True))

        tasks = self.task_manager.list_pending_tasks()
        if not tasks:
            body.add_widget(self._label("No pending tasks yet.", height=dp(34), color=MUTED))
        for task in tasks:
            row = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(6))
            row.add_widget(
                self._label(f"{task.title} · {task.priority}", height=dp(56), size=sp(14))
            )
            done = self._button(
                "Done",
                lambda _button, task_id=task.id: self._complete_task(task_id),
                color=GREEN,
            )
            done.size_hint_x = None
            done.width = dp(78)
            row.add_widget(done)
            body.add_widget(row)
        return self._wrap_body(body)

    def _add_task(self, _button):
        try:
            self.task_manager.add_task(
                self.task_title.text,
                self.task_description.text,
                self.task_priority.text,
            )
        except self.AssistantDataError as exc:
            self._show_message(str(exc))
            return
        self.show_page("tasks")

    def _complete_task(self, task_id):
        try:
            self.task_manager.mark_done(task_id)
        except self.AssistantDataError as exc:
            self._show_message(str(exc))
            return
        self.show_page("tasks")

    def _money_page(self):
        body = self._page_body("Money", "Track income, spending, payments, and loans.")
        self.money_type = Spinner(
            text="Expense",
            values=self.money_entry_types,
            size_hint_y=None,
            height=dp(46),
            background_normal="",
            background_color=CARD,
            color=TEXT,
        )
        self.money_amount = self._input("Amount")
        self.money_amount.input_filter = "float"
        self.money_note = self._input("Note (optional)")
        self.money_person = self._input("Person (for Given / Taken)")
        self.money_category = Spinner(
            text="Uncategorised",
            values=self.spending_categories,
            size_hint_y=None,
            height=dp(46),
            background_normal="",
            background_color=CARD,
            color=TEXT,
        )
        for widget in (
            self.money_type,
            self.money_amount,
            self.money_note,
            self.money_person,
            self.money_category,
        ):
            body.add_widget(widget)
        body.add_widget(self._button("Add entry", self._add_money_entry))
        body.add_widget(self._label("Recent entries", height=dp(32), size=sp(17), bold=True))

        entries = self.money_manager.list_entries()
        if not entries:
            body.add_widget(self._label("No money entries yet.", height=dp(34), color=MUTED))
        for entry in entries[:30]:
            person = f" · {entry.person}" if entry.person else ""
            note = f" · {entry.note}" if entry.note else ""
            body.add_widget(
                self._label(
                    f"{entry.entry_type}  ₹{entry.amount:,.2f}{person}{note}",
                    height=dp(38),
                    size=sp(14),
                )
            )
        return self._wrap_body(body)

    def _add_money_entry(self, _button):
        try:
            self.money_manager.add_entry(
                self.money_type.text,
                self.money_amount.text,
                note=self.money_note.text,
                person=self.money_person.text,
                category=self.money_category.text,
            )
        except self.AssistantDataError as exc:
            self._show_message(str(exc))
            return
        self.show_page("money")

    def _ai_page(self):
        body = self._page_body(
            "AI Assistant",
            "Built-in guidance based on your saved tasks and money entries.",
        )
        transcript = TextInput(
            text=self._format_chat_history(),
            readonly=True,
            multiline=True,
            size_hint_y=None,
            height=dp(260),
            background_color=CARD,
            foreground_color=TEXT,
            font_size=sp(14),
        )
        body.add_widget(transcript)
        self.chat_input = self._input("Ask about tasks, money, or planning")
        body.add_widget(self.chat_input)
        body.add_widget(self._button("Ask", self._send_chat))
        return self._wrap_body(body)

    def _format_chat_history(self):
        return "\n\n".join(f"{speaker}: {message}" for speaker, message in self.chat_history)

    def _send_chat(self, _button):
        question = self.chat_input.text.strip()
        if not question:
            return
        self.chat_history.append(("You", question))
        response = self.get_chat_response(question, self.task_manager, self.money_manager)
        self.chat_history.append(("Assistant", response))
        self.show_page("ai")

    def _info_page(self):
        body = self._page_body("About this Android version")
        body.add_widget(
            self._label(
                "Your Android database is stored in this app's private storage and is separate "
                "from the desktop database.",
                height=dp(72),
                size=sp(15),
            )
        )
        body.add_widget(
            self._label(
                "For this first version, Android uses standard SQLite in the app sandbox; "
                "it is not SQLCipher-encrypted and does not use the desktop password login.",
                height=dp(96),
                size=sp(14),
                color=MUTED,
            )
        )
        body.add_widget(
            self._label(
                "Built-in AI guidance works offline; no account or API key is required.",
                height=dp(54),
                size=sp(14),
                color=MUTED,
            )
        )
        return self._wrap_body(body)

    @staticmethod
    def _wrap_body(body):
        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(body)
        return scroll

    def _show_message(self, message):
        popup = Popup(
            title="Assistant Pro",
            content=Label(text=message, color=TEXT),
            size_hint=(0.88, 0.32),
        )
        popup.open()

    def on_stop(self):
        storage = getattr(self, "storage", None)
        if storage is not None:
            storage.conn.close()


def run():
    AssistantMobileApp().run()
