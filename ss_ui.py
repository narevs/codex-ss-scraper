"""Main application UI for SS Scraper."""
from __future__ import annotations

import json
from pathlib import Path

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
    )
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except Exception:  # pragma: no cover - allows import without Qt deps
    QApplication = QMainWindow = QHBoxLayout = QVBoxLayout = QWidget = QListWidget = QWebEngineView = None


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

    def load_rules(self):
        rule_path = RULES_DIR / "popular.json"
        if rule_path.exists():
            data = json.loads(rule_path.read_text())
            self.popular_sites = data.get("sites", [])
        else:
            self.popular_sites = []


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    win = SSMainWindow()
    win.show()
    sys.exit(app.exec())
