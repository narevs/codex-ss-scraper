"""Admin dialog for managing licensed users."""
from __future__ import annotations

import re
import datetime as _dt
from pathlib import Path

try:  # pragma: no cover - GUI elements are not exercised in tests
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLineEdit,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QMessageBox,
        QFormLayout,
        QDialogButtonBox,
    )
except Exception:  # pragma: no cover
    QDialog = QVBoxLayout = QHBoxLayout = QLineEdit = QPushButton = QTableWidget = QTableWidgetItem = QMessageBox = QFormLayout = QDialogButtonBox = object  # type: ignore

from auth import users as user_store


class AdminDialog(QDialog):  # pragma: no cover - GUI heavy
    def __init__(self, db_path: Path, parent=None):
        super().__init__(parent)
        self.db_path = Path(db_path)
        user_store.init_db(self.db_path)
        self.setWindowTitle("Admin - Users")

        layout = QVBoxLayout(self)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search")
        layout.addWidget(self.search_edit)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "Email",
            "Expires At",
            "Usage Limit",
            "Notes",
        ])
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        edit_btn = QPushButton("Edit")
        del_btn = QPushButton("Delete")
        close_btn = QPushButton("Close")
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.search_edit.textChanged.connect(self._filter)
        add_btn.clicked.connect(self._add)
        edit_btn.clicked.connect(self._edit)
        del_btn.clicked.connect(self._delete)
        close_btn.clicked.connect(self.accept)

        self._refresh()

    def _refresh(self):
        rows = user_store.list_users(self.db_path)
        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(r["email"]))
            self.table.setItem(row, 1, QTableWidgetItem(r["expires_at"]))
            usage = "" if r["usage_limit"] is None else str(r["usage_limit"])
            self.table.setItem(row, 2, QTableWidgetItem(usage))
            self.table.setItem(row, 3, QTableWidgetItem(r.get("notes") or ""))

    def _filter(self, text: str) -> None:
        text = text.lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            self.table.setRowHidden(row, text not in item.text().lower())

    def _add(self):
        data = self._user_form()
        if not data:
            return
        existing = [u for u in user_store.list_users(self.db_path) if u["email"] == data["email"]]
        if existing:
            QMessageBox.warning(self, "Error", "Email already exists")
            return
        user_store.upsert_user(self.db_path, data)
        self._refresh()

    def _edit(self):
        row = self.table.currentRow()
        if row < 0:
            return
        email = self.table.item(row, 0).text()
        users = user_store.list_users(self.db_path)
        data = next((u for u in users if u["email"] == email), None)
        if not data:
            return
        new_data = self._user_form(data)
        if not new_data:
            return
        user_store.upsert_user(self.db_path, new_data)
        self._refresh()

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            return
        email = self.table.item(row, 0).text()
        user_store.delete_user(self.db_path, email)
        self._refresh()

    def _user_form(self, user: dict | None = None) -> dict | None:
        dlg = QDialog(self)
        dlg.setWindowTitle("User")
        form = QFormLayout(dlg)

        email_edit = QLineEdit(user.get("email", "") if user else "")
        exp_edit = QLineEdit(user.get("expires_at", "") if user else "")
        usage_edit = QLineEdit("" if not user or user.get("usage_limit") is None else str(user.get("usage_limit")))
        notes_edit = QLineEdit(user.get("notes", "") if user else "")

        form.addRow("Email", email_edit)
        form.addRow("Expires At", exp_edit)
        form.addRow("Usage Limit", usage_edit)
        form.addRow("Notes", notes_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        form.addRow(buttons)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None

        email = email_edit.text().strip()
        expires_at = exp_edit.text().strip()
        usage_txt = usage_edit.text().strip()
        notes = notes_edit.text().strip() or None

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            QMessageBox.warning(self, "Error", "Invalid email format")
            return None
        try:
            exp_date = _dt.date.fromisoformat(expires_at)
            if exp_date <= _dt.date.today():
                raise ValueError
        except Exception:
            QMessageBox.warning(self, "Error", "Invalid expires_at date")
            return None

        usage = None
        if usage_txt:
            if not usage_txt.isdigit():
                QMessageBox.warning(self, "Error", "Usage limit must be an integer")
                return None
            usage = int(usage_txt)

        return {
            "email": email,
            "expires_at": expires_at,
            "usage_limit": usage,
            "notes": notes,
        }


__all__ = ["AdminDialog"]
