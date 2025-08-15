"""Simple license/login dialog presented on startup.

The dialog collects an email address and license key.  Upon successful
verification the dialog is accepted, otherwise an inline error is shown.
"""

from __future__ import annotations

try:  # pragma: no cover - GUI elements are not exercised in tests
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QLineEdit,
        QLabel,
        QPushButton,
        QHBoxLayout,
    )
except Exception:  # pragma: no cover - allows import without Qt deps
    QDialog = QVBoxLayout = QLineEdit = QLabel = QPushButton = QHBoxLayout = object  # type: ignore

from auth.license import LicenseManager, LicenseError


class LoginDialog(QDialog):  # pragma: no cover - requires GUI
    def __init__(self, license_manager: LicenseManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("License Required")
        self.license_manager = license_manager

        layout = QVBoxLayout(self)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Email")
        layout.addWidget(self.email_edit)

        self.license_edit = QLineEdit()
        self.license_edit.setPlaceholderText("License Key")
        layout.addWidget(self.license_edit)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red")
        layout.addWidget(self.error_label)

        btn_layout = QHBoxLayout()
        verify_btn = QPushButton("Verify")
        quit_btn = QPushButton("Quit")
        btn_layout.addWidget(verify_btn)
        btn_layout.addWidget(quit_btn)
        layout.addLayout(btn_layout)

        verify_btn.clicked.connect(self._on_verify)
        quit_btn.clicked.connect(self.reject)

    def _on_verify(self):
        email = self.email_edit.text().strip()
        key = self.license_edit.text().strip()
        try:
            self.license_manager.register(email, key)
        except LicenseError as exc:
            self.error_label.setText(str(exc))
            return
        self.accept()


__all__ = ["LoginDialog"]

