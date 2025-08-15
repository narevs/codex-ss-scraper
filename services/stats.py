from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


@dataclass
class StatsManager:
    path: Path
    data_today: int = 0
    data_session: int = 0
    pages_today: int = 0
    pages_session: int = 0
    current_date: str = ""

    def load(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
            except Exception:
                data = {}
        else:
            data = {}
        today = date.today().isoformat()
        self.current_date = data.get("date", today)
        self.data_today = data.get("data_today", 0)
        self.data_session = data.get("data_session", 0)
        self.pages_today = data.get("pages_today", 0)
        self.pages_session = data.get("pages_session", 0)
        if self.current_date != today:
            self.current_date = today
            self.data_today = 0
            self.pages_today = 0
        self.save()

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "date": self.current_date or date.today().isoformat(),
                "data_today": self.data_today,
                "data_session": self.data_session,
                "pages_today": self.pages_today,
                "pages_session": self.pages_session,
            }
            self.path.write_text(json.dumps(data))
        except Exception:
            pass

    def ensure_today_date(self) -> None:
        self.load()

    def increment_data(self, new_count: int = 1) -> None:
        self.data_today += new_count
        self.data_session += new_count
        self.save()

    def increment_pages(self, new_count: int = 1) -> None:
        self.pages_today += new_count
        self.pages_session += new_count
        self.save()

    def reset_session(self) -> None:
        self.data_session = 0
        self.pages_session = 0
        self.save()
