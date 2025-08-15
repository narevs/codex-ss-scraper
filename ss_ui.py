"""Main application UI for SS Scraper."""
from __future__ import annotations

import json
import os
from pathlib import Path

from auth.license import LicenseManager, should_show_license_modal
from dialogs import LoginDialog, AdminDialog
from auth import users

DEFAULT_HOME = "https://www.google.com/"
RULES_DIR = Path(__file__).parent / "rules"

try:
    from PyQt6.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QListWidget,
        QMainWindow,
        QVBoxLayout,
        QWidget,
        QShortcut,
    )
    from PyQt6.QtGui import QKeySequence
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except Exception:  # pragma: no cover - allows import without Qt deps
    QApplication = QMainWindow = QHBoxLayout = QVBoxLayout = QWidget = QListWidget = QWebEngineView = QShortcut = object  # type: ignore
    QKeySequence = None  # type: ignore


class SSMainWindow(QMainWindow if QMainWindow else object):
    """Very small 3-panel UI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SS Scraper")
        self.resize(1200, 800)

        # Left panel
        self.url_list = QListWidget()

        # Middle panel
        self.browser = QWebEngineView()
        self.browser.load(DEFAULT_HOME)
        middle_layout = QVBoxLayout()
        middle_layout.addWidget(self.browser)
        middle_widget = QWidget()
        middle_widget.setLayout(middle_layout)

        # Right panel
        self.email_list = QListWidget()

        layout = QHBoxLayout()
        layout.addWidget(self.url_list)
        layout.addWidget(middle_widget)
        layout.addWidget(self.email_list)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        self.load_rules()

        if os.getenv("ADMIN_MODE") == "1":
            self._db_path = Path(__file__).parent / "data" / "auth.db"
            users.init_db(self._db_path)
            shortcut = QShortcut(QKeySequence("Ctrl+Alt+A"), self)
            shortcut.activated.connect(self.open_admin_dialog)

    def load_rules(self):
        rule_path = RULES_DIR / "popular.json"
        if rule_path.exists():
            data = json.loads(rule_path.read_text())
            self.popular_sites = data.get("sites", [])
        else:
            self.popular_sites = []

    def open_admin_dialog(self):  # pragma: no cover - GUI
        dlg = AdminDialog(self._db_path, self)
        dlg.exec()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    lm = LicenseManager()
    if should_show_license_modal(lm.config_path):
        dlg = LoginDialog(lm)
        if dlg.exec() != 1:  # QDialog.Accepted
            sys.exit(0)

    win = SSMainWindow()
    win.show()
    sys.exit(app.exec())
