from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

BACKGROUND = (1.0, 0.97, 0.92, 1)
TEXT = (0.32, 0.15, 0.03, 1)
MUTED = (0.55, 0.33, 0.14, 1)
ACCENT = (0.95, 0.48, 0.0, 1)
ACCENT_DARK = (0.42, 0.18, 0.0, 1)
CARD = (1.0, 0.99, 0.96, 1)
GREEN = (0.86, 0.97, 0.90, 1)
AI_PROMPTS = (
    ("Plan my day", "Plan my day so I stay productive."),
    ("What first?", "What should I focus on first today?"),
    ("Money check", "How is my money looking this month?"),
    ("Evening reset", "Give me a productive evening routine."),
    ("Survival mode", "I'm overwhelmed - help me survive today."),
    ("Weekly goals", "Set my weekly goals for survival."),
    ("Productivity insights", "Give me productivity insights."),
)


class AssistantMobileApp(App):
    title = "Assistant Pro"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chat_history: list[tuple[str, str]] = []
        self.ai_scroll_to_bottom = False
        self.current_page = "home"

    def build(self):
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)
        os.environ["APP_DATA_DIR"] = self.user_data_dir

        from app.ai import get_chat_response
        from app.ai import get_ai_settings, get_ai_status_text, is_ai_connected, update_ai_settings
        from app.ai_settings import DEFAULT_MODEL, SUPPORTED_PROVIDERS
        from app.backup import (
            BACKUP_EXTENSION,
            ENCRYPTED_MAGIC,
            BackupError,
            export_backup,
            import_backup,
            inspect_backup,
        )
        from app.backend import MoneyManager, SQLiteStorage, TaskManager
        from app.errors import AssistantDataError
        from app.validation import MONEY_ENTRY_TYPES, SPENDING_CATEGORIES, TASK_PRIORITIES

        self.get_chat_response = get_chat_response
        self.get_ai_settings = get_ai_settings
        self.get_ai_status_text = get_ai_status_text
        self.is_ai_connected = is_ai_connected
        self.update_ai_settings = update_ai_settings
        self.default_ai_model = DEFAULT_MODEL
        self.supported_ai_providers = SUPPORTED_PROVIDERS
        self.backup_extension = BACKUP_EXTENSION
        self.backup_encrypted_magic = ENCRYPTED_MAGIC
        self.BackupError = BackupError
        self.export_backup = export_backup
        self.import_backup = import_backup
        self.inspect_backup = inspect_backup
        self.last_backup_at = "Never"
        self.backup_request_code = 7341
        self.pending_backup_operation = None
        self.pending_backup_pin = ""
        self.pending_backup_path = None
        self.AssistantDataError = AssistantDataError
        self.task_priorities = TASK_PRIORITIES
        self.money_entry_types = MONEY_ENTRY_TYPES
        self.spending_categories = SPENDING_CATEGORIES
        self.storage = SQLiteStorage()
        self.task_manager = TaskManager(storage=self.storage)
        self.money_manager = MoneyManager(storage=self.storage)
        self.active_task_filter = "All"
        self.task_search_text = ""
        self.selected_task_id = None
        self.selected_money_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self.active_money_filter = "All"
        self.editing_money_entry_id = None

        root = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        with root.canvas.before:
            from kivy.graphics import Color, Rectangle

            root._background_color = Color(*BACKGROUND)
            root._background_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_background, size=self._update_background)

        heading = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(58),
            spacing=dp(8),
        )
        brand = BoxLayout(orientation="vertical", spacing=0)
        brand.add_widget(
            self._label("Assistant Pro", height=dp(34), size=sp(22), color=ACCENT_DARK, bold=True)
        )
        brand.add_widget(
            self._label("PLAN YOUR DAY WITH CLARITY", height=dp(18), size=sp(9), color=MUTED, bold=True)
        )
        heading.add_widget(brand)
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

    @staticmethod
    def _surface(height, background=CARD, padding=(dp(14), dp(12)), spacing=dp(4)):
        surface = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=height,
            padding=padding,
            spacing=spacing,
        )
        with surface.canvas.before:
            Color(*background)
            surface._shape = RoundedRectangle(
                pos=surface.pos,
                size=surface.size,
                radius=[(dp(18), dp(18))] * 4,
            )

        def update_shape(widget, _value):
            widget._shape.pos = widget.pos
            widget._shape.size = widget.size

        surface.bind(pos=update_shape, size=update_shape)
        return surface

    def _summary_card(self, title, value, detail):
        card = self._surface(dp(82), padding=(dp(12), dp(10)), spacing=dp(2))
        card.add_widget(self._label(title.upper(), height=dp(18), size=sp(9), color=MUTED, bold=True))
        card.add_widget(self._label(value, height=dp(30), size=sp(19), color=ACCENT_DARK, bold=True))
        card.add_widget(self._label(detail, height=dp(15), size=sp(10), color=MUTED))
        return card

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
        from datetime import datetime

        now = datetime.now()
        greeting = "Good morning" if now.hour < 12 else "Good afternoon" if now.hour < 18 else "Good evening"
        body = self._page_body(
            greeting,
            now.strftime("%A, %B %d").upper() + "  ·  A fresh chance to make progress.",
        )
        pending = self.task_manager.list_pending_tasks()
        completed = self.task_manager.list_completed_tasks()
        summary = self.money_manager.compute_summary(year=now.year, month=now.month)

        focus_card = self._surface(dp(142), background=ACCENT_DARK, padding=(dp(16), dp(12)), spacing=dp(3))
        focus_card.add_widget(
            self._label("YOUR NEXT STEP", height=dp(18), size=sp(9), color=GREEN, bold=True)
        )
        if pending:
            focus_task = min(
                pending,
                key=lambda task: (
                    {"High": 0, "Medium": 1, "Low": 2}.get(task.priority, 3),
                    task.date or datetime.max,
                    task.id,
                ),
            )
            focus_card.add_widget(
                self._label(focus_task.title, height=dp(32), size=sp(17), color=CARD, bold=True)
            )
            focus_detail = f"{focus_task.priority} priority  ·  {len(pending)} task(s) waiting"
        else:
            focus_card.add_widget(
                self._label("Start with one small task", height=dp(32), size=sp(17), color=CARD, bold=True)
            )
            focus_detail = "Your next win can start right here."
        focus_card.add_widget(self._label(focus_detail, height=dp(20), size=sp(11), color=CARD))
        focus_action = self._button(
            "View tasks" if pending else "Add your first task",
            lambda _button: self.show_page("tasks"),
            color=GREEN,
        )
        focus_action.height = dp(38)
        focus_action.font_size = sp(11)
        focus_card.add_widget(focus_action)
        body.add_widget(focus_card)

        body.add_widget(
            self._label("THIS MONTH", height=dp(26), size=sp(12), color=ACCENT_DARK, bold=True)
        )
        metrics = GridLayout(
            cols=2,
            spacing=dp(9),
            size_hint_y=None,
            row_default_height=dp(82),
            row_force_default=True,
        )
        metrics.height = dp(82 * 2 + 9)
        metrics.add_widget(self._summary_card("Pending tasks", str(len(pending)), "Ready when you are"))
        metrics.add_widget(self._summary_card("Completed", str(len(completed)), "Progress so far"))
        metrics.add_widget(
            self._summary_card("Income", f"₹{summary['salary']:,.0f}", "Money coming in")
        )
        metrics.add_widget(
            self._summary_card("Expenses", f"₹{summary['expenses']:,.0f}", "Money going out")
        )
        body.add_widget(metrics)

        balance = self._surface(dp(58), background=GREEN, padding=(dp(14), dp(8)), spacing=0)
        balance.add_widget(
            self._label(
                f"NET BALANCE     ₹{summary['net_balance']:,.0f}",
                height=dp(38),
                size=sp(15),
                color=ACCENT_DARK,
                bold=True,
            )
        )
        body.add_widget(balance)

        body.add_widget(self._label("QUICK ACTIONS", height=dp(25), size=sp(12), color=ACCENT_DARK, bold=True))
        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(9))
        actions.add_widget(
            self._button("Add a task", lambda _button: self.show_page("tasks"), color=ACCENT)
        )
        actions.add_widget(
            self._button("Log money", lambda _button: self.show_page("money"), color=CARD)
        )
        body.add_widget(actions)
        return self._wrap_body(body)

    def _tasks_page(self):
        from datetime import datetime

        pending = self.task_manager.list_pending_tasks()
        completed = self.task_manager.list_completed_tasks()
        today = datetime.now().date()
        completed_today = sum(
            1 for task in completed
            if task.completed_at is not None and task.completed_at.date() == today
        )
        high_priority = sum(1 for task in pending if task.priority == "High")
        body = self._page_body(
            "Tasks",
            "Your full task board. Filter the queue, open details, and mark work done.",
        )

        stats = GridLayout(
            cols=2,
            spacing=dp(8),
            size_hint_y=None,
            row_default_height=dp(82),
            row_force_default=True,
        )
        stats.height = dp(172)
        stats.add_widget(self._summary_card("Pending tasks", str(len(pending)), "In your queue"))
        stats.add_widget(self._summary_card("Done today", str(completed_today), "Completed today"))
        stats.add_widget(self._summary_card("High priority", str(high_priority), "Needs attention"))
        stats.add_widget(self._summary_card("Focus hours", f"~{len(pending)}h", "Estimated effort"))
        body.add_widget(stats)

        body.add_widget(
            self._label("PENDING TASKS", height=dp(23), size=sp(11), color=ACCENT_DARK, bold=True)
        )
        filters = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(6))
        self.task_filter_buttons = {}
        for filter_name in ("All", "High", "Medium", "Low"):
            chip = self._button(
                filter_name,
                lambda _button, choice=filter_name: self._set_task_filter(choice),
                color=ACCENT if self.active_task_filter == filter_name else CARD,
            )
            chip.height = dp(36)
            chip.font_size = sp(11)
            filters.add_widget(chip)
            self.task_filter_buttons[filter_name] = chip
        body.add_widget(filters)

        self.task_search = self._input("Search tasks...")
        self.task_search.text = self.task_search_text
        self.task_search.size_hint_y = None
        self.task_search.height = dp(42)
        self.task_search.bind(text=self._on_task_search)
        body.add_widget(self.task_search)

        self.task_cards = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(7),
        )
        self.task_cards.bind(minimum_height=self.task_cards.setter("height"))
        body.add_widget(self.task_cards)
        self._refresh_task_cards()

        actions = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        actions.add_widget(
            self._button("Add task", lambda _button: self._open_add_task_dialog(), color=ACCENT)
        )
        actions.add_widget(
            self._button("Open selected", lambda _button: self._open_selected_task(), color=CARD)
        )
        body.add_widget(actions)
        return self._wrap_body(body)

    def _set_task_filter(self, filter_name):
        self.active_task_filter = filter_name
        self.show_page("tasks")

    def _on_task_search(self, _input, text):
        self.task_search_text = text
        self._refresh_task_cards()

    def _refresh_task_cards(self):
        from datetime import datetime

        if not hasattr(self, "task_cards"):
            return
        self.task_cards.clear_widgets()
        pending = self.task_manager.list_pending_tasks()
        search = self.task_search_text.strip().casefold()
        matches = [
            task for task in pending
            if (self.active_task_filter == "All" or task.priority == self.active_task_filter)
            and (
                not search
                or search in task.title.casefold()
                or search in task.description.casefold()
            )
        ]
        if self.selected_task_id not in {task.id for task in matches}:
            self.selected_task_id = matches[0].id if matches else None
        if not matches:
            if pending:
                message = "No tasks match this filter. Try another priority or search."
            else:
                message = "Your task list is clear. Add a task to get started."
            empty = self._surface(dp(82), background=CARD)
            empty.add_widget(self._label(message, height=dp(54), size=sp(13), color=MUTED))
            self.task_cards.add_widget(empty)
            return

        for task in matches:
            created = task.date.strftime("Created %d %b, %I:%M %p") if task.date else "Creation date unavailable"
            note = " ".join(task.description.split()) if task.description else "No extra notes yet. Open the task to add context."
            if len(note) > 90:
                note = note[:87].rstrip() + "..."
            card = self._surface(
                dp(126),
                background=GREEN if task.id == self.selected_task_id else CARD,
                padding=(dp(10), dp(8)),
                spacing=dp(2),
            )
            header = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(6))
            title_label = self._label(task.title, height=dp(28), size=sp(14), color=ACCENT_DARK, bold=True)
            header.add_widget(title_label)
            header.add_widget(
                self._label(task.priority, height=dp(28), size=sp(10), color=MUTED, bold=True)
            )
            card.add_widget(header)
            card.add_widget(self._label(created, height=dp(19), size=sp(10), color=MUTED))
            card.add_widget(self._label(note, height=dp(32), size=sp(11), color=TEXT))

            buttons = BoxLayout(size_hint_y=None, height=dp(33), spacing=dp(7))
            open_button = self._button(
                "Open",
                lambda _button, item=task: self._show_task_details(item),
                color=BACKGROUND,
            )
            open_button.height = dp(32)
            done_button = self._button(
                "Done",
                lambda _button, task_id=task.id: self._complete_task(task_id),
                color=ACCENT,
            )
            done_button.height = dp(32)
            buttons.add_widget(open_button)
            buttons.add_widget(done_button)
            card.add_widget(buttons)
            self.task_cards.add_widget(card)

    def _open_add_task_dialog(self):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))
        title_input = self._input("What needs to get done?")
        details_input = self._input("Add notes or the next action", multiline=True)
        priority = Spinner(
            text="Medium",
            values=self.task_priorities,
            size_hint_y=None,
            height=dp(44),
            background_normal="",
            background_color=CARD,
            color=TEXT,
        )
        content.add_widget(self._label("Create a task", height=dp(34), size=sp(19), color=ACCENT_DARK, bold=True))
        content.add_widget(title_input)
        content.add_widget(details_input)
        content.add_widget(priority)
        buttons = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        popup = Popup(title="Add task", content=content, size_hint=(0.92, 0.62), auto_dismiss=True)
        buttons.add_widget(self._button("Cancel", lambda _button: popup.dismiss(), color=CARD))

        def save_task(_button):
            try:
                self.task_manager.add_task(title_input.text, details_input.text, priority.text)
            except self.AssistantDataError as exc:
                self._show_message(str(exc))
                return
            popup.dismiss()
            self.show_page("tasks")

        buttons.add_widget(self._button("Save task", save_task, color=ACCENT))
        content.add_widget(buttons)
        popup.open()

    def _show_task_details(self, task):
        self.selected_task_id = task.id
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))
        content.add_widget(
            self._label(task.title, height=dp(48), size=sp(20), color=ACCENT_DARK, bold=True)
        )
        content.add_widget(
            self._label(f"{task.priority} priority", height=dp(25), size=sp(12), color=MUTED, bold=True)
        )
        created = task.date.strftime("%d %b %Y, %I:%M %p") if task.date else "Creation date unavailable"
        content.add_widget(self._label(created, height=dp(25), size=sp(11), color=MUTED))
        details = task.description or "No notes have been added to this task yet."
        content.add_widget(self._label(details, height=dp(110), size=sp(14), color=TEXT))
        buttons = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        popup = Popup(title="Task details", content=content, size_hint=(0.92, 0.55))
        buttons.add_widget(self._button("Close", lambda _button: popup.dismiss(), color=CARD))

        def complete_task(_button):
            popup.dismiss()
            self._complete_task(task.id)

        buttons.add_widget(self._button("Mark done", complete_task, color=ACCENT))
        content.add_widget(buttons)
        popup.open()

    def _open_selected_task(self):
        task = next(
            (item for item in self.task_manager.list_pending_tasks() if item.id == self.selected_task_id),
            None,
        )
        if task is None:
            self._show_message("Select a pending task first.")
            return
        self._show_task_details(task)

    def _complete_task(self, task_id):
        try:
            self.task_manager.mark_done(task_id)
        except self.AssistantDataError as exc:
            self._show_message(str(exc))
            return
        self.show_page("tasks")

    def _money_page(self):
        body = self._page_body("Money", "Track income, spending, payments, and loans.")
        actions = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        actions.add_widget(self._button("Ask AI", lambda _button: self.show_page("ai"), color=GREEN))
        actions.add_widget(self._button("Export", self._export_money_entries, color=CARD))
        body.add_widget(actions)

        month_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        month_row.add_widget(self._button("Previous", lambda _button: self._change_money_month(-1), color=CARD))
        month_row.add_widget(
            self._label(
                self.selected_money_month.strftime("%B %Y"),
                height=dp(42),
                size=sp(15),
                color=ACCENT_DARK,
                bold=True,
            )
        )
        month_row.add_widget(self._button("Next", lambda _button: self._change_money_month(1), color=CARD))
        body.add_widget(month_row)
        body.add_widget(
            self._label(
                f"Tracking entries saved in {self.selected_money_month.strftime('%B %Y')}.",
                height=dp(28),
                size=sp(12),
                color=MUTED,
            )
        )

        summary = self.money_manager.compute_summary(
            year=self.selected_money_month.year,
            month=self.selected_money_month.month,
        )
        stats = GridLayout(
            cols=2,
            spacing=dp(8),
            size_hint_y=None,
            row_default_height=dp(74),
            row_force_default=True,
        )
        stats.height = dp(3 * 74 + 2 * 8)
        stat_values = (
            ("Net balance", self._format_signed_money(summary["net_balance"])),
            ("Income", self._format_money(summary["salary"])),
            ("Expenses", self._format_money(summary["expenses"])),
            ("EMI", self._format_money(summary["emi"])),
            ("Credit", self._format_money(summary["credit"])),
            ("Owes you", self._format_money(summary["owes_you"])),
        )
        for title, value in stat_values:
            stats.add_widget(self._summary_card(title, value, "This month"))
        body.add_widget(stats)

        self.money_form_title = self._label(
            "Edit money entry" if self.editing_money_entry_id is not None else "Add money entry",
            height=dp(28),
            size=sp(15),
            color=ACCENT_DARK,
            bold=True,
        )
        body.add_widget(self.money_form_title)
        self.money_type = Spinner(
            text="Income",
            values=self.money_entry_types,
            size_hint_y=None,
            height=dp(46),
            background_normal="",
            background_color=CARD,
            color=TEXT,
        )
        self.money_amount = self._input("Amount")
        self.money_amount.input_filter = "float"
        self.money_note = self._input("Salary, groceries, fuel, rent...")
        self.money_person = self._input("Optional")
        self.money_date = self._input("YYYY-MM-DD")
        now = datetime.now()
        default_entry_date = (
            now
            if (self.selected_money_month.year, self.selected_money_month.month) == (now.year, now.month)
            else self.selected_money_month
        )
        self.money_date.text = default_entry_date.strftime("%Y-%m-%d")
        self.money_category = Spinner(
            text="Uncategorised",
            values=self.spending_categories,
            size_hint_y=None,
            height=dp(46),
            background_normal="",
            background_color=CARD,
            color=TEXT,
        )
        self.money_type.bind(text=self._update_money_person_hint)
        form_grid = GridLayout(
            cols=2,
            spacing=(dp(8), dp(6)),
            size_hint_y=None,
            row_default_height=dp(70),
            row_force_default=True,
        )
        form_grid.height = dp(146)
        for label, widget in (
            ("Type", self.money_type),
            ("Amount", self.money_amount),
            ("Note", self.money_note),
            ("Person", self.money_person),
        ):
            field = BoxLayout(orientation="vertical", spacing=dp(2))
            field.add_widget(self._label(label, height=dp(17), size=sp(10), color=MUTED, bold=True))
            field.add_widget(widget)
            form_grid.add_widget(field)
        body.add_widget(form_grid)
        category_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        category_row.add_widget(self._label("Category", height=dp(46), size=sp(12), color=MUTED, bold=True))
        category_row.add_widget(self.money_category)
        body.add_widget(category_row)

        date_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        date_row.add_widget(
            self._label("Date (YYYY-MM-DD)", height=dp(46), size=sp(12), color=MUTED, bold=True)
        )
        date_row.add_widget(self.money_date)
        date_row.add_widget(
            self._button(
                "Today",
                lambda _button: setattr(self.money_date, "text", datetime.now().strftime("%Y-%m-%d")),
                color=CARD,
            )
        )
        body.add_widget(date_row)

        form_actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        save_label = "Save changes" if self.editing_money_entry_id is not None else "Add entry"
        form_actions.add_widget(self._button(save_label, self._add_money_entry))
        if self.editing_money_entry_id is not None:
            form_actions.add_widget(
                self._button("Cancel", lambda _button: self._reset_money_form(), color=CARD)
            )
        body.add_widget(form_actions)
        body.add_widget(self._label("Recent entries", height=dp(28), size=sp(15), bold=True))

        filter_grid = GridLayout(
            cols=3,
            spacing=dp(6),
            size_hint_y=None,
            row_default_height=dp(40),
            row_force_default=True,
        )
        filters = ("All", *self.money_entry_types)
        filter_grid.height = dp(((len(filters) + 2) // 3) * 40 + 6)
        for name in filters:
            color = ACCENT if name == self.active_money_filter else CARD
            filter_grid.add_widget(
                self._button(
                    name,
                    lambda _button, selected=name: self._set_money_filter(selected),
                    color=color,
                )
            )
        body.add_widget(filter_grid)

        entries = self.money_manager.list_entries(
            year=self.selected_money_month.year,
            month=self.selected_money_month.month,
            entry_type=None if self.active_money_filter == "All" else self.active_money_filter,
        )
        if not entries:
            empty_text = (
                "No entries match this filter."
                if self.active_money_filter != "All"
                else f"No entries for {self.selected_money_month.strftime('%B %Y')} yet."
            )
            empty_card = self._surface(dp(74), padding=(dp(14), dp(10)))
            empty_card.add_widget(self._label(empty_text, height=dp(50), color=MUTED))
            body.add_widget(empty_card)
        for entry in entries[:30]:
            body.add_widget(self._money_entry_card(entry))

        if self.editing_money_entry_id is not None:
            editing = next((entry for entry in entries if entry.id == self.editing_money_entry_id), None)
            if editing is not None:
                self.money_type.text = editing.entry_type
                self.money_amount.text = f"{editing.amount:.2f}"
                self.money_note.text = editing.note
                self.money_person.text = editing.person
                self.money_category.text = editing.category
                self.money_date.text = editing.date.strftime("%Y-%m-%d")
        return self._wrap_body(body)

    def _add_money_entry(self, _button):
        try:
            amount = float(self.money_amount.text)
        except ValueError:
            self._show_message("Enter an amount greater than zero.")
            return
        if amount <= 0:
            self._show_message("Enter an amount greater than zero.")
            return
        try:
            entry_date = datetime.strptime(self.money_date.text.strip(), "%Y-%m-%d")
        except ValueError:
            self._show_message("Enter a valid date in YYYY-MM-DD format.")
            return
        try:
            if self.editing_money_entry_id is None:
                self.money_manager.add_entry(
                    self.money_type.text,
                    amount,
                    note=self.money_note.text,
                    person=self.money_person.text,
                    category=self.money_category.text,
                    entry_date=entry_date,
                )
            else:
                self.money_manager.update_entry(
                    self.editing_money_entry_id,
                    self.money_type.text,
                    amount,
                    note=self.money_note.text,
                    person=self.money_person.text,
                    category=self.money_category.text,
                    entry_date=entry_date,
                )
        except self.AssistantDataError as exc:
            self._show_message(str(exc))
            return
        self.selected_money_month = entry_date.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        self.editing_money_entry_id = None
        self.active_money_filter = "All"
        self.show_page("money")

    def _money_entry_card(self, entry):
        card = self._surface(dp(160), padding=(dp(12), dp(8)), spacing=dp(2))
        heading = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(6))
        title = entry.note or entry.person or entry.category or "Money entry"
        heading.add_widget(self._label(title, height=dp(24), size=sp(14), bold=True))
        heading.add_widget(
            self._label(entry.entry_type, height=dp(24), size=sp(10), color=MUTED, bold=True)
        )
        card.add_widget(heading)
        details = f"{entry.date.strftime('%d %b %Y')} | {entry.entry_type}"
        if entry.person:
            details += f" | {entry.person}"
        card.add_widget(self._label(details, height=dp(19), size=sp(10), color=MUTED))
        is_positive = entry.entry_type in {"Income", "Taken"}
        amount = self._format_money(entry.amount)
        if not is_positive:
            amount = f"-{amount}"
        card.add_widget(
            self._label(amount, height=dp(32), size=sp(15), color=ACCENT_DARK, bold=True)
        )
        buttons = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
        buttons.add_widget(
            self._button("Edit", lambda _button, item=entry: self._begin_edit_money_entry(item), color=CARD)
        )
        buttons.add_widget(
            self._button(
                "Delete",
                lambda _button, item=entry: self._confirm_delete_money_entry(item),
                color=CARD,
            )
        )
        card.add_widget(buttons)
        return card

    @staticmethod
    def _format_money(value):
        return f"₹{int(round(value)):,}"

    @classmethod
    def _format_signed_money(cls, value):
        sign = "-" if value < 0 else ""
        return f"{sign}{cls._format_money(abs(value))}"

    def _update_money_person_hint(self, _spinner, entry_type):
        self.money_person.hint_text = "Person name" if entry_type in {"Given", "Taken"} else "Optional"

    def _change_money_month(self, delta):
        month_index = self.selected_money_month.year * 12 + self.selected_money_month.month - 1 + delta
        year, month = divmod(month_index, 12)
        self.selected_money_month = datetime(year, month + 1, 1)
        self.editing_money_entry_id = None
        self.show_page("money")

    def _set_money_filter(self, entry_type):
        self.active_money_filter = entry_type
        self.show_page("money")

    def _begin_edit_money_entry(self, entry):
        self.editing_money_entry_id = entry.id
        self.show_page("money")

    def _reset_money_form(self):
        self.editing_money_entry_id = None
        self.show_page("money")

    def _confirm_delete_money_entry(self, entry):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        content.add_widget(
            self._label(f"Delete '{entry.note or entry.entry_type}'?", height=dp(54), color=TEXT)
        )
        buttons = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        popup = Popup(
            title="Delete entry",
            content=content,
            size_hint=(0.88, 0.3),
            background="",
            background_color=CARD,
            separator_color=ACCENT,
        )
        buttons.add_widget(self._button("Cancel", lambda _button: popup.dismiss(), color=CARD))

        def delete_entry(_button):
            popup.dismiss()
            try:
                self.money_manager.delete_entry(entry.id)
            except self.AssistantDataError as exc:
                self._show_message(str(exc))
                return
            if self.editing_money_entry_id == entry.id:
                self.editing_money_entry_id = None
            self.show_page("money")

        buttons.add_widget(self._button("Delete", delete_entry, color=ACCENT))
        content.add_widget(buttons)
        popup.open()

    def _export_money_entries(self, _button):
        export_path = Path(self.user_data_dir) / "money_export.csv"
        try:
            entries = self.money_manager.list_entries()
            with export_path.open("w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(("ID", "Type", "Amount", "Date", "Note", "Person", "Category"))
                for entry in entries:
                    writer.writerow(
                        (
                            entry.id,
                            entry.entry_type,
                            entry.amount,
                            entry.date.strftime("%Y-%m-%d"),
                            entry.note,
                            entry.person,
                            entry.category,
                        )
                    )
        except OSError as exc:
            self._show_message(f"Unable to export money entries: {exc}")
            return
        self._show_message(f"Money entries exported to:\n{export_path}")

    def _ai_page(self):
        body = self._page_body(
            "AI Coach",
            "Ask about tasks, daily life, routines, or money. This coach uses the tasks and money data saved in the app to give grounded suggestions.",
        )
        self._ensure_ai_welcome()

        shortcuts = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        shortcuts.add_widget(self._button("Home", lambda _button: self.show_page("home"), color=CARD))
        shortcuts.add_widget(self._button("Money", lambda _button: self.show_page("money"), color=CARD))
        body.add_widget(shortcuts)

        pending = self.task_manager.list_pending_tasks()
        high_priority = sum(1 for task in pending if task.priority == "High")
        summary = self.money_manager.compute_summary(
            year=self.selected_money_month.year,
            month=self.selected_money_month.month,
        )
        stats = GridLayout(
            cols=3,
            spacing=dp(6),
            size_hint_y=None,
            row_default_height=dp(74),
            row_force_default=True,
        )
        stats.height = dp(74)
        stats.add_widget(self._summary_card("Pending", str(len(pending)), "Open tasks"))
        stats.add_widget(self._summary_card("High priority", str(high_priority), "Needs focus"))
        stats.add_widget(
            self._summary_card(
                "Net this month",
                self._format_signed_money(summary["net_balance"]),
                "Current balance",
            )
        )
        body.add_widget(stats)

        body.add_widget(
            self._label("QUICK QUESTIONS", height=dp(24), size=sp(11), color=ACCENT_DARK, bold=True)
        )
        prompts = GridLayout(
            cols=2,
            spacing=dp(6),
            size_hint_y=None,
            row_default_height=dp(38),
            row_force_default=True,
        )
        prompts.height = dp(4 * 38 + 3 * 6)
        for label, prompt in AI_PROMPTS:
            prompts.add_widget(
                self._button(
                    label,
                    lambda _button, question=prompt: self._send_chat(question),
                    color=CARD,
                )
            )
        body.add_widget(prompts)

        body.add_widget(
            self._label("CHAT", height=dp(24), size=sp(11), color=ACCENT_DARK, bold=True)
        )
        self.chat_scroll = ScrollView(
            size_hint_y=None,
            height=dp(270),
            do_scroll_x=False,
            bar_width=dp(3),
        )
        self.chat_messages = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
            padding=(dp(2), dp(2)),
        )
        self.chat_messages.bind(minimum_height=self.chat_messages.setter("height"))
        for speaker, message in self.chat_history:
            self.chat_messages.add_widget(self._chat_bubble(speaker, message))
        self.chat_scroll.add_widget(self.chat_messages)
        self.chat_scroll.scroll_y = 0
        body.add_widget(self.chat_scroll)

        composer = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.chat_input = self._input("Ask about tasks, money, or planning")
        self.chat_input.bind(on_text_validate=self._send_chat)
        composer.add_widget(self.chat_input)
        send_button = self._button("Send", self._send_chat)
        send_button.size_hint_x = 0.38
        composer.add_widget(send_button)
        body.add_widget(composer)
        clear_button = self._button("Clear chat", self._reset_ai_chat, color=CARD)
        clear_button.height = dp(38)
        body.add_widget(clear_button)
        scroll = self._wrap_body(body)
        Clock.schedule_once(lambda _dt: setattr(self.chat_scroll, "scroll_y", 0), 0.1)
        if self.ai_scroll_to_bottom:
            self.ai_scroll_to_bottom = False
            Clock.schedule_once(lambda _dt: setattr(scroll, "scroll_y", 0), 0.1)
        return scroll

    def _chat_bubble(self, speaker, message):
        is_user = speaker == "You"
        color = ACCENT if is_user else CARD
        text_color = CARD if is_user else TEXT
        role_color = CARD if is_user else MUTED
        bubble = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=(dp(10), dp(8)),
            spacing=dp(4),
        )
        with bubble.canvas.before:
            Color(*color)
            bubble._shape = RoundedRectangle(
                pos=bubble.pos,
                size=bubble.size,
                radius=[(dp(14), dp(14))] * 4,
            )

        def update_shape(widget, _value):
            widget._shape.pos = widget.pos
            widget._shape.size = widget.size

        bubble.bind(pos=update_shape, size=update_shape)
        role = self._label(speaker, height=dp(16), size=sp(10), color=role_color, bold=True)
        bubble.add_widget(role)
        message_label = Label(
            text=message,
            size_hint_y=None,
            font_size=sp(13),
            color=text_color,
            halign="left",
            valign="top",
        )
        message_label.bind(width=lambda label, width: setattr(label, "text_size", (width, None)))

        def update_message_height(label, _value):
            label.height = max(dp(20), label.texture_size[1] + dp(2))
            bubble.height = label.height + dp(38)

        message_label.bind(texture_size=update_message_height)
        bubble.add_widget(message_label)
        return bubble

    def _ensure_ai_welcome(self):
        if self.chat_history:
            return
        pending = self.task_manager.list_pending_tasks()
        summary = self.money_manager.compute_summary(
            year=self.selected_money_month.year,
            month=self.selected_money_month.month,
        )
        if pending:
            focus_task = min(
                pending,
                key=lambda task: (
                    {"High": 0, "Medium": 1, "Low": 2}.get(task.priority, 3),
                    task.date or datetime.max,
                    task.id,
                ),
            )
            task_text = (
                f"Your strongest focus task right now is '{focus_task.title}', and you have "
                f"{len(pending)} pending task{'s' if len(pending) != 1 else ''}. "
            )
        else:
            task_text = "You do not have pending tasks right now, so this is a good window to plan ahead. "
        if any(summary.values()):
            net_balance = self._format_signed_money(summary["net_balance"])
            money_text = (
                f"For {self.selected_money_month.strftime('%B %Y')}, your current net balance is "
                f"{net_balance}. "
            )
        else:
            money_text = (
                f"You have not logged money entries for {self.selected_money_month.strftime('%B %Y')} yet. "
            )
        welcome = (
            "Ask me anything about productivity, tasks, or money. "
            f"{task_text}{money_text}"
            "Try one of the quick questions above if you want a fast start."
        )
        self.chat_history.append(("AI Coach", welcome))

    def _send_chat(self, _button):
        question = _button if isinstance(_button, str) else self.chat_input.text.strip()
        if not question:
            return
        try:
            response = self.get_chat_response(
                question,
                self.task_manager,
                self.money_manager,
                reference_date=self.selected_money_month,
            )
        except self.AssistantDataError as exc:
            self._show_message(str(exc))
            return
        self.chat_history.append(("You", question))
        self.chat_history.append(("Assistant", response))
        self.ai_scroll_to_bottom = True
        self.show_page("ai")

    def _reset_ai_chat(self, _button):
        self.chat_history.clear()
        self.show_page("ai")

    def _info_page(self):
        body = self._page_body("Settings", "Manage the AI provider used by chat and suggestions.")
        home_row = BoxLayout(size_hint_y=None, height=dp(40))
        home_row.add_widget(Widget())
        home_button = self._button("Home", lambda _button: self.show_page("home"), color=CARD)
        home_button.size_hint_x = None
        home_button.width = dp(90)
        home_row.add_widget(home_button)
        body.add_widget(home_row)

        body.add_widget(
            self._label("AI CONNECTION", height=dp(24), size=sp(11), color=ACCENT_DARK, bold=True)
        )
        settings = self.get_ai_settings()
        self.settings_provider = Spinner(
            text=settings.provider,
            values=self.supported_ai_providers,
            size_hint_y=None,
            height=dp(44),
            background_normal="",
            background_color=CARD,
            color=TEXT,
        )
        body.add_widget(self._label("Provider", height=dp(20), size=sp(11), color=MUTED, bold=True))
        body.add_widget(self.settings_provider)

        self.settings_model = self._input("Model name")
        self.settings_model.text = settings.model
        body.add_widget(self._label("Model", height=dp(20), size=sp(11), color=MUTED, bold=True))
        body.add_widget(self.settings_model)

        self.settings_api_key = self._input("Paste your provider API key")
        self.settings_api_key.password = True
        self.settings_api_key.text = settings.api_key
        body.add_widget(self._label("API key", height=dp(20), size=sp(11), color=MUTED, bold=True))
        body.add_widget(self.settings_api_key)

        status_color = GREEN if self.is_ai_connected() else (0.95, 0.88, 0.84, 1)
        self.settings_status = self._label(
            self.get_ai_status_text(),
            height=dp(36),
            size=sp(12),
            color=TEXT,
            bold=True,
        )
        status_card = self._surface(dp(44), background=status_color, padding=(dp(10), dp(4)))
        status_card.add_widget(self.settings_status)
        body.add_widget(status_card)

        ai_actions = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        ai_actions.add_widget(self._button("Save AI settings", self._save_ai_settings))
        ai_actions.add_widget(
            self._button("Reset model", self._reset_ai_model, color=CARD)
        )
        body.add_widget(ai_actions)

        body.add_widget(
            self._label("DATA & BACKUP", height=dp(24), size=sp(11), color=ACCENT_DARK, bold=True)
        )
        backup_actions = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        backup_actions.add_widget(self._button("Export Backup", self._prompt_backup_pin))
        backup_actions.add_widget(
            self._label(f"Last backup: {self.last_backup_at}", height=dp(44), size=sp(11), color=MUTED)
        )
        body.add_widget(backup_actions)

        import_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        import_row.add_widget(self._button("Import Backup", self._start_backup_import, color=CARD))
        import_row.add_widget(
            self._label("This will replace all current data", height=dp(44), size=sp(11), color=MUTED)
        )
        body.add_widget(import_row)
        body.add_widget(
            self._label(
                "Android stores its data in this app's private storage, separate from the desktop app.",
                height=dp(48),
                size=sp(12),
                color=MUTED,
            )
        )
        return self._wrap_body(body)

    def _save_ai_settings(self, _button):
        try:
            self.update_ai_settings(
                provider=self.settings_provider.text,
                model=self.settings_model.text.strip(),
                api_key=self.settings_api_key.text.strip(),
            )
        except OSError as exc:
            self._show_message(f"Unable to save AI settings: {exc}")
            return
        self.show_page("info")
        self._show_message("AI provider settings have been saved.")

    def _reset_ai_model(self, _button):
        self.settings_model.text = self.default_ai_model

    def _prompt_backup_pin(self, _button):
        self._show_backup_pin_dialog(
            "Protect Backup",
            "Optional PIN. Leave blank for an unencrypted backup.",
            self._start_backup_export,
        )

    def _start_backup_export(self, pin):
        self.pending_backup_operation = "export"
        self.pending_backup_pin = pin
        self._start_backup_picker()

    def _start_backup_import(self, _button):
        self.pending_backup_operation = "import"
        self.pending_backup_pin = ""
        self._start_backup_picker()

    def _show_backup_pin_dialog(self, title, message, callback):
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        content.add_widget(self._label(message, height=dp(44), size=sp(12), color=MUTED))
        pin_input = self._input("Backup PIN (optional)")
        pin_input.password = True
        content.add_widget(pin_input)
        buttons = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.9, 0.34),
            background="",
            background_color=CARD,
            separator_color=ACCENT,
            title_color=TEXT,
        )
        buttons.add_widget(self._button("Cancel", lambda _button: popup.dismiss(), color=CARD))

        def continue_with_pin(_button):
            popup.dismiss()
            callback(pin_input.text.strip())

        buttons.add_widget(self._button("Continue", continue_with_pin))
        content.add_widget(buttons)
        popup.open()

    def _start_backup_picker(self):
        try:
            from android import activity
            from jnius import autoclass

            Intent = autoclass("android.content.Intent")
            intent = Intent(Intent.ACTION_CREATE_DOCUMENT if self.pending_backup_operation == "export" else Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType(
                "application/octet-stream" if self.pending_backup_operation == "export" else "*/*"
            )
            if self.pending_backup_operation == "export":
                name = f"assistant-{datetime.now().strftime('%Y%m%d-%H%M')}{self.backup_extension}"
                intent.putExtra(Intent.EXTRA_TITLE, name)
            self.backup_activity = activity
            self.backup_result_callback = self._on_backup_picker_result
            activity.bind(on_activity_result=self.backup_result_callback)
            autoclass("org.kivy.android.PythonActivity").mActivity.startActivityForResult(
                intent,
                self.backup_request_code,
            )
        except Exception as exc:
            self.pending_backup_operation = None
            self.pending_backup_pin = ""
            self._show_message(f"Unable to open the Android file picker: {exc}")

    def _on_backup_picker_result(self, request_code, result_code, intent):
        if request_code != self.backup_request_code:
            return
        if self.backup_activity is not None and self.backup_result_callback is not None:
            self.backup_activity.unbind(on_activity_result=self.backup_result_callback)
        self.backup_activity = None
        self.backup_result_callback = None
        Clock.schedule_once(
            lambda _dt: self._handle_backup_picker_result(result_code, intent),
            0,
        )

    def _handle_backup_picker_result(self, result_code, intent):
        operation = self.pending_backup_operation
        pin = self.pending_backup_pin
        self.pending_backup_operation = None
        self.pending_backup_pin = ""
        if result_code != -1 or intent is None:
            return
        uri = intent.getData()
        if uri is None:
            self._show_message("The Android file picker did not return a file.")
            return
        try:
            if operation == "export":
                self._write_backup_to_uri(uri, pin)
            elif operation == "import":
                path = Path(self.user_data_dir) / "selected_backup.assistantbackup"
                self._copy_backup_from_uri(uri, path)
                self.pending_backup_path = path
                if path.read_bytes().startswith(self.backup_encrypted_magic):
                    self._show_backup_pin_dialog(
                        "Unlock Backup",
                        "Enter the PIN used when this backup was created.",
                        lambda backup_pin: self._prepare_backup_import(path, backup_pin),
                    )
                else:
                    self._prepare_backup_import(path, "")
        except Exception as exc:
            self._cleanup_pending_backup()
            self._show_message(f"Backup operation failed: {exc}")

    def _write_backup_to_uri(self, uri, pin):
        from jnius import autoclass

        temp_path = Path(self.user_data_dir) / "pending_backup.assistantbackup"
        output_stream = None
        try:
            preview = self.export_backup(
                temp_path,
                pin=pin,
                db_path=Path(self.storage.db_path),
            )
            resolver = autoclass("org.kivy.android.PythonActivity").mActivity.getContentResolver()
            output_stream = resolver.openOutputStream(uri)
            if output_stream is None:
                raise OSError("Unable to write to the selected destination.")
            with temp_path.open("rb") as backup_file:
                while True:
                    chunk = backup_file.read(65536)
                    if not chunk:
                        break
                    output_stream.write(chunk)
            output_stream.flush()
            self.last_backup_at = preview.created_at
            self.show_page("info")
            self._show_message(f"Backup exported successfully.\n{preview.summary()}")
        finally:
            if output_stream is not None:
                output_stream.close()
            temp_path.unlink(missing_ok=True)

    def _copy_backup_from_uri(self, uri, destination):
        from jnius import autoclass

        resolver = autoclass("org.kivy.android.PythonActivity").mActivity.getContentResolver()
        input_stream = resolver.openInputStream(uri)
        if input_stream is None:
            raise OSError("Unable to read the selected backup.")
        buffer = bytearray(65536)
        try:
            with destination.open("wb") as backup_file:
                while True:
                    length = input_stream.read(buffer, 0, len(buffer))
                    if length == -1:
                        break
                    backup_file.write(buffer[:length])
        finally:
            input_stream.close()

    def _prepare_backup_import(self, path, pin):
        try:
            preview = self.inspect_backup(path, pin=pin)
        except self.BackupError as exc:
            self._show_message(str(exc))
            self._cleanup_pending_backup()
            return
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        content.add_widget(
            self._label(
                f"{preview.summary()}\n\nImporting replaces all current data. Continue?",
                height=dp(126),
                size=sp(12),
                color=TEXT,
            )
        )
        buttons = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        popup = Popup(
            title="Replace current data?",
            content=content,
            size_hint=(0.92, 0.4),
            background="",
            background_color=CARD,
            separator_color=ACCENT,
            title_color=TEXT,
        )
        buttons.add_widget(
            self._button(
                "Cancel",
                lambda _button: (popup.dismiss(), self._cleanup_pending_backup()),
                color=CARD,
            )
        )
        buttons.add_widget(
            self._button(
                "Import",
                lambda _button: self._apply_backup_import(path, pin, popup),
            )
        )
        content.add_widget(buttons)
        popup.open()

    def _apply_backup_import(self, path, pin, popup):
        popup.dismiss()
        target_path = Path(self.storage.db_path)
        import_error = None
        try:
            self.storage.conn.close()
            preview = self.import_backup(path, pin=pin, db_path=target_path)
        except Exception as exc:
            import_error = exc
        try:
            from app.backend import MoneyManager, SQLiteStorage, TaskManager

            self.storage = SQLiteStorage()
            self.task_manager = TaskManager(storage=self.storage)
            self.money_manager = MoneyManager(storage=self.storage)
        except Exception as exc:
            self._cleanup_pending_backup()
            self._show_message(f"Unable to reopen app data after backup import: {exc}")
            return
        self._cleanup_pending_backup()
        if import_error is not None:
            self._show_message(f"Unable to import backup: {import_error}")
            return
        self.show_page("home")
        self._show_message(f"Backup imported successfully.\n{preview.summary()}")

    def _cleanup_pending_backup(self):
        path = self.pending_backup_path
        self.pending_backup_path = None
        if path is not None:
            path.unlink(missing_ok=True)

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
