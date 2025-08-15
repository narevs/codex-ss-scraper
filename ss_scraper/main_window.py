"""Main window for the Scholar Summit Email Scraper.

The implementation follows the 3‑panel design described in the project
specification.  Only a small subset of the overall functionality is
required for the unit tests executed in this kata, however the structure
is representative of the real application.
"""

from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List

from PyQt6.QtCore import QSettings, Qt, QUrl
from PyQt6.QtGui import QAction, QCloseEvent, QGuiApplication
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from bs4 import BeautifulSoup

from .utils import to_qurl, is_same_host, navigate, deduplicate

HOME_URL = "https://www.google.com/"


@dataclass
class Record:
    """Representation of a single extracted email record."""

    name: str
    email: str
    journal: str
    topic: str
    verified: bool
    duplicate: bool
    source_url: str
    timestamp: str


class MainWindow(QMainWindow):
    """Main application window implementing the 3‑panel UI."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Scholar Summit Email Scraper")

        self.settings = QSettings("ScholarSummit", "EmailScraper")

        self.records: List[Record] = []
        self.session_emails = set()
        self.stats: Dict[str, int] = {
            "data_today": 0,
            "data_session": 0,
            "pages_today": 0,
            "pages_session": 0,
        }
        self.today = date.today()

        self._build_ui()
        self._load_rules()
        self._restore_state()

        # Home page
        navigate(self.web, to_qurl(HOME_URL))

    # ------------------------------------------------------------------
    # UI construction helpers
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)

        # Header row 1: address bar
        self.address = QLineEdit(self)
        self.address.returnPressed.connect(self.on_open)
        outer.addWidget(self.address)

        # Header row 2: navigation + rule/site controls
        nav_layout = QHBoxLayout()
        outer.addLayout(nav_layout)

        self.back_btn = QPushButton("\u25C0", self)
        self.back_btn.clicked.connect(self.web.back)
        nav_layout.addWidget(self.back_btn)

        self.forward_btn = QPushButton("\u25B6", self)
        self.forward_btn.clicked.connect(self.web.forward)
        nav_layout.addWidget(self.forward_btn)

        self.reload_btn = QPushButton("\u27f3", self)
        self.reload_btn.clicked.connect(self.web.reload)
        nav_layout.addWidget(self.reload_btn)

        self.home_btn = QPushButton("\u2302", self)
        self.home_btn.clicked.connect(self.on_home)
        nav_layout.addWidget(self.home_btn)

        nav_layout.addSpacing(12)

        self.rule_combo = QComboBox(self)
        self.rule_combo.currentTextChanged.connect(self.on_rule_changed)
        nav_layout.addWidget(self.rule_combo)

        self.site_combo = QComboBox(self)
        self.site_combo.currentTextChanged.connect(self.on_site_changed)
        nav_layout.addWidget(self.site_combo)

        self.open_btn = QPushButton("Open", self)
        self.open_btn.clicked.connect(self.on_open)
        nav_layout.addWidget(self.open_btn)

        self.n_edit = QLineEdit(self)
        self.n_edit.setPlaceholderText("N")
        self.n_edit.setFixedWidth(40)
        nav_layout.addWidget(self.n_edit)

        self.scrape_links_btn = QPushButton("Scrape Links", self)
        self.scrape_links_btn.clicked.connect(self.on_scrape_links)
        nav_layout.addWidget(self.scrape_links_btn)

        # Main splitter with three panels
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        outer.addWidget(splitter)
        self.splitter = splitter

        # Left panel -----------------------------------------------------
        left_widget = QWidget(self)
        left_layout = QVBoxLayout(left_widget)
        splitter.addWidget(left_widget)

        paste_toolbar = QToolBar(self)
        paste_btn = QToolButton(self)
        paste_btn.setText("Paste ▾")
        paste_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        paste_menu = QMenu(paste_btn)
        self.paste_action = QAction("Paste", paste_menu)
        self.paste_action.triggered.connect(self.on_paste_clipboard)
        paste_menu.addAction(self.paste_action)
        self.split_action = QAction("Split", paste_menu)
        self.split_action.triggered.connect(self.on_split_queue)
        paste_menu.addAction(self.split_action)
        self.dedup_action = QAction("Dedup", paste_menu)
        self.dedup_action.triggered.connect(self.on_dedup_queue)
        paste_menu.addAction(self.dedup_action)
        self.import_action = QAction("Import", paste_menu)
        self.import_action.triggered.connect(self.on_import_queue)
        paste_menu.addAction(self.import_action)
        paste_btn.setMenu(paste_menu)
        paste_toolbar.addWidget(paste_btn)
        left_layout.addWidget(paste_toolbar)

        self.prefix_edit = QLineEdit(self)
        self.prefix_edit.setPlaceholderText("Prefix Text")
        left_layout.addWidget(self.prefix_edit)

        self.queue_list = QListWidget(self)
        self.queue_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.queue_list.customContextMenuRequested.connect(self.on_queue_menu)
        left_layout.addWidget(self.queue_list)

        footer = QHBoxLayout()
        left_layout.addLayout(footer)
        for text, handler in [
            ("Save", self.on_save_queue),
            ("Prev", self.on_prev_queue),
            ("Load", self.on_load_queue),
            ("Next", self.on_next_queue),
            ("Clear", self.on_clear_queue),
            ("Scrape", self.on_scrape_queue),
        ]:
            btn = QPushButton(text, self)
            btn.clicked.connect(handler)
            footer.addWidget(btn)

        # Middle panel ---------------------------------------------------
        self.web = QWebEngineView(self)
        splitter.addWidget(self.web)
        self.web.urlChanged.connect(self.on_url_changed)
        self.web.loadFinished.connect(self.on_page_loaded)

        # Right panel ----------------------------------------------------
        right_widget = QWidget(self)
        right_layout = QVBoxLayout(right_widget)
        splitter.addWidget(right_widget)

        self.data_table = QTableWidget(self)
        self.data_table.setColumnCount(1)
        self.data_table.setHorizontalHeaderLabels(["Email"])
        self.data_table.horizontalHeader().setStretchLastSection(True)
        right_layout.addWidget(self.data_table)

        options_layout = QHBoxLayout()
        right_layout.addLayout(options_layout)
        self.export_csv_btn = QPushButton("Export CSV", self)
        self.export_csv_btn.clicked.connect(self.on_export_csv)
        options_layout.addWidget(self.export_csv_btn)
        self.export_xlsx_btn = QPushButton("Export Excel", self)
        self.export_xlsx_btn.clicked.connect(self.on_export_xlsx)
        options_layout.addWidget(self.export_xlsx_btn)
        self.copy_btn = QPushButton("Copy", self)
        self.copy_btn.clicked.connect(self.on_copy_emails)
        options_layout.addWidget(self.copy_btn)

        self.clear_data_btn = QPushButton("Clear", self)
        self.clear_data_btn.clicked.connect(self.on_clear_data)
        right_layout.addWidget(self.clear_data_btn)

        stats_group = QGroupBox("Stats", self)
        stats_layout = QFormLayout(stats_group)
        self.data_today_lbl = QLabel("0", self)
        self.data_session_lbl = QLabel("0", self)
        self.pages_today_lbl = QLabel("0", self)
        self.pages_session_lbl = QLabel("0", self)
        stats_layout.addRow("Data Collected Today", self.data_today_lbl)
        stats_layout.addRow("Data Collected Session", self.data_session_lbl)
        stats_layout.addRow("Pages Visited Today", self.pages_today_lbl)
        stats_layout.addRow("Pages Visited Session", self.pages_session_lbl)
        right_layout.addWidget(stats_group)

        splitter.setSizes([320, 900, 360])

    # ------------------------------------------------------------------
    # Settings ---------------------------------------------------------
    def _restore_state(self) -> None:
        if geometry := self.settings.value("window/geometry"):
            self.restoreGeometry(geometry)
        if sizes := self.settings.value("window/splitter_sizes"):
            self.splitter.setSizes([int(x) for x in sizes])
        self.rule_combo.setCurrentText(self.settings.value("rule", ""))
        self.site_combo.setCurrentText(self.settings.value("site", ""))
        self.n_edit.setText(self.settings.value("n", ""))

    def _save_state(self) -> None:
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("window/splitter_sizes", self.splitter.sizes())
        self.settings.setValue("rule", self.rule_combo.currentText())
        self.settings.setValue("site", self.site_combo.currentText())
        self.settings.setValue("n", self.n_edit.text())

    # ------------------------------------------------------------------
    # Rules ------------------------------------------------------------
    def _load_rules(self) -> None:
        rules_path = Path(__file__).with_name("..") / "rules" / "sites.json"
        rules_path = rules_path.resolve()
        self.rules: Dict[str, List[Dict[str, str]]] = {}
        try:
            with open(rules_path, "r", encoding="utf8") as fh:
                data = json.load(fh)
        except Exception as exc:  # pragma: no cover - defensive
            QMessageBox.critical(self, "Rules", f"Failed to load rules: {exc}")
            data = {}
        for rule in data.get("rules", []):
            self.rules[rule["name"]] = rule["sites"]
        self.rule_combo.addItems(self.rules.keys())

    def on_rule_changed(self, rule: str) -> None:
        self.site_combo.clear()
        for site in self.rules.get(rule, []):
            self.site_combo.addItem(site["name"], site)

    def on_site_changed(self, site_name: str) -> None:
        site = self.site_combo.currentData()
        if site:
            url = to_qurl(site["url"])
            navigate(self.web, url)

    # ------------------------------------------------------------------
    # Navigation -------------------------------------------------------
    def on_open(self) -> None:
        url = to_qurl(self.address.text())
        if url.isEmpty():
            return
        navigate(self.web, url)

    def on_home(self) -> None:
        navigate(self.web, to_qurl(HOME_URL))

    def on_url_changed(self, url: QUrl) -> None:
        self.address.setText(url.toString())

    # ------------------------------------------------------------------
    # Queue management -------------------------------------------------
    def on_paste_clipboard(self) -> None:
        text = QGuiApplication.clipboard().text()
        if text:
            self.queue_list.addItem(text.strip())

    def on_split_queue(self) -> None:
        if not self.queue_list.count():
            return
        items = [self.queue_list.item(i).text() for i in range(self.queue_list.count())]
        self.queue_list.clear()
        for item in items:
            for part in re.split(r"[\n,\s]+", item):
                part = part.strip()
                if part:
                    self.queue_list.addItem(part)

    def on_dedup_queue(self) -> None:
        items = [self.queue_list.item(i).text() for i in range(self.queue_list.count())]
        self.queue_list.clear()
        for url in deduplicate(items):
            self.queue_list.addItem(url)

    def on_import_queue(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import URLs", "", "Text (*.txt *.csv)")
        if not path:
            return
        with open(path, "r", encoding="utf8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    self.queue_list.addItem(line)

    def on_queue_menu(self, pos) -> None:
        item = self.queue_list.itemAt(pos)
        menu = QMenu(self)
        open_act = QAction("Open", menu)
        remove_act = QAction("Remove", menu)
        clear_act = QAction("Clear", menu)
        if item:
            open_act.triggered.connect(lambda: self.on_open_item(item))
            remove_act.triggered.connect(lambda: self.queue_list.takeItem(self.queue_list.row(item)))
        clear_act.triggered.connect(self.queue_list.clear)
        menu.addAction(open_act)
        menu.addAction(remove_act)
        menu.addAction(clear_act)
        menu.exec(self.queue_list.mapToGlobal(pos))

    def on_open_item(self, item: QListWidgetItem) -> None:
        url = to_qurl(item.text())
        if url.isEmpty():
            return
        navigate(self.web, url)

    def on_save_queue(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Queue", "queue.json", "JSON (*.json)")
        if not path:
            return
        items = [self.queue_list.item(i).text() for i in range(self.queue_list.count())]
        with open(path, "w", encoding="utf8") as fh:
            json.dump(items, fh, indent=2)

    def on_load_queue(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load Queue", "", "JSON (*.json)")
        if not path:
            return
        self.queue_list.clear()
        with open(path, "r", encoding="utf8") as fh:
            for url in json.load(fh):
                self.queue_list.addItem(url)

    def on_prev_queue(self) -> None:  # pragma: no cover - UI convenience
        row = self.queue_list.currentRow()
        if row > 0:
            self.queue_list.setCurrentRow(row - 1)

    def on_next_queue(self) -> None:  # pragma: no cover - UI convenience
        row = self.queue_list.currentRow()
        if row < self.queue_list.count() - 1:
            self.queue_list.setCurrentRow(row + 1)

    def on_clear_queue(self) -> None:
        self.queue_list.clear()

    def on_scrape_queue(self) -> None:
        if self.queue_list.count() == 0:
            return
        self.current_queue_index = 0
        self._process_queue_item()

    def _process_queue_item(self) -> None:
        if self.current_queue_index >= self.queue_list.count():
            return
        item = self.queue_list.item(self.current_queue_index)
        qurl = to_qurl(item.text())
        if qurl.isEmpty():
            self.current_queue_index += 1
            self._process_queue_item()
            return
        navigate(self.web, qurl)
        self.current_queue_index += 1

    # ------------------------------------------------------------------
    # Scrape links -----------------------------------------------------
    def on_scrape_links(self) -> None:
        n_text = self.n_edit.text().strip()
        n = int(n_text) if n_text.isdigit() else 50
        current_site = self.site_combo.currentData()
        if not current_site:
            return

        def handle_html(html: str) -> None:
            soup = BeautifulSoup(html, "html.parser")
            links: List[str] = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                full = QUrl.fromUserInput(href).toString()
                if is_same_host(full, current_site["url"]):
                    links.append(full)
                if len(links) >= n:
                    break
            for url in deduplicate(links):
                if not any(self.queue_list.item(i).text() == url for i in range(self.queue_list.count())):
                    self.queue_list.addItem(url)

        self.web.page().toHtml(handle_html)

    # ------------------------------------------------------------------
    # Page load / email extraction -------------------------------------
    def on_page_loaded(self, ok: bool) -> None:
        if not ok:
            return
        self.stats["pages_session"] += 1
        if date.today() == self.today:
            self.stats["pages_today"] += 1
        else:
            self.today = date.today()
            self.stats["pages_today"] = 1
            self.stats["data_today"] = 0
        self._update_stats()

        def handle_html(html: str) -> None:
            url = self.web.url().toString()
            self._extract_from_html(html, url)

        self.web.page().toHtml(handle_html)

    def _extract_from_html(self, html: str, source_url: str) -> None:
        emails = []
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.lower().startswith("mailto:"):
                email = href[7:]
                emails.append(email)
        text = soup.get_text("\n")
        for email in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
            emails.append(email)

        unique: List[str] = []
        seen = set()
        for e in emails:
            el = e.lower()
            if el not in seen:
                seen.add(el)
                unique.append(e)
        for email in unique:
            record = Record(
                name="",
                email=email,
                journal=self.site_combo.currentText() or "",
                topic="",
                verified=False,
                duplicate=email.lower() in self.session_emails,
                source_url=source_url,
                timestamp=datetime.utcnow().isoformat(),
            )
            self.records.append(record)
            if email.lower() not in self.session_emails:
                self.session_emails.add(email.lower())
            row = self.data_table.rowCount()
            self.data_table.insertRow(row)
            self.data_table.setItem(row, 0, QTableWidgetItem(email))
            self.stats["data_session"] += 1
            if date.today() == self.today:
                self.stats["data_today"] += 1
            self._update_stats()

        # Continue queue processing if running
        if hasattr(self, "current_queue_index"):
            self._process_queue_item()

    # ------------------------------------------------------------------
    def on_export_csv(self) -> None:
        if not self.records:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "data.csv", "CSV (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(asdict(self.records[0]).keys()))
            writer.writeheader()
            for r in self.records:
                writer.writerow(asdict(r))

    def on_export_xlsx(self) -> None:
        try:
            import openpyxl
        except Exception as exc:  # pragma: no cover - optional dependency
            QMessageBox.warning(self, "Export", f"openpyxl not available: {exc}")
            return
        if not self.records:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Excel", "data.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(list(asdict(self.records[0]).keys()))
        for r in self.records:
            ws.append(list(asdict(r).values()))
        wb.save(path)

    def on_copy_emails(self) -> None:
        emails = [self.data_table.item(r, 0).text() for r in range(self.data_table.rowCount())]
        QGuiApplication.clipboard().setText("\n".join(emails))

    def on_clear_data(self) -> None:
        self.records.clear()
        self.data_table.setRowCount(0)
        self.session_emails.clear()
        self.stats["data_session"] = 0
        self.stats["data_today"] = 0
        self._update_stats()

    # ------------------------------------------------------------------
    def _update_stats(self) -> None:
        self.data_today_lbl.setText(str(self.stats["data_today"]))
        self.data_session_lbl.setText(str(self.stats["data_session"]))
        self.pages_today_lbl.setText(str(self.stats["pages_today"]))
        self.pages_session_lbl.setText(str(self.stats["pages_session"]))

    # ------------------------------------------------------------------
    def closeEvent(self, event: QCloseEvent) -> None:  # pragma: no cover - GUI
        self._save_state()
        super().closeEvent(event)


# ----------------------------------------------------------------------
def main() -> None:  # pragma: no cover - manual execution only
    app = QApplication([])
    win = MainWindow()
    win.show()
    app.exec()


if __name__ == "__main__":  # pragma: no cover
    main()
