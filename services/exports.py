from __future__ import annotations

import csv
from io import StringIO
from typing import List, Dict

from openpyxl import Workbook

FIELDS = [
    "name",
    "email",
    "journal",
    "topic",
    "verified",
    "duplicate",
    "source_url",
    "timestamp",
]


def to_csv(records: List[Dict]) -> str:
    """Return CSV string for records including header."""
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FIELDS)
    writer.writeheader()
    for rec in records:
        writer.writerow({f: rec.get(f, "") for f in FIELDS})
    return buffer.getvalue()


def to_excel_file(records: List[Dict], path: str) -> None:
    """Write records to an Excel file at ``path``."""
    wb = Workbook()
    ws = wb.active
    ws.title = "data"
    ws.append(FIELDS)
    for rec in records:
        ws.append([rec.get(f, "") for f in FIELDS])
    wb.save(path)
