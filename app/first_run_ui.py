"""
app/first_run_ui.py
--------------------
PyQt6 dialogs shown on first launch (setup wizard) and every later launch (login).
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class SetupWizard(QDialog):
    """
    First-run wizard: collects username + password (with confirm).
    On accept, exposes .username and .password.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Welcome — First Time Setup")
        self.setFixedWidth(420)
        self.setModal(True)

        self.username: str = ""
        self.password: str = ""

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Create Your Local Account")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        subtitle = QLabel(
            "This account protects your data on this device.\n"
            "Your password encrypts the local database — keep it safe."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # Username
        layout.addWidget(QLabel("Username"))
        self._username_input = QLineEdit()
        self._username_input.setPlaceholderText("Enter a username")
        layout.addWidget(self._username_input)

        # Password
        layout.addWidget(QLabel("Password"))
        self._password_input = QLineEdit()
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_input.setPlaceholderText("At least 8 characters")
        layout.addWidget(self._password_input)

        # Confirm password
        layout.addWidget(QLabel("Confirm Password"))
        self._confirm_input = QLineEdit()
        self._confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm_input.setPlaceholderText("Repeat your password")
        layout.addWidget(self._confirm_input)

        layout.addSpacing(8)

        # Buttons
        btn_row = QHBoxLayout()
        self._submit_btn = QPushButton("Create Account")
        self._submit_btn.setDefault(True)
        self._submit_btn.clicked.connect(self._on_submit)
        btn_row.addStretch()
        btn_row.addWidget(self._submit_btn)
        layout.addLayout(btn_row)

    def _on_submit(self) -> None:
        username = self._username_input.text().strip()
        password = self._password_input.text()
        confirm = self._confirm_input.text()

        if not username:
            QMessageBox.warning(self, "Validation", "Username cannot be empty.")
            return
        if len(password) < 8:
            QMessageBox.warning(self, "Validation", "Password must be at least 8 characters.")
            return
        if password != confirm:
            QMessageBox.warning(self, "Validation", "Passwords do not match.")
            return

        self.username = username
        self.password = password
        self.accept()


class LoginDialog(QDialog):
    """
    Login dialog shown on every subsequent launch.
    On accept, exposes .password.
    """

    def __init__(self, username: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Sign In")
        self.setFixedWidth(360)
        self.setModal(True)

        self.password: str = ""
        self._username = username

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel(f"Welcome back, {self._username}")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        layout.addWidget(QLabel("Password"))
        self._password_input = QLineEdit()
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_input.setPlaceholderText("Enter your password")
        self._password_input.returnPressed.connect(self._on_submit)
        layout.addWidget(self._password_input)

        layout.addSpacing(4)

        btn_row = QHBoxLayout()
        self._submit_btn = QPushButton("Sign In")
        self._submit_btn.setDefault(True)
        self._submit_btn.clicked.connect(self._on_submit)
        btn_row.addStretch()
        btn_row.addWidget(self._submit_btn)
        layout.addLayout(btn_row)

    def _on_submit(self) -> None:
        password = self._password_input.text()
        if not password:
            QMessageBox.warning(self, "Validation", "Please enter your password.")
            return
        self.password = password
        self.accept()
