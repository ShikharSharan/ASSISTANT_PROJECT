from datetime import datetime
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QTextEdit, QLineEdit, QComboBox, QFormLayout, QSpinBox,
    QStackedWidget, QMessageBox, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt
from .backend import TaskManager, MoneyManager
from .ai import get_daily_suggestion
from .models import Task

APP_STYLESHEET = """
QMainWindow {
    background: #fff7ec;
}
QStackedWidget {
    background: transparent;
}
QWidget#infinityPage {
    background: transparent;
}
QFrame#pageCard {
    background-color: rgba(255, 252, 246, 228);
    border: 1px solid rgba(227, 166, 66, 0.28);
    border-radius: 24px;
}
QFrame#statCard {
    background-color: rgba(255, 247, 232, 0.98);
    border: 1px solid rgba(230, 177, 94, 0.42);
    border-radius: 16px;
}
QLabel {
    color: #5a2800;
    font-size: 13px;
}
QLabel#pageTitle {
    color: #8a3600;
    font-size: 24px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
QLabel#sectionTitle {
    color: #b45b00;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}
QLabel#detailValue {
    color: #6d2f00;
    font-size: 14px;
    font-weight: 600;
}
QLabel#statValue {
    color: #8a3600;
    font-size: 20px;
    font-weight: 700;
}
QLabel#statCaption {
    color: #b45b00;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
}
QPushButton {
    min-height: 36px;
    padding: 0 14px;
    border-radius: 12px;
    border: 1px solid #e6b36a;
    background-color: rgba(255, 253, 249, 0.95);
    color: #7a3200;
    font-size: 13px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #fff0d7;
}
QPushButton:pressed {
    background-color: #f7d29c;
}
QPushButton#primaryButton {
    background-color: #e68700;
    border: 1px solid #d97700;
    color: white;
}
QPushButton#primaryButton:hover {
    background-color: #d97c00;
}
QPushButton#secondaryButton {
    background-color: rgba(255, 245, 230, 0.98);
}
QPushButton#ghostButton {
    background-color: rgba(255, 255, 255, 0.55);
    border: 1px solid rgba(230, 161, 58, 0.38);
}
QPushButton:disabled {
    background-color: #f2dfc2;
    border-color: #ead3b0;
    color: #b58b5d;
}
QLineEdit,
QTextEdit,
QListWidget,
QComboBox,
QSpinBox {
    background-color: rgba(255, 255, 255, 0.95);
    color: #4f2200;
    border: 1px solid #efc57f;
    border-radius: 14px;
    padding: 8px 10px;
    selection-background-color: #f1a33a;
    selection-color: white;
}
QLineEdit:focus,
QTextEdit:focus,
QListWidget:focus,
QComboBox:focus,
QSpinBox:focus {
    border: 2px solid #e68700;
}
QListWidget {
    outline: 0;
}
QListWidget::item {
    margin: 3px 6px;
    padding: 10px 12px;
    border-radius: 10px;
    color: #5a2800;
}
QListWidget::item:hover {
    background-color: #fff1d8;
}
QListWidget::item:selected {
    background-color: #ffe0b3;
    color: #6b2a00;
}
QComboBox::drop-down {
    border: none;
    width: 26px;
}
QMessageBox {
    background-color: #fff9f0;
}
"""


def create_section_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("sectionTitle")
    return label


def create_page_layout(page: QWidget) -> QVBoxLayout:
    outer_layout = QVBoxLayout()
    outer_layout.setContentsMargins(16, 16, 16, 16)
    outer_layout.setSpacing(0)
    page.setLayout(outer_layout)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.Shape.NoFrame)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll_area.setStyleSheet("background: transparent;")
    outer_layout.addWidget(scroll_area)

    scroll_content = QWidget()
    scroll_content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    scroll_content.setStyleSheet("background: transparent;")
    scroll_area.setWidget(scroll_content)

    scroll_layout = QVBoxLayout()
    scroll_layout.setContentsMargins(0, 0, 0, 0)
    scroll_layout.setSpacing(0)
    scroll_content.setLayout(scroll_layout)

    page_card = QFrame()
    page_card.setObjectName("pageCard")
    scroll_layout.addWidget(page_card)

    card_layout = QVBoxLayout()
    card_layout.setContentsMargins(20, 18, 20, 18)
    card_layout.setSpacing(12)
    page_card.setLayout(card_layout)
    return card_layout


