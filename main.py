import sys
from PyQt6.QtWidgets import QApplication
from logging_conf import setup_logging
from app.ui import MainWindow
#ver 1.1.3
def main():
    setup_logging()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()