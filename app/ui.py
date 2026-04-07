from datetime import datetime
from html import escape
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QTextEdit, QLineEdit, QComboBox, QFormLayout, QSpinBox, QDoubleSpinBox, QListView,
    QStackedWidget, QMessageBox, QFrame, QScrollArea
)
from PyQt6.QtCore import QSize, Qt
from .backend import TaskManager, MoneyManager
from .ai import get_chat_response, get_daily_suggestion
from .errors import AssistantDataError
from .models import Task
from .validation import MONEY_ENTRY_TYPES, TASK_PRIORITIES

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
QFrame#statCard[tone="pending"] {
    background-color: rgba(255, 243, 224, 0.98);
}
QFrame#statCard[tone="done"] {
    background-color: rgba(246, 242, 225, 0.98);
}
QFrame#statCard[tone="alert"] {
    background-color: rgba(255, 235, 219, 0.98);
}
QFrame#statCard[tone="focus"] {
    background-color: rgba(255, 249, 238, 0.98);
}
QFrame#statCard[tone="money"] {
    background-color: rgba(255, 245, 226, 0.98);
}
QFrame#statCard[tone="expense"] {
    background-color: rgba(255, 238, 224, 0.98);
}
QFrame#statCard[tone="credit"] {
    background-color: rgba(255, 241, 229, 0.98);
}
QFrame#statCard[tone="owe"] {
    background-color: rgba(245, 243, 230, 0.98);
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
QLabel#pageSubtitle {
    color: #a9651d;
    font-size: 13px;
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
QLabel#insightHeading,
QLabel#focusTitle,
QLabel#emptyStateTitle,
QLabel#taskTitle {
    color: #7a3200;
    font-size: 15px;
    font-weight: 700;
}
QLabel#insightText,
QLabel#focusBody,
QLabel#emptyStateBody,
QLabel#taskBody {
    color: #6f4419;
    font-size: 13px;
}
QLabel#focusMeta,
QLabel#taskMeta {
    color: #b16a22;
    font-size: 11px;
}
QLabel#priorityBadge {
    border-radius: 10px;
    padding: 3px 8px;
    font-size: 10px;
    font-weight: 700;
}
QLabel#priorityBadge[priority="High"] {
    background-color: #ffe0c1;
    color: #9c3f00;
}
QLabel#priorityBadge[priority="Medium"] {
    background-color: #fff1d0;
    color: #8b5a00;
}
QLabel#priorityBadge[priority="Low"] {
    background-color: #f5f0df;
    color: #6e6a2d;
}
QLabel#monthLabel {
    color: #8a3600;
    font-size: 16px;
    font-weight: 700;
}
QLabel#entryTypeBadge {
    border-radius: 10px;
    padding: 3px 8px;
    font-size: 10px;
    font-weight: 700;
    background-color: #fff0d0;
    color: #8a5a00;
}
QLabel#entryAmount {
    font-size: 15px;
    font-weight: 700;
}
QLabel#entryAmount[direction="positive"] {
    color: #8a3600;
}
QLabel#entryAmount[direction="negative"] {
    color: #9a4300;
}
QLabel#entryTitle {
    color: #7a3200;
    font-size: 14px;
    font-weight: 700;
}
QLabel#entryMeta {
    color: #b16a22;
    font-size: 11px;
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
    background-color: #ffd08a;
    border: 2px solid #e68700;
    color: #7a3200;
    font-weight: 700;
}
QPushButton#primaryButton:hover {
    background-color: #ffc56a;
}
QPushButton#primaryButton:pressed {
    background-color: #f2b453;
}
QPushButton#secondaryButton {
    background-color: rgba(255, 245, 230, 0.98);
}
QPushButton#ghostButton {
    background-color: rgba(255, 255, 255, 0.55);
    border: 1px solid rgba(230, 161, 58, 0.38);
}
QPushButton#compactButton,
QPushButton#compactPrimaryButton,
QPushButton#compactDangerButton,
QPushButton#filterChip {
    min-height: 30px;
    padding: 0 12px;
    border-radius: 10px;
    font-size: 12px;
}
QPushButton#compactPrimaryButton {
    background-color: #ffd08a;
    border: 2px solid #e68700;
    color: #7a3200;
    font-weight: 700;
}
QPushButton#compactPrimaryButton:hover {
    background-color: #ffc56a;
}
QPushButton#compactDangerButton {
    background-color: #fff0e1;
    border: 1px solid #f0b173;
    color: #9a4300;
}
QPushButton#compactDangerButton:hover {
    background-color: #ffdcbc;
}
QPushButton#filterChip {
    background-color: rgba(255, 250, 241, 0.95);
    border: 1px solid rgba(230, 161, 58, 0.45);
}
QPushButton#filterChip:checked {
    background-color: #ffd08a;
    border: 2px solid #e68700;
    color: #7a3200;
    font-weight: 700;
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
QSpinBox,
QDoubleSpinBox {
    background-color: rgba(255, 255, 255, 0.95);
    color: #4f2200;
    border: 1px solid #efc57f;
    border-radius: 14px;
    padding: 8px 10px;
    selection-background-color: #f1a33a;
    selection-color: white;
}
QComboBox {
    padding-right: 30px;
}
QLineEdit:focus,
QTextEdit:focus,
QListWidget:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus {
    border: 2px solid #e68700;
}
QTextEdit#chatHistory {
    background-color: rgba(255, 253, 249, 0.98);
    border: 1px solid rgba(230, 161, 58, 0.38);
    border-radius: 18px;
    padding: 10px 12px;
}
QLineEdit#chatInput {
    min-height: 38px;
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
QFrame#insightCard,
QFrame#focusCard,
QFrame#emptyStateCard,
QFrame#taskCard,
QFrame#moneyEntryCard {
    background-color: rgba(255, 251, 244, 0.94);
    border: 1px solid rgba(232, 177, 86, 0.42);
    border-radius: 18px;
}
QFrame#focusCard {
    background-color: rgba(255, 245, 226, 0.98);
}
QFrame#taskCard[selected="true"] {
    background-color: #fff0d8;
    border: 2px solid #e68700;
}
QFrame#emptyStateCard {
    background-color: rgba(255, 248, 236, 0.98);
}
QFrame#moneyEntryCard {
    background-color: rgba(255, 250, 242, 0.98);
}
QMessageBox {
    background-color: #fff9f0;
}
"""

COMBO_POPUP_STYLESHEET = """
QListView {
    background-color: #fff9f2;
    color: #6b2a00;
    border: 1px solid #efc57f;
    border-radius: 12px;
    outline: 0;
    padding: 6px;
}
QListView::item {
    min-height: 30px;
    margin: 2px 4px;
    padding: 6px 10px;
    border-radius: 8px;
    color: #6b2a00;
}
QListView::item:hover {
    background-color: #fff0d7;
    color: #7a3200;
}
QListView::item:selected {
    background-color: #f1a33a;
    color: #fffdf9;
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


def apply_combo_popup_theme(combo_box: QComboBox):
    popup_view = QListView()
    popup_view.setObjectName("comboPopup")
    popup_view.setFrameShape(QFrame.Shape.NoFrame)
    popup_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    popup_view.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
    popup_view.setSpacing(2)
    popup_view.setUniformItemSizes(True)
    popup_view.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    popup_view.viewport().setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    popup_view.viewport().setAutoFillBackground(True)
    popup_view.setStyleSheet(COMBO_POPUP_STYLESHEET)
    combo_box.setView(popup_view)
    combo_box.setMaxVisibleItems(8)


def create_stat_card(title: str, tone: str = "default") -> tuple[QFrame, QLabel]:
    stat_card = QFrame()
    stat_card.setObjectName("statCard")
    stat_card.setProperty("tone", tone)

    stat_layout = QVBoxLayout()
    stat_layout.setContentsMargins(14, 10, 14, 10)
    stat_layout.setSpacing(2)
    stat_card.setLayout(stat_layout)

    value_label = QLabel("0")
    value_label.setObjectName("statValue")
    value_label.setProperty("tone", tone)
    stat_layout.addWidget(value_label)

    title_label = QLabel(title)
    title_label.setObjectName("statCaption")
    title_label.setWordWrap(True)
    stat_layout.addWidget(title_label)

    stat_layout.addStretch(1)
    return stat_card, value_label


def create_stats_grid(
    stat_specs: list[tuple[str, str, str]],
    columns: int,
) -> tuple[QGridLayout, dict[str, QLabel]]:
    stats_grid = QGridLayout()
    stats_grid.setHorizontalSpacing(10)
    stats_grid.setVerticalSpacing(10)

    stat_values: dict[str, QLabel] = {}
    for index, (key, title, tone) in enumerate(stat_specs):
        stat_card, value_label = create_stat_card(title, tone)
        stat_values[key] = value_label
        stats_grid.addWidget(stat_card, index // columns, index % columns)

    for column in range(columns):
        stats_grid.setColumnStretch(column, 1)

    return stats_grid, stat_values


def format_currency(value: float) -> str:
    return f"₹{int(round(value)):,}"


def format_signed_currency(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}₹{abs(int(round(value))):,}"


def get_greeting_text(moment: datetime) -> str:
    if moment.hour < 12:
        return "Good morning"
    if moment.hour < 18:
        return "Good afternoon"
    return "Good evening"


def priority_rank(priority: str) -> int:
    return {
        "High": 0,
        "Medium": 1,
        "Low": 2,
    }.get(priority, 3)


def format_task_preview(description: str) -> str:
    if not description:
        return "No extra notes yet. Open the task to add context."
    compact = " ".join(description.split())
    if len(compact) <= 90:
        return compact
    return f"{compact[:87]}..."


def format_task_timestamp(moment: datetime | None) -> str:
    if moment is None:
        return "No saved time"
    return moment.strftime("%d %b, %I:%M %p")


def month_start(moment: datetime | None = None) -> datetime:
    source = moment or datetime.now()
    return datetime(source.year, source.month, 1)


def shift_month(moment: datetime, delta: int) -> datetime:
    month_index = (moment.year * 12 + (moment.month - 1)) + delta
    year = month_index // 12
    month = month_index % 12 + 1
    return datetime(year, month, 1)


def format_month_label(moment: datetime) -> str:
    return moment.strftime("%B %Y")


def is_positive_money_entry(entry_type: str) -> bool:
    return entry_type in {"Income", "Taken"}


def format_money_note(entry) -> str:
    if entry.note:
        return entry.note
    if entry.entry_type == "Income":
        return "Untitled income entry"
    return "Untitled money entry"


def repolish(widget: QWidget) -> None:
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


class TaskListCard(QFrame):
    def __init__(self, task: Task, select_callback, open_callback, done_callback):
        super().__init__()
        self.task = task
        self.select_callback = select_callback
        self.open_callback = open_callback
        self.done_callback = done_callback

        self.setObjectName("taskCard")
        self.setProperty("selected", False)

        root_layout = QHBoxLayout()
        root_layout.setContentsMargins(14, 12, 14, 12)
        root_layout.setSpacing(12)
        self.setLayout(root_layout)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        root_layout.addLayout(content_layout, 1)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        content_layout.addLayout(title_row)

        self.title_label = QLabel(task.title)
        self.title_label.setObjectName("taskTitle")
        self.title_label.setWordWrap(True)
        title_row.addWidget(self.title_label, 1)

        self.priority_badge = QLabel(task.priority)
        self.priority_badge.setObjectName("priorityBadge")
        self.priority_badge.setProperty("priority", task.priority)
        title_row.addWidget(self.priority_badge)

        self.meta_label = QLabel(f"Created {format_task_timestamp(task.date)}")
        self.meta_label.setObjectName("taskMeta")
        content_layout.addWidget(self.meta_label)

        self.body_label = QLabel(format_task_preview(task.description))
        self.body_label.setObjectName("taskBody")
        self.body_label.setWordWrap(True)
        content_layout.addWidget(self.body_label)

        for label in (
            self.title_label,
            self.priority_badge,
            self.meta_label,
            self.body_label,
        ):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        action_layout = QVBoxLayout()
        action_layout.setSpacing(8)
        root_layout.addLayout(action_layout)

        self.open_btn = QPushButton("Open")
        self.open_btn.setObjectName("compactButton")
        self.open_btn.clicked.connect(lambda: self.open_callback(task.id))
        action_layout.addWidget(self.open_btn)

        self.done_btn = QPushButton("Done")
        self.done_btn.setObjectName("compactPrimaryButton")
        self.done_btn.clicked.connect(lambda: self.done_callback(task.id))
        action_layout.addWidget(self.done_btn)
        action_layout.addStretch(1)

    def mousePressEvent(self, event):
        self.select_callback()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.select_callback()
        self.open_callback(self.task.id)
        super().mouseDoubleClickEvent(event)

    def set_selected(self, selected: bool):
        self.setProperty("selected", selected)
        repolish(self)


class MoneyEntryCard(QFrame):
    def __init__(self, entry, edit_callback, delete_callback):
        super().__init__()
        self.entry = entry
        self.setObjectName("moneyEntryCard")

        root_layout = QHBoxLayout()
        root_layout.setContentsMargins(14, 12, 14, 12)
        root_layout.setSpacing(12)
        self.setLayout(root_layout)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        root_layout.addLayout(content_layout, 1)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        content_layout.addLayout(top_row)

        self.title_label = QLabel(format_money_note(entry))
        self.title_label.setObjectName("entryTitle")
        self.title_label.setWordWrap(True)
        top_row.addWidget(self.title_label, 1)

        self.type_badge = QLabel(entry.entry_type)
        self.type_badge.setObjectName("entryTypeBadge")
        top_row.addWidget(self.type_badge)

        person_part = f" | {entry.person}" if entry.person else ""
        self.meta_label = QLabel(f"{entry.date.strftime('%d %b %Y')} | {entry.entry_type}{person_part}")
        self.meta_label.setObjectName("entryMeta")
        content_layout.addWidget(self.meta_label)

        signed_amount = entry.amount if is_positive_money_entry(entry.entry_type) else -entry.amount
        self.amount_label = QLabel(format_signed_currency(signed_amount))
        self.amount_label.setObjectName("entryAmount")
        self.amount_label.setProperty(
            "direction",
            "positive" if signed_amount >= 0 else "negative",
        )
        content_layout.addWidget(self.amount_label)

        action_layout = QVBoxLayout()
        action_layout.setSpacing(8)
        root_layout.addLayout(action_layout)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setObjectName("compactButton")
        self.edit_btn.clicked.connect(lambda: edit_callback(entry))
        action_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setObjectName("compactDangerButton")
        self.delete_btn.clicked.connect(lambda: delete_callback(entry))
        action_layout.addWidget(self.delete_btn)
        action_layout.addStretch(1)


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


class AssistantChatPage(InfinityPage):
    STARTER_PROMPTS = [
        ("Plan my day", "Plan my day so I stay productive."),
        ("What first?", "What should I focus on first today?"),
        ("Money check", "How is my money looking this month?"),
        ("Evening reset", "Give me a productive evening routine."),
    ]

    def __init__(self, main_window, task_manager: TaskManager, money_manager: MoneyManager):
        super().__init__()
        self.main_window = main_window
        self.task_manager = task_manager
        self.money_manager = money_manager

        layout = create_page_layout(self)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        header_label = QLabel("AI Coach")
        header_label.setObjectName("pageTitle")
        header_row.addWidget(header_label)
        header_row.addStretch(1)

        self.home_btn = QPushButton("Home")
        self.home_btn.setObjectName("compactButton")
        self.home_btn.clicked.connect(self.go_home)
        header_row.addWidget(self.home_btn)

        self.money_btn = QPushButton("Money")
        self.money_btn.setObjectName("compactButton")
        self.money_btn.clicked.connect(self.go_money)
        header_row.addWidget(self.money_btn)
        layout.addLayout(header_row)

        self.subtitle_label = QLabel(
            "Ask about tasks, daily life, routines, or money. This coach uses the tasks and money data "
            "saved in the app to give grounded suggestions."
        )
        self.subtitle_label.setObjectName("pageSubtitle")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        chat_stats, self.stat_values = create_stats_grid(
            [
                ("pending", "PENDING", "pending"),
                ("high_priority", "HIGH PRIORITY", "alert"),
                ("net_balance", "NET THIS MONTH", "focus"),
            ],
            columns=3,
        )
        layout.addLayout(chat_stats)

        layout.addWidget(create_section_title("QUICK QUESTIONS"))
        prompt_grid = QGridLayout()
        prompt_grid.setHorizontalSpacing(10)
        prompt_grid.setVerticalSpacing(10)
        for index, (label, prompt) in enumerate(self.STARTER_PROMPTS):
            button = QPushButton(label)
            button.setObjectName("compactButton")
            button.clicked.connect(
                lambda checked=False, current_prompt=prompt: self.send_prompt(current_prompt)
            )
            prompt_grid.addWidget(button, index // 2, index % 2)
        prompt_grid.setColumnStretch(0, 1)
        prompt_grid.setColumnStretch(1, 1)
        layout.addLayout(prompt_grid)

        layout.addWidget(create_section_title("CHAT"))
        self.chat_history = QTextEdit()
        self.chat_history.setObjectName("chatHistory")
        self.chat_history.setReadOnly(True)
        self.chat_history.setMinimumHeight(300)
        layout.addWidget(self.chat_history)

        layout.addWidget(create_section_title("YOUR MESSAGE"))
        self.prompt_edit = QLineEdit()
        self.prompt_edit.setObjectName("chatInput")
        self.prompt_edit.setPlaceholderText("Ask what to focus on, how your money looks, or how to plan the day...")
        self.prompt_edit.returnPressed.connect(self.send_message)
        layout.addWidget(self.prompt_edit)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("primaryButton")
        self.send_btn.clicked.connect(self.send_message)
        btn_row.addWidget(self.send_btn)

        self.clear_btn = QPushButton("Clear chat")
        self.clear_btn.setObjectName("ghostButton")
        self.clear_btn.clicked.connect(self.reset_conversation)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)
        layout.addStretch(1)

        self.reset_conversation()

    def current_reference_month(self) -> datetime:
        if hasattr(self.main_window, "money_page"):
            return self.main_window.money_page.selected_month
        return month_start()

    def refresh_context(self):
        reference_month = self.current_reference_month()
        pending_tasks = self.task_manager.list_pending_tasks()
        high_priority = sum(1 for task in pending_tasks if task.priority == "High")
        summary = self.money_manager.compute_summary(
            year=reference_month.year,
            month=reference_month.month,
        )
        net_balance = summary["net_balance"]
        net_text = format_signed_currency(net_balance) if net_balance < 0 else format_currency(net_balance)

        self.stat_values["pending"].setText(str(len(pending_tasks)))
        self.stat_values["high_priority"].setText(str(high_priority))
        self.stat_values["net_balance"].setText(net_text)

    def build_welcome_message(self) -> str:
        reference_month = self.current_reference_month()
        pending_tasks = self.task_manager.list_pending_tasks()
        summary = self.money_manager.compute_summary(
            year=reference_month.year,
            month=reference_month.month,
        )
        if pending_tasks:
            focus_task = min(
                pending_tasks,
                key=lambda task: (
                    priority_rank(task.priority),
                    task.date or datetime.max,
                    task.id,
                ),
            )
            task_text = (
                f"Your strongest focus task right now is '{focus_task.title}', and you have "
                f"{len(pending_tasks)} pending task{'s' if len(pending_tasks) != 1 else ''}. "
            )
        else:
            task_text = "You do not have pending tasks right now, so this is a good window to plan ahead. "

        if any(summary.values()):
            net_balance = summary["net_balance"]
            net_text = format_signed_currency(net_balance) if net_balance < 0 else format_currency(net_balance)
            money_text = (
                f"For {format_month_label(reference_month)}, your current net balance is {net_text}. "
            )
        else:
            money_text = f"You have not logged money entries for {format_month_label(reference_month)} yet. "

        return (
            "Ask me anything about productivity, tasks, or money. "
            f"{task_text}{money_text}"
            "Try one of the quick questions above if you want a fast start."
        )

    def reset_conversation(self):
        self.has_user_messages = False
        self.refresh_context()
        self.chat_history.clear()
        self.append_message("AI Coach", self.build_welcome_message())
        self.prompt_edit.clear()

    def prepare_page(self):
        if getattr(self, "has_user_messages", False):
            self.refresh_context()
            return
        self.reset_conversation()

    def append_message(self, role: str, text: str):
        safe_text = escape(text).replace("\n", "<br>")
        if role == "You":
            bubble_background = "#fff0d8"
            border_color = "#e68700"
            role_color = "#8a3600"
        else:
            bubble_background = "rgba(255, 251, 244, 0.98)"
            border_color = "#efc57f"
            role_color = "#b45b00"

        message_html = (
            f'<div style="margin:0 0 10px 0; padding:12px 14px; background:{bubble_background}; '
            f'border:1px solid {border_color}; border-radius:16px;">'
            f'<div style="font-size:11px; font-weight:700; color:{role_color}; letter-spacing:0.5px;">'
            f"{escape(role.upper())}</div>"
            f'<div style="margin-top:6px; color:#5a2800; font-size:13px; line-height:1.5;">{safe_text}</div>'
            "</div>"
        )
        self.chat_history.insertHtml(message_html)
        self.chat_history.insertHtml("<br>")
        scroll_bar = self.chat_history.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def send_prompt(self, prompt: str):
        self.prompt_edit.setText(prompt)
        self.send_message()

    def send_message(self):
        prompt = self.prompt_edit.text().strip()
        if not prompt:
            return

        self.has_user_messages = True
        self.refresh_context()
        self.append_message("You", prompt)
        reply = get_chat_response(
            prompt,
            self.task_manager,
            self.money_manager,
            reference_date=self.current_reference_month(),
        )
        self.append_message("AI Coach", reply)
        self.prompt_edit.clear()
        self.refresh_context()

    def go_home(self):
        self.main_window.show_home_page()

    def go_money(self):
        self.main_window.show_money_page()


class HomePage(InfinityPage):
    def __init__(self, main_window, task_manager: TaskManager):
        super().__init__()
        self.main_window = main_window
        self.task_manager = task_manager
        self.active_filter = "All"
        self.filter_buttons = {}
        self.task_rows = {}
        self.current_focus_task_id = None

        layout = create_page_layout(self)

        self.header_label = QLabel(f"Home – Today: {datetime.now().strftime('%a, %d %b %Y')}")
        self.header_label.setObjectName("pageTitle")
        layout.addWidget(self.header_label)

        self.subtitle_label = QLabel("")
        self.subtitle_label.setObjectName("pageSubtitle")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        home_stats, self.stat_values = create_stats_grid(
            [
                ("pending", "PENDING TASKS", "pending"),
                ("done_today", "DONE TODAY", "done"),
                ("high_priority", "HIGH PRIORITY", "alert"),
                ("focus_hours", "FOCUS HOURS", "focus"),
            ],
            columns=4,
        )
        layout.addLayout(home_stats)

        ai_header = QHBoxLayout()
        ai_header.addWidget(create_section_title("TODAY'S NUDGE"))
        ai_header.addStretch(1)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("compactButton")
        refresh_btn.clicked.connect(self.refresh_suggestion)
        ai_header.addWidget(refresh_btn)
        self.ai_chat_btn = QPushButton("Chat with AI")
        self.ai_chat_btn.setObjectName("compactPrimaryButton")
        self.ai_chat_btn.clicked.connect(self.go_to_ai_chat)
        ai_header.addWidget(self.ai_chat_btn)
        layout.addLayout(ai_header)

        self.ai_card = QFrame()
        self.ai_card.setObjectName("insightCard")
        ai_card_layout = QVBoxLayout()
        ai_card_layout.setContentsMargins(16, 14, 16, 14)
        ai_card_layout.setSpacing(6)
        self.ai_card.setLayout(ai_card_layout)

        self.ai_heading_label = QLabel("Best next step")
        self.ai_heading_label.setObjectName("insightHeading")
        ai_card_layout.addWidget(self.ai_heading_label)

        self.ai_text = QLabel("AI suggestions will appear here...")
        self.ai_text.setObjectName("insightText")
        self.ai_text.setWordWrap(True)
        ai_card_layout.addWidget(self.ai_text)
        layout.addWidget(self.ai_card)

        layout.addWidget(create_section_title("TODAY FOCUS"))
        self.focus_card = QFrame()
        self.focus_card.setObjectName("focusCard")
        focus_layout = QVBoxLayout()
        focus_layout.setContentsMargins(16, 14, 16, 14)
        focus_layout.setSpacing(6)
        self.focus_card.setLayout(focus_layout)

        self.focus_title_label = QLabel("")
        self.focus_title_label.setObjectName("focusTitle")
        self.focus_title_label.setWordWrap(True)
        focus_layout.addWidget(self.focus_title_label)

        self.focus_meta_label = QLabel("")
        self.focus_meta_label.setObjectName("focusMeta")
        focus_layout.addWidget(self.focus_meta_label)

        self.focus_body_label = QLabel("")
        self.focus_body_label.setObjectName("focusBody")
        self.focus_body_label.setWordWrap(True)
        focus_layout.addWidget(self.focus_body_label)

        focus_actions = QHBoxLayout()
        focus_actions.setSpacing(10)
        self.focus_open_btn = QPushButton("Open focus")
        self.focus_open_btn.setObjectName("compactButton")
        self.focus_open_btn.clicked.connect(self.open_focus_task)
        focus_actions.addWidget(self.focus_open_btn)

        self.focus_done_btn = QPushButton("Done now")
        self.focus_done_btn.setObjectName("compactPrimaryButton")
        self.focus_done_btn.clicked.connect(self.complete_focus_task)
        focus_actions.addWidget(self.focus_done_btn)
        focus_actions.addStretch(1)
        focus_layout.addLayout(focus_actions)
        layout.addWidget(self.focus_card)

        tasks_header = QHBoxLayout()
        tasks_header.addWidget(create_section_title("PENDING TASKS"))
        tasks_header.addStretch(1)
        layout.addLayout(tasks_header)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)
        for filter_name in ("All", "High", "Medium", "Low"):
            button = QPushButton(filter_name)
            button.setObjectName("filterChip")
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, current_filter=filter_name: self.set_active_filter(current_filter)
            )
            self.filter_buttons[filter_name] = button
            filter_row.addWidget(button)
        self.filter_buttons[self.active_filter].setChecked(True)
        filter_row.addStretch(1)
        layout.addLayout(filter_row)

        self.pending_list = QListWidget()
        self.pending_list.setSpacing(4)
        self.pending_list.setMinimumHeight(170)
        self.pending_list.itemSelectionChanged.connect(self.sync_task_card_selection)
        layout.addWidget(self.pending_list)

        self.empty_state_card = QFrame()
        self.empty_state_card.setObjectName("emptyStateCard")
        empty_layout = QVBoxLayout()
        empty_layout.setContentsMargins(16, 14, 16, 14)
        empty_layout.setSpacing(6)
        self.empty_state_card.setLayout(empty_layout)

        self.empty_state_title = QLabel("")
        self.empty_state_title.setObjectName("emptyStateTitle")
        empty_layout.addWidget(self.empty_state_title)

        self.empty_state_body = QLabel("")
        self.empty_state_body.setObjectName("emptyStateBody")
        self.empty_state_body.setWordWrap(True)
        empty_layout.addWidget(self.empty_state_body)

        self.empty_state_action_btn = QPushButton("Add task")
        self.empty_state_action_btn.setObjectName("compactPrimaryButton")
        self.empty_state_action_btn.clicked.connect(self.go_to_add_task)
        empty_layout.addWidget(self.empty_state_action_btn)
        layout.addWidget(self.empty_state_card)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        self.add_task_btn = QPushButton("Add task")
        self.add_task_btn.setObjectName("primaryButton")
        self.add_task_btn.clicked.connect(self.go_to_add_task)
        btn_row.addWidget(self.add_task_btn)

        self.view_task_btn = QPushButton("Open selected")
        self.view_task_btn.setObjectName("secondaryButton")
        self.view_task_btn.clicked.connect(self.view_selected_task)
        btn_row.addWidget(self.view_task_btn)

        self.money_btn = QPushButton("Money")
        self.money_btn.setObjectName("ghostButton")
        self.money_btn.clicked.connect(self.go_to_money)
        btn_row.addWidget(self.money_btn)

        layout.addLayout(btn_row)
        layout.addStretch(1)

        self.refresh_lists()
        self.refresh_suggestion()

    def refresh_lists(self):
        pending = self.task_manager.list_pending_tasks()
        completed = self.task_manager.list_completed_tasks()
        today = datetime.now().date()
        completed_today = sum(
            1
            for task in completed
            if task.completed_at is not None and task.completed_at.date() == today
        )
        high_priority = sum(1 for task in pending if task.priority == "High")
        filtered_pending = self.get_filtered_tasks(pending)
        current_selection = self.pending_list.currentItem()
        selected_task_id = (
            current_selection.data(Qt.ItemDataRole.UserRole)
            if current_selection is not None
            else None
        )

        self.stat_values["pending"].setText(str(len(pending)))
        self.stat_values["done_today"].setText(str(completed_today))
        self.stat_values["high_priority"].setText(str(high_priority))
        self.stat_values["focus_hours"].setText(f"~{len(pending)}h")
        self.subtitle_label.setText(
            f"{get_greeting_text(datetime.now())}. {len(pending)} task"
            f"{'' if len(pending) == 1 else 's'} are active right now."
        )

        self.refresh_focus_card(pending)
        self.render_pending_tasks(filtered_pending, pending, selected_task_id)

    def refresh_suggestion(self):
        suggestion = get_daily_suggestion(self.task_manager)
        if self.task_manager.list_pending_tasks():
            self.ai_heading_label.setText("Best next step")
        else:
            self.ai_heading_label.setText("Calm window")
        self.ai_text.setText(suggestion)

    def go_to_add_task(self):
        self.main_window.show_add_task_page()

    def go_to_money(self):
        self.main_window.show_money_page()

    def go_to_ai_chat(self):
        self.main_window.show_ai_chat_page()

    def set_active_filter(self, filter_name: str):
        self.active_filter = filter_name
        for name, button in self.filter_buttons.items():
            button.setChecked(name == filter_name)
        self.refresh_lists()

    def get_filtered_tasks(self, pending_tasks):
        if self.active_filter == "All":
            return pending_tasks
        return [
            task for task in pending_tasks
            if task.priority == self.active_filter
        ]

    def refresh_focus_card(self, pending_tasks):
        if not pending_tasks:
            self.current_focus_task_id = None
            self.focus_title_label.setText("Nothing urgent right now")
            self.focus_meta_label.setText("Clear board")
            self.focus_body_label.setText(
                "Use this quiet window to plan the week, review money, or add one small next step."
            )
            self.focus_open_btn.setText("Add task")
            self.focus_done_btn.setEnabled(False)
            return

        focus_task = min(
            pending_tasks,
            key=lambda task: (
                priority_rank(task.priority),
                task.date or datetime.max,
            ),
        )
        self.current_focus_task_id = focus_task.id
        self.focus_title_label.setText(focus_task.title)
        self.focus_meta_label.setText(
            f"{focus_task.priority} priority | Created {format_task_timestamp(focus_task.date)}"
        )
        self.focus_body_label.setText(format_task_preview(focus_task.description))
        self.focus_open_btn.setText("Open focus")
        self.focus_done_btn.setEnabled(True)

    def open_focus_task(self):
        if self.current_focus_task_id is None:
            self.go_to_add_task()
            return
        self.open_task_by_id(self.current_focus_task_id)

    def complete_focus_task(self):
        if self.current_focus_task_id is None:
            return
        self.mark_task_done_from_home(self.current_focus_task_id)

    def render_pending_tasks(self, tasks, all_pending_tasks, selected_task_id):
        self.pending_list.clear()
        self.task_rows = {}

        if not tasks:
            self.pending_list.hide()
            self.empty_state_card.show()
            if all_pending_tasks:
                self.empty_state_title.setText("No tasks match this filter")
                self.empty_state_body.setText(
                    "Try a different priority chip or switch back to All to see your full queue."
                )
                self.set_empty_state_action(
                    "Show all tasks",
                    lambda: self.set_active_filter("All"),
                )
            else:
                self.empty_state_title.setText("Your task list is clear")
                self.empty_state_body.setText(
                    "Add a task to get started, or enjoy the breathing room while the board is empty."
                )
                self.set_empty_state_action("Add task", self.go_to_add_task)
            return

        self.pending_list.show()
        self.empty_state_card.hide()
        self.reset_empty_state_action()

        for task in tasks:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, task.id)
            item.setSizeHint(QSize(0, 96))
            self.pending_list.addItem(item)

            task_card = TaskListCard(
                task=task,
                select_callback=lambda list_item=item: self.pending_list.setCurrentItem(list_item),
                open_callback=self.open_task_by_id,
                done_callback=self.mark_task_done_from_home,
            )
            self.pending_list.setItemWidget(item, task_card)
            self.task_rows[task.id] = task_card

        if selected_task_id is not None:
            self.select_task_in_list(selected_task_id)
        elif self.pending_list.count() > 0:
            self.pending_list.setCurrentRow(0)

        self.sync_task_card_selection()

    def reset_empty_state_action(self):
        self.set_empty_state_action("Add task", self.go_to_add_task)

    def set_empty_state_action(self, text: str, handler):
        self.empty_state_action_btn.setText(text)
        try:
            self.empty_state_action_btn.clicked.disconnect()
        except TypeError:
            pass
        self.empty_state_action_btn.clicked.connect(handler)

    def select_task_in_list(self, task_id: int):
        for index in range(self.pending_list.count()):
            item = self.pending_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == task_id:
                self.pending_list.setCurrentItem(item)
                return

    def sync_task_card_selection(self):
        current_item = self.pending_list.currentItem()
        current_task_id = (
            current_item.data(Qt.ItemDataRole.UserRole)
            if current_item is not None
            else None
        )
        for task_id, task_row in self.task_rows.items():
            task_row.set_selected(task_id == current_task_id)

    def open_task_by_id(self, task_id: int):
        task = next(
            (pending_task for pending_task in self.task_manager.list_pending_tasks() if pending_task.id == task_id),
            None,
        )
        if task is None:
            QMessageBox.warning(
                self,
                "Task not found",
                "That task is no longer available in the pending list.",
            )
            self.refresh_lists()
            return
        self.main_window.show_task_details_page(task)

    def mark_task_done_from_home(self, task_id: int):
        try:
            self.task_manager.mark_done(task_id)
        except AssistantDataError as exc:
            QMessageBox.warning(self, "Unable to update task", str(exc))
            self.refresh_lists()
            self.refresh_suggestion()
            return
        self.refresh_lists()
        self.refresh_suggestion()

    def view_selected_task(self, _item=None):
        current_item = self.pending_list.currentItem()
        if current_item is None:
            QMessageBox.information(
                self,
                "Select a task",
                "Choose a pending task first, then click 'View selected task'.",
            )
            return

        self.open_task_by_id(current_item.data(Qt.ItemDataRole.UserRole))

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
        self.priority_combo.addItems(list(TASK_PRIORITIES))
        apply_combo_popup_theme(self.priority_combo)
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
            QMessageBox.information(
                self,
                "Task title required",
                "Add a task title before saving.",
            )
            return
        description = self.details_edit.toPlainText().strip()
        priority = self.priority_combo.currentText()
        try:
            self.task_manager.add_task(title=title, description=description, priority=priority)
        except AssistantDataError as exc:
            QMessageBox.warning(self, "Unable to save task", str(exc))
            return
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

        try:
            self.task_manager.mark_done(self.current_task.id)
        except AssistantDataError as exc:
            QMessageBox.warning(self, "Unable to update task", str(exc))
            self.main_window.home_page.refresh_lists()
            self.main_window.home_page.refresh_suggestion()
            return
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
        self.selected_month = month_start()
        self.active_entry_filter = "All"
        self.entry_filter_buttons = {}
        self.editing_entry_id = None

        layout = create_page_layout(self)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        self.header_label = QLabel("Money")
        self.header_label.setObjectName("pageTitle")
        header_row.addWidget(self.header_label)
        header_row.addStretch(1)

        self.ai_chat_btn = QPushButton("Ask AI")
        self.ai_chat_btn.setObjectName("compactPrimaryButton")
        self.ai_chat_btn.clicked.connect(self.go_to_ai_chat)
        header_row.addWidget(self.ai_chat_btn)

        prev_month_btn = QPushButton("Previous")
        prev_month_btn.setObjectName("compactButton")
        prev_month_btn.clicked.connect(lambda: self.change_month(-1))
        header_row.addWidget(prev_month_btn)

        self.month_label = QLabel("")
        self.month_label.setObjectName("monthLabel")
        header_row.addWidget(self.month_label)

        next_month_btn = QPushButton("Next")
        next_month_btn.setObjectName("compactButton")
        next_month_btn.clicked.connect(lambda: self.change_month(1))
        header_row.addWidget(next_month_btn)
        layout.addLayout(header_row)

        self.subtitle_label = QLabel("")
        self.subtitle_label.setObjectName("pageSubtitle")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        money_stats, self.stat_values = create_stats_grid(
            [
                ("net_balance", "NET BALANCE", "focus"),
                ("salary", "INCOME", "money"),
                ("expenses", "EXPENSES", "expense"),
                ("emi", "EMI", "credit"),
                ("credit", "CREDIT", "credit"),
                ("owes_you", "OWES YOU", "owe"),
            ],
            columns=3,
        )
        layout.addLayout(money_stats)

        self.form_section_label = create_section_title("ADD MONEY ENTRY")
        layout.addWidget(self.form_section_label)

        form = QFormLayout()
        form.setVerticalSpacing(14)
        form.setHorizontalSpacing(18)

        self.type_combo = QComboBox()
        self.type_combo.addItems(list(MONEY_ENTRY_TYPES))
        apply_combo_popup_theme(self.type_combo)
        self.type_combo.currentTextChanged.connect(self.update_person_placeholder)
        form.addRow("Type:", self.type_combo)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 1_000_000)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setSingleStep(100)
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

        form_btn_row = QHBoxLayout()
        form_btn_row.setSpacing(10)
        self.save_entry_btn = QPushButton("Add entry")
        self.save_entry_btn.setObjectName("primaryButton")
        self.save_entry_btn.clicked.connect(self.save_entry)
        form_btn_row.addWidget(self.save_entry_btn)

        self.cancel_edit_btn = QPushButton("Cancel edit")
        self.cancel_edit_btn.setObjectName("ghostButton")
        self.cancel_edit_btn.clicked.connect(self.reset_form)
        self.cancel_edit_btn.hide()
        form_btn_row.addWidget(self.cancel_edit_btn)
        form_btn_row.addStretch(1)
        layout.addLayout(form_btn_row)

        entries_header = QHBoxLayout()
        entries_header.addWidget(create_section_title("RECENT ENTRIES"))
        entries_header.addStretch(1)
        layout.addLayout(entries_header)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)
        for filter_name in ("All", *MONEY_ENTRY_TYPES):
            button = QPushButton(filter_name)
            button.setObjectName("filterChip")
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, current_filter=filter_name: self.set_entry_filter(current_filter)
            )
            self.entry_filter_buttons[filter_name] = button
            filter_row.addWidget(button)
        self.entry_filter_buttons[self.active_entry_filter].setChecked(True)
        filter_row.addStretch(1)
        layout.addLayout(filter_row)

        self.entries_list = QListWidget()
        self.entries_list.setSpacing(4)
        self.entries_list.setMinimumHeight(170)
        layout.addWidget(self.entries_list)

        self.empty_state_card = QFrame()
        self.empty_state_card.setObjectName("emptyStateCard")
        empty_layout = QVBoxLayout()
        empty_layout.setContentsMargins(16, 14, 16, 14)
        empty_layout.setSpacing(6)
        self.empty_state_card.setLayout(empty_layout)

        self.empty_state_title = QLabel("")
        self.empty_state_title.setObjectName("emptyStateTitle")
        empty_layout.addWidget(self.empty_state_title)

        self.empty_state_body = QLabel("")
        self.empty_state_body.setObjectName("emptyStateBody")
        self.empty_state_body.setWordWrap(True)
        empty_layout.addWidget(self.empty_state_body)

        self.empty_state_action_btn = QPushButton("Add entry")
        self.empty_state_action_btn.setObjectName("compactPrimaryButton")
        empty_layout.addWidget(self.empty_state_action_btn)
        layout.addWidget(self.empty_state_card)

        back_btn = QPushButton("Back to Home")
        back_btn.setObjectName("ghostButton")
        back_btn.clicked.connect(self.go_back_home)
        layout.addWidget(back_btn)
        layout.addStretch(1)

        self.update_person_placeholder(self.type_combo.currentText())
        self.set_empty_state_action("Go to current month", self.reset_to_current_month)
        self.refresh_month_header()
        self.refresh_summary()
        self.refresh_entries()

    def refresh_month_header(self):
        self.month_label.setText(format_month_label(self.selected_month))
        self.subtitle_label.setText(
            f"Tracking entries saved in {format_month_label(self.selected_month)}."
        )

    def change_month(self, delta: int):
        self.selected_month = shift_month(self.selected_month, delta)
        self.refresh_month_header()
        self.reset_form()
        self.refresh_summary()
        self.refresh_entries()

    def reset_to_current_month(self):
        self.selected_month = month_start()
        self.refresh_month_header()
        self.refresh_summary()
        self.refresh_entries()

    def set_entry_filter(self, filter_name: str):
        self.active_entry_filter = filter_name
        for name, button in self.entry_filter_buttons.items():
            button.setChecked(name == filter_name)
        self.refresh_entries()

    def update_person_placeholder(self, entry_type: str):
        if entry_type in {"Given", "Taken"}:
            self.person_edit.setPlaceholderText("Person name")
        else:
            self.person_edit.setPlaceholderText("Optional")

    def save_entry(self):
        entry_type = self.type_combo.currentText()
        amount = float(self.amount_spin.value())
        note = self.note_edit.text().strip()
        person = self.person_edit.text().strip()
        if amount <= 0:
            QMessageBox.information(
                self,
                "Amount required",
                "Enter an amount greater than zero before saving.",
            )
            return

        try:
            if self.editing_entry_id is None:
                self.money_manager.add_entry(entry_type, amount, note, person)
                if self.selected_month != month_start():
                    self.selected_month = month_start()
                    self.refresh_month_header()
            else:
                self.money_manager.update_entry(self.editing_entry_id, entry_type, amount, note, person)
        except AssistantDataError as exc:
            QMessageBox.warning(self, "Unable to save entry", str(exc))
            self.refresh_entries()
            return

        self.reset_form()
        self.refresh_summary()
        self.refresh_entries()

    def begin_edit_entry(self, entry):
        self.editing_entry_id = entry.id
        self.form_section_label.setText("EDIT ENTRY")
        self.save_entry_btn.setText("Save changes")
        self.cancel_edit_btn.show()
        self.type_combo.setCurrentText(entry.entry_type)
        self.amount_spin.setValue(entry.amount)
        self.note_edit.setText(entry.note)
        self.person_edit.setText(entry.person)

    def reset_form(self):
        self.editing_entry_id = None
        self.form_section_label.setText("ADD MONEY ENTRY")
        self.save_entry_btn.setText("Add entry")
        self.cancel_edit_btn.hide()
        self.type_combo.setCurrentText("Income")
        self.update_person_placeholder("Income")
        self.amount_spin.setValue(0)
        self.note_edit.clear()
        self.person_edit.clear()

    def set_empty_state_action(self, text: str, handler):
        self.empty_state_action_btn.setText(text)
        try:
            self.empty_state_action_btn.clicked.disconnect()
        except TypeError:
            pass
        self.empty_state_action_btn.clicked.connect(handler)

    def delete_entry(self, entry):
        choice = QMessageBox.question(
            self,
            "Delete entry",
            f"Delete '{format_money_note(entry)}' from {entry.date.strftime('%d %b %Y')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if choice != QMessageBox.StandardButton.Yes:
            return

        try:
            self.money_manager.delete_entry(entry.id)
        except AssistantDataError as exc:
            QMessageBox.warning(self, "Unable to delete entry", str(exc))
            self.refresh_entries()
            return
        if self.editing_entry_id == entry.id:
            self.reset_form()
        self.refresh_summary()
        self.refresh_entries()

    def refresh_summary(self):
        summary = self.money_manager.compute_summary(
            year=self.selected_month.year,
            month=self.selected_month.month,
        )
        net_balance = summary["net_balance"]
        self.stat_values["net_balance"].setText(
            format_signed_currency(net_balance) if net_balance < 0 else format_currency(net_balance)
        )
        self.stat_values["salary"].setText(format_currency(summary["salary"]))
        self.stat_values["expenses"].setText(format_currency(summary["expenses"]))
        self.stat_values["emi"].setText(format_currency(summary["emi"]))
        self.stat_values["credit"].setText(format_currency(summary["credit"]))
        self.stat_values["owes_you"].setText(format_currency(summary["owes_you"]))

    def refresh_entries(self):
        self.entries_list.clear()
        filtered_type = None if self.active_entry_filter == "All" else self.active_entry_filter
        entries = self.money_manager.list_entries(
            year=self.selected_month.year,
            month=self.selected_month.month,
            entry_type=filtered_type,
        )

        if not entries:
            self.entries_list.hide()
            self.empty_state_card.show()
            if filtered_type is None:
                self.empty_state_title.setText("No entries for this month")
                self.empty_state_body.setText(
                    "Add a new entry to start tracking this month, or switch months to review earlier activity."
                )
                if self.selected_month == month_start():
                    self.set_empty_state_action("Add entry", self.reset_form)
                else:
                    self.set_empty_state_action("Go to current month", self.reset_to_current_month)
            else:
                self.empty_state_title.setText("No entries match this filter")
                self.empty_state_body.setText(
                    f"Try a different type chip or return to All to see everything in {format_month_label(self.selected_month)}."
                )
                self.set_empty_state_action("Show all entries", lambda: self.set_entry_filter("All"))
            return

        self.entries_list.show()
        self.empty_state_card.hide()
        self.set_empty_state_action("Go to current month", self.reset_to_current_month)

        for entry in entries:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 94))
            self.entries_list.addItem(item)
            entry_card = MoneyEntryCard(
                entry=entry,
                edit_callback=self.begin_edit_entry,
                delete_callback=self.delete_entry,
            )
            self.entries_list.setItemWidget(item, entry_card)

    def go_back_home(self):
        self.main_window.show_home_page()

    def go_to_ai_chat(self):
        self.main_window.show_ai_chat_page()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assistant Pro")
        self.resize(900, 600)
        self.setStyleSheet(APP_STYLESHEET)

        self.task_manager = TaskManager()
        self.money_manager = MoneyManager()

        self.stack = QStackedWidget()
        self.stack.setObjectName("pageStack")
        self.setCentralWidget(self.stack)

        self.home_page = HomePage(self, self.task_manager)
        self.add_task_page = AddTaskPage(self, self.task_manager)
        self.task_details_page = TaskDetailsPage(self, self.task_manager)
        self.money_page = MoneyPage(self, self.money_manager)
        self.ai_chat_page = AssistantChatPage(self, self.task_manager, self.money_manager)

        self.stack.addWidget(self.home_page)      # index 0
        self.stack.addWidget(self.add_task_page)  # index 1
        self.stack.addWidget(self.task_details_page)
        self.stack.addWidget(self.money_page)
        self.stack.addWidget(self.ai_chat_page)

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

    def show_ai_chat_page(self):
        self.ai_chat_page.prepare_page()
        self.stack.setCurrentWidget(self.ai_chat_page)
