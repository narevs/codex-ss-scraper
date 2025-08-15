from __future__ import annotations

from datetime import datetime


def normalize_email(email: str) -> str:
    """Normalize an email address to lowercase without surrounding spaces."""
    return email.strip().lower()


def current_timestamp() -> str:
    """Return an ISO formatted UTC timestamp."""
    return datetime.utcnow().isoformat()