def create_stat_card(title: str) -> tuple[QFrame, QLabel]:
    stat_card = QFrame()
    stat_card.setObjectName("statCard")

    stat_layout = QVBoxLayout()
    stat_layout.setContentsMargins(14, 10, 14, 10)
    stat_layout.setSpacing(2)
    stat_card.setLayout(stat_layout)

    value_label = QLabel("0")
    value_label.setObjectName("statValue")
    stat_layout.addWidget(value_label)

    title_label = QLabel(title)
    title_label.setObjectName("statCaption")
    title_label.setWordWrap(True)
    stat_layout.addWidget(title_label)

    stat_layout.addStretch(1)
    return stat_card, value_label


def create_stats_grid(
    stat_specs: list[tuple[str, str]],
    columns: int,
) -> tuple[QGridLayout, dict[str, QLabel]]:
    stats_grid = QGridLayout()
    stats_grid.setHorizontalSpacing(10)
    stats_grid.setVerticalSpacing(10)

    stat_values: dict[str, QLabel] = {}
    for index, (key, title) in enumerate(stat_specs):
        stat_card, value_label = create_stat_card(title)
        stat_values[key] = value_label
        stats_grid.addWidget(stat_card, index // columns, index % columns)

    for column in range(columns):
        stats_grid.setColumnStretch(column, 1)

    return stats_grid, stat_values


def format_currency(value: float) -> str:
    return f"₹{int(round(value)):,}"


class InfinityPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("infinityPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor("#fffaf3"))
        gradient.setColorAt(0.45, QColor("#fff3dd"))
        gradient.setColorAt(1.0, QColor("#ffd59a"))
        painter.fillRect(self.rect(), gradient)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 176, 54, 44))
        painter.drawEllipse(int(self.width() * 0.60), -40, int(self.width() * 0.44), int(self.height() * 0.50))

        painter.setBrush(QColor(255, 255, 255, 92))
        painter.drawEllipse(-100, int(self.height() * 0.58), int(self.width() * 0.45), int(self.height() * 0.42))

        font = QFont("Georgia")
        font.setBold(True)
        font.setPixelSize(max(96, min(self.width(), self.height()) // 3))
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 6)
        painter.setFont(font)
        painter.setPen(QColor(214, 113, 0, 26))

        painter.save()
        painter.translate(int(self.width() * 0.56), int(self.height() * 0.46))
        painter.rotate(-18)
        painter.drawText(-int(self.width() * 0.48), 0, self.width(), self.height(), Qt.AlignmentFlag.AlignCenter, "INFINITY")
        painter.restore()

        super().paintEvent(event)


class HomePage(InfinityPage):
    def __init__(self, main_window, task_manager: TaskManager):
        super().__init__()
        self.main_window = main_window
        self.task_manager = task_manager

        layout = create_page_layout(self)

        # Date / summary header
        header = QLabel(f"Home – Today: {datetime.now().strftime('%a, %d %b %Y')}")
        header.setObjectName("pageTitle")
        layout.addWidget(header)

        home_stats, self.stat_values = create_stats_grid(
            [
                ("pending", "PENDING TASKS"),
                ("completed", "COMPLETED"),
                ("high_priority", "HIGH PRIORITY"),
                ("focus_hours", "FOCUS HOURS"),
            ],
            columns=4,
        )
        layout.addLayout(home_stats)

        # AI suggestion box
        layout.addWidget(create_section_title("AI SUGGESTION"))
        self.ai_text = QTextEdit()
        self.ai_text.setReadOnly(True)
        self.ai_text.setPlaceholderText("AI suggestions will appear here...")
        self.ai_text.setMinimumHeight(84)
        layout.addWidget(self.ai_text)

        refresh_btn = QPushButton("Refresh suggestion")
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.clicked.connect(self.refresh_suggestion)
        layout.addWidget(refresh_btn)

        # Pending tasks list
        layout.addWidget(create_section_title("PENDING TASKS"))
        self.pending_list = QListWidget()
        self.pending_list.itemDoubleClicked.connect(self.view_selected_task)
        self.pending_list.setSpacing(4)
        self.pending_list.setMinimumHeight(170)
        layout.addWidget(self.pending_list)

        # Buttons row
        btn_row = QGridLayout()
        btn_row.setHorizontalSpacing(12)
        btn_row.setVerticalSpacing(10)
        self.add_task_btn = QPushButton("Add new task")
        self.add_task_btn.setObjectName("primaryButton")
        self.add_task_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.add_task_btn.clicked.connect(self.go_to_add_task)
        btn_row.addWidget(self.add_task_btn, 0, 0)

        self.view_task_btn = QPushButton("View selected task")
        self.view_task_btn.setObjectName("secondaryButton")
        self.view_task_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.view_task_btn.clicked.connect(self.view_selected_task)
        btn_row.addWidget(self.view_task_btn, 0, 1)

        self.money_btn = QPushButton("Go to Money")
        self.money_btn.setObjectName("ghostButton")
        self.money_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.money_btn.clicked.connect(self.go_to_money)
        btn_row.addWidget(self.money_btn, 1, 0, 1, 2)
        btn_row.setColumnStretch(0, 1)
        btn_row.setColumnStretch(1, 1)

        layout.addLayout(btn_row)
        layout.addStretch(1)

        self.refresh_lists()
        self.refresh_suggestion()

    def refresh_lists(self):
        self.pending_list.clear()
        pending = self.task_manager.list_pending_tasks()
        for t in pending:
            item = QListWidgetItem(f"[ ] {t.title} ({t.priority})")
            item.setData(Qt.ItemDataRole.UserRole, t.id)
            self.pending_list.addItem(item)

        completed = self.task_manager.list_completed_tasks()
        high_priority = sum(1 for task in pending if task.priority == "High")
        self.stat_values["pending"].setText(str(len(pending)))
        self.stat_values["completed"].setText(str(len(completed)))
        self.stat_values["high_priority"].setText(str(high_priority))
        self.stat_values["focus_hours"].setText(f"~{len(pending)}h")

    def refresh_suggestion(self):
        suggestion = get_daily_suggestion(self.task_manager)
        self.ai_text.setPlainText(suggestion)

    def go_to_add_task(self):
        self.main_window.show_add_task_page()

    def go_to_money(self):
        self.main_window.show_money_page()

    def view_selected_task(self, _item=None):
        current_item = self.pending_list.currentItem()
        if current_item is None:
            QMessageBox.information(
                self,
                "Select a task",
                "Choose a pending task first, then click 'View selected task'.",
            )
            return

        task_id = current_item.data(Qt.ItemDataRole.UserRole)
        task = next(
            (pending_task for pending_task in self.task_manager.list_pending_tasks() if pending_task.id == task_id),
            None,
        )
        if task is None:
            QMessageBox.warning(
                self,
                "Task not found",
                "The selected task could not be loaded. Refresh the list and try again.",
            )
            self.refresh_lists()
            return

        self.main_window.show_task_details_page(task)

class AddTaskPage(InfinityPage):
    def __init__(self, main_window, task_manager: TaskManager):
        super().__init__()
        self.main_window = main_window
        self.task_manager = task_manager

        layout = create_page_layout(self)

        header = QLabel("Add Task")
        header.setObjectName("pageTitle")
        layout.addWidget(header)

        form = QFormLayout()
        form.setVerticalSpacing(14)
        form.setHorizontalSpacing(18)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("What needs to get done?")
        form.addRow("Title:", self.title_edit)

        self.details_edit = QTextEdit()
        self.details_edit.setPlaceholderText("Add notes, context, or the next action...")
        self.details_edit.setMinimumHeight(130)
        form.addRow("Details:", self.details_edit)

        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High"])
        form.addRow("Priority:", self.priority_combo)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        save_btn = QPushButton("Save task")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_task)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghostButton")
        cancel_btn.clicked.connect(self.cancel)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)

        layout.addLayout(btn_row)
        layout.addStretch(1)

    def save_task(self):
        title = self.title_edit.text().strip()
        if not title:
            return
        description = self.details_edit.toPlainText().strip()
        priority = self.priority_combo.currentText()
        self.task_manager.add_task(title=title, description=description, priority=priority)
        # clear form
        self.title_edit.clear()
        self.details_edit.clear()
        self.priority_combo.setCurrentText("Medium")
        # refresh home page and go back
        self.main_window.home_page.refresh_lists()
        self.main_window.home_page.refresh_suggestion()
        self.main_window.show_home_page()

    def cancel(self):
        self.main_window.show_home_page()

