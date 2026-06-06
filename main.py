"""main.py — application entry point.

Startup flow
~~~~~~~~~~~~
1. Check APP_DATA_DIR for setup marker + credentials file.
2a. First run  → show SetupWizard, create credentials + encrypted DB.
2b. Later run  → show LoginDialog, verify password, unlock encrypted DB.
3. Hand the derived DB key to SQLiteStorage so the database is opened
   with the correct SQLCipher key.
4. Launch MainWindow as normal.
pyinstaller --onefile --windowed \
  --name "shikhars planner assistant" \
  --icon 26.png \
  --exclude-module PyQt5 \
  --exclude-module PySide2 \
  --exclude-module PySide6 \
  main.py
"""

import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from logging_conf import setup_logging
from config import CREDENTIALS_FILE, SETUP_MARKER
from app.auth import AuthManager
from app.first_run_ui import SetupWizard, LoginDialog
from app.ui import MainWindow

# ver 2.0.0 — first-run setup + encrypted DB


def main() -> None:
    setup_logging()
    app = QApplication(sys.argv)

    auth = AuthManager(
        credentials_file=CREDENTIALS_FILE,
        setup_marker=SETUP_MARKER,
    )

    db_key: str = ""

    if auth.is_first_run():
        # ── Phase 2: first-run setup wizard ────────────────────────────────
        wizard = SetupWizard()
        if wizard.exec() != SetupWizard.DialogCode.Accepted:
            # User closed the wizard without completing setup → exit cleanly
            sys.exit(0)

        try:
            db_key = auth.setup(wizard.username, wizard.password)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(None, "Setup failed", str(exc))
            sys.exit(1)

    else:
        # ── Phase 2: login on every subsequent launch ───────────────────────
        username = auth.get_username()
        max_attempts = 5

        for attempt in range(1, max_attempts + 1):
            dialog = LoginDialog(username=username)
            if dialog.exec() != LoginDialog.DialogCode.Accepted:
                sys.exit(0)  # User closed the login dialog

            db_key = auth.login(dialog.password)
            if db_key is not None:
                break

            remaining = max_attempts - attempt
            if remaining > 0:
                QMessageBox.warning(
                    None,
                    "Incorrect password",
                    f"Wrong password. {remaining} attempt(s) remaining.",
                )
            else:
                QMessageBox.critical(
                    None,
                    "Access denied",
                    "Too many failed attempts. The application will now close.",
                )
                sys.exit(1)

    # ── Phase 3: launch main window, passing the DB key ────────────────────
    window = MainWindow(db_key=db_key)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
