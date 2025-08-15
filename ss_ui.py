"""Main application UI for SS Scraper."""
from __future__ import annotations

import json
import os
import asyncio
from pathlib import Path
from urllib.parse import urlparse

from auth.license import LicenseManager, should_show_license_modal
from dialogs import LoginDialog, AdminDialog
from auth import users
from utils import link_collector
from services.page_runner import PageRunner

DEFAULT_HOME = "https://www.google.com/"
RULES_DIR = Path(__file__).parent / "rules"

try:
    from PyQt6.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QMainWindow,
        QPushButton,
        QVBoxLayout,
        QWidget,
        QShortcut,
    )
    from PyQt6.QtGui import QKeySequence
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except Exception:  # pragma: no cover - allows import without Qt deps
    QApplication = QMainWindow = QHBoxLayout = QVBoxLayout = QWidget = QListWidget = QWebEngineView = QShortcut = QLabel = QPushButton = object  # type: ignore
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
        self.scrape_btn = QPushButton("Scrape Links")
        self.start_btn = QPushButton("Start")
        self.status_label = QLabel("")
        self.scrape_btn.clicked.connect(self.scrape_links)  # type: ignore[attr-defined]
        self.start_btn.clicked.connect(self.start_processing)  # type: ignore[attr-defined]
        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(self.scrape_btn)
        ctrl_layout.addWidget(self.start_btn)
        ctrl_layout.addWidget(self.status_label)
        ctrl_widget = QWidget()
        ctrl_widget.setLayout(ctrl_layout)
        middle_layout = QVBoxLayout()
        middle_layout.addWidget(ctrl_widget)
        middle_layout.addWidget(self.browser)
        middle_widget = QWidget()
        middle_widget.setLayout(middle_layout)

        # Right panel
        self.email_list = QListWidget()
        self.records: list[dict] = []

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

    def scrape_links(self):  # pragma: no cover - GUI heavy
        self.scrape_btn.setEnabled(False)
        cap = 50
        page_url = self.browser.url().toString()
        host = urlparse(page_url).hostname or ""
        link_collector.CURRENT_VIEW = self.browser

        def update_status(collected: int, total: int):
            self.status_label.setText(f"Collected {collected}/{total} links")

        links = link_collector.collect_links(page_url, None, host, cap, update_status)
        if links:
            self.url_list.addItems(links)
        self.scrape_btn.setEnabled(True)

    def start_processing(self):  # pragma: no cover - GUI heavy
        urls = [self.url_list.item(i).text() for i in range(self.url_list.count())]
        if not urls:
            return
        self.start_btn.setEnabled(False)
        self.scrape_btn.setEnabled(False)
        runner = PageRunner(self.browser, self.email_list.addItem)
        asyncio.run(runner.run_urls(urls))
        self.records = runner.records
        self.start_btn.setEnabled(True)
        self.scrape_btn.setEnabled(True)


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