class TaskDetailsPage(InfinityPage):
    def __init__(self, main_window, task_manager: TaskManager):
        super().__init__()
        self.main_window = main_window
        self.task_manager = task_manager
        self.current_task = None

        layout = create_page_layout(self)

        header = QLabel("Task Details")
        header.setObjectName("pageTitle")
        layout.addWidget(header)

        form = QFormLayout()
        form.setVerticalSpacing(12)
        form.setHorizontalSpacing(18)

        self.title_value = QLabel("")
        self.title_value.setObjectName("detailValue")
        self.title_value.setWordWrap(True)
        form.addRow("Title:", self.title_value)

        self.priority_value = QLabel("")
        self.priority_value.setObjectName("detailValue")
        form.addRow("Priority:", self.priority_value)

        self.status_value = QLabel("")
        self.status_value.setObjectName("detailValue")
        form.addRow("Status:", self.status_value)

        self.created_value = QLabel("")
        self.created_value.setObjectName("detailValue")
        form.addRow("Created:", self.created_value)

        layout.addLayout(form)

        layout.addWidget(create_section_title("DESCRIPTION"))
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMinimumHeight(150)
        layout.addWidget(self.description_text)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.mark_done_btn = QPushButton("Mark as done")
        self.mark_done_btn.setObjectName("primaryButton")
        self.mark_done_btn.clicked.connect(self.mark_task_done)
        btn_row.addWidget(self.mark_done_btn)

        back_btn = QPushButton("Back to Home")
        back_btn.setObjectName("ghostButton")
        back_btn.clicked.connect(self.go_back_home)
        btn_row.addWidget(back_btn)

        layout.addLayout(btn_row)
        layout.addStretch(1)

    def show_task(self, task: Task):
        self.current_task = task
        self.title_value.setText(task.title)
        self.priority_value.setText(task.priority)
        self.status_value.setText("Completed" if task.done else "Pending")
        created_value = task.date.strftime("%d %b %Y, %I:%M %p") if task.date else "Not available"
        self.created_value.setText(created_value)
        self.description_text.setPlainText(task.description or "No description added.")
        self.mark_done_btn.setEnabled(not task.done)

    def mark_task_done(self):
        if self.current_task is None or self.current_task.done:
            return

        self.task_manager.mark_done(self.current_task.id)
        self.current_task.done = True
        self.main_window.home_page.refresh_lists()
        self.main_window.home_page.refresh_suggestion()
        self.main_window.show_home_page()

    def go_back_home(self):
        self.main_window.show_home_page()

