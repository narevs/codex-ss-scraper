"""Main application UI for SS Scraper."""
from __future__ import annotations

import json
import os
import asyncio
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime

from auth.license import LicenseManager, should_show_license_modal
from dialogs import LoginDialog, AdminDialog
from auth import users
from utils import link_collector, html as html_utils
from services.page_runner import PageRunner
from services import exports, stats

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
        QFileDialog,
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
        self.browser.load(html_utils.to_qurl(DEFAULT_HOME))
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
        self.export_csv_btn = QPushButton("Export CSV")
        self.export_excel_btn = QPushButton("Export Excel")
        self.copy_btn = QPushButton("Copy")
        self.clear_btn = QPushButton("Clear")
        self.export_csv_btn.clicked.connect(self.export_csv)  # type: ignore[attr-defined]
        self.export_excel_btn.clicked.connect(self.export_excel)  # type: ignore[attr-defined]
        self.copy_btn.clicked.connect(self.copy_records)  # type: ignore[attr-defined]
        self.clear_btn.clicked.connect(self.clear_records)  # type: ignore[attr-defined]
        opts_layout = QHBoxLayout()
        opts_layout.addWidget(self.export_csv_btn)
        opts_layout.addWidget(self.export_excel_btn)
        opts_layout.addWidget(self.copy_btn)
        opts_layout.addWidget(self.clear_btn)
        opts_widget = QWidget()
        opts_widget.setLayout(opts_layout)
        self.data_stats = QLabel("Data: Today 0 / Session 0")
        self.pages_stats = QLabel("Pages: Today 0 / Session 0")
        stats_layout = QVBoxLayout()
        stats_layout.addWidget(self.data_stats)
        stats_layout.addWidget(self.pages_stats)
        stats_widget = QWidget()
        stats_widget.setLayout(stats_layout)
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.email_list)
        right_layout.addWidget(opts_widget)
        right_layout.addWidget(stats_widget)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        layout = QHBoxLayout()
        layout.addWidget(self.url_list)
        layout.addWidget(middle_widget)
        layout.addWidget(right_widget)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        self.stats = stats.StatsManager(Path(__file__).parent / "data" / "state.json")
        self.stats.ensure_today_date()
        self.update_stats_labels()

        self.load_rules()

        if os.getenv("ADMIN_MODE") == "1":
            self._db_path = Path(__file__).parent / "data" / "auth.db"
            users.init_db(self._db_path)
            shortcut = QShortcut(QKeySequence("Ctrl+Alt+A"), self)
            shortcut.activated.connect(self.open_admin_dialog)

    def update_stats_labels(self):
        self.data_stats.setText(
            f"Data: Today {self.stats.data_today} / Session {self.stats.data_session}"
        )
        self.pages_stats.setText(
            f"Pages: Today {self.stats.pages_today} / Session {self.stats.pages_session}"
        )

    def export_csv(self):  # pragma: no cover - GUI
        if not self.records:
            return
        default = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", default, "CSV Files (*.csv)")
        if not path:
            return
        try:
            csv_text = exports.to_csv(self.records)
            Path(path).write_text(csv_text, encoding="utf-8")
        except Exception:
            pass

    def export_excel(self):  # pragma: no cover - GUI
        if not self.records:
            return
        default = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "Export Excel", default, "Excel Files (*.xlsx)")
        if not path:
            return
        try:
            exports.to_excel_file(self.records, path)
        except Exception:
            pass

    def copy_records(self):  # pragma: no cover - GUI
        if not self.records:
            return
        csv_text = exports.to_csv(self.records)
        QApplication.clipboard().setText(csv_text)

    def clear_records(self):  # pragma: no cover - GUI
        self.records.clear()
        self.email_list.clear()
        self.stats.reset_session()
        self.update_stats_labels()

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
        runner = PageRunner(
            self.browser,
            self.email_list.addItem,
            stats_manager=self.stats,
            stats_callback=self.update_stats_labels,
        )
        asyncio.run(runner.run_urls(urls))
        self.records = runner.records
        self.update_stats_labels()
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