class MoneyPage(InfinityPage):
    def __init__(self, main_window, money_manager: MoneyManager):
        super().__init__()
        self.main_window = main_window
        self.money_manager = money_manager

        layout = create_page_layout(self)

        header = QLabel("Money – This Month")
        header.setObjectName("pageTitle")
        layout.addWidget(header)

        money_stats, self.stat_values = create_stats_grid(
            [
                ("salary", "SALARY"),
                ("expenses", "EXPENSES"),
                ("emi", "EMI"),
                ("credit", "CREDIT"),
                ("owes_you", "OWES YOU"),
            ],
            columns=5,
        )
        layout.addLayout(money_stats)

        # Form to add entry
        layout.addWidget(create_section_title("ADD MONEY ENTRY"))

        form = QFormLayout()
        form.setVerticalSpacing(14)
        form.setHorizontalSpacing(18)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Income", "Expense", "EMI", "Credit", "Given", "Taken"])
        form.addRow("Type:", self.type_combo)

        self.amount_spin = QSpinBox()
        self.amount_spin.setRange(0, 1_000_000)
        self.amount_spin.setPrefix("₹ ")
        self.amount_spin.setGroupSeparatorShown(True)
        form.addRow("Amount:", self.amount_spin)

        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("Salary, groceries, fuel, rent...")
        form.addRow("Note:", self.note_edit)

        self.person_edit = QLineEdit()
        self.person_edit.setPlaceholderText("Optional")
        form.addRow("Person:", self.person_edit)

        layout.addLayout(form)

        add_btn = QPushButton("Add entry")
        add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self.add_entry)
        layout.addWidget(add_btn)

        layout.addWidget(create_section_title("RECENT ENTRIES"))
        self.entries_list = QListWidget()
        self.entries_list.setSpacing(4)
        self.entries_list.setMinimumHeight(170)
        layout.addWidget(self.entries_list)

        back_btn = QPushButton("Back to Home")
        back_btn.setObjectName("ghostButton")
        back_btn.clicked.connect(self.go_back_home)
        layout.addWidget(back_btn)
        layout.addStretch(1)

        self.refresh_summary()
        self.refresh_entries()

    def add_entry(self):
        entry_type = self.type_combo.currentText()
        amount = float(self.amount_spin.value())
        note = self.note_edit.text().strip()
        person = self.person_edit.text().strip()
        if amount <= 0:
            return
        self.money_manager.add_entry(entry_type, amount, note, person)
        # reset
        self.amount_spin.setValue(0)
        self.note_edit.clear()
        self.person_edit.clear()
        # refresh views
        self.refresh_summary()
        self.refresh_entries()

    def refresh_summary(self):
        summary = self.money_manager.compute_summary()
        self.stat_values["salary"].setText(format_currency(summary["salary"]))
        self.stat_values["expenses"].setText(format_currency(summary["expenses"]))
        self.stat_values["emi"].setText(format_currency(summary["emi"]))
        self.stat_values["credit"].setText(format_currency(summary["credit"]))
        self.stat_values["owes_you"].setText(format_currency(summary["owes_you"]))

    def refresh_entries(self):
        self.entries_list.clear()
        for e in self.money_manager.list_entries():
            sign = "+" if e.entry_type == "Income" else "-"
            date_str = e.date.strftime("%d %b %Y")
            person_part = f" ({e.person})" if e.person else ""
            text = f"[{e.entry_type}] {date_str} – {e.note}{person_part}  {sign}₹{e.amount:.0f}"
            self.entries_list.addItem(text)

    def go_back_home(self):
        self.main_window.show_home_page()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assistant Pro")
        self.resize(900, 600)

        self.task_manager = TaskManager()
        self.money_manager = MoneyManager()

        self.stack = QStackedWidget()
        self.stack.setObjectName("pageStack")
        self.setCentralWidget(self.stack)

        self.home_page = HomePage(self, self.task_manager)
        self.add_task_page = AddTaskPage(self, self.task_manager)
        self.task_details_page = TaskDetailsPage(self, self.task_manager)
        self.money_page = MoneyPage(self, self.money_manager)

        self.stack.addWidget(self.home_page)      # index 0
        self.stack.addWidget(self.add_task_page)  # index 1
        self.stack.addWidget(self.task_details_page)
        self.stack.addWidget(self.money_page)

        self.setStyleSheet(APP_STYLESHEET)
        self.show_home_page()

    def show_home_page(self):
        self.stack.setCurrentWidget(self.home_page)

    def show_add_task_page(self):
        self.stack.setCurrentWidget(self.add_task_page)

    def show_task_details_page(self, task: Task):
        self.task_details_page.show_task(task)
        self.stack.setCurrentWidget(self.task_details_page)

    def show_money_page(self):
        self.stack.setCurrentWidget(self.money_page)
