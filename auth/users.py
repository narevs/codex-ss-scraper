"""User persistence helpers for Admin dialog."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

SCHEMA = (
    "CREATE TABLE IF NOT EXISTS users(" 
    "email TEXT PRIMARY KEY," 
    "expires_at TEXT NOT NULL," 
    "usage_limit INTEGER NULL," 
    "notes TEXT NULL," 
    "created_at TEXT NOT NULL," 
    "updated_at TEXT NOT NULL)"
)


def init_db(path: Path) -> None:
    """Initialize the SQLite database and ensure schema exists."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(SCHEMA)


def list_users(path: Path) -> list[dict]:
    """Return a list of all users."""
    path = Path(path)
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT email, expires_at, usage_limit, notes, created_at, updated_at FROM users ORDER BY email"
        ).fetchall()
        return [dict(r) for r in rows]


def upsert_user(path: Path, user: Dict[str, Optional[object]]) -> None:
    """Insert or update a user record."""
    path = Path(path)
    now = datetime.utcnow().isoformat()
    with sqlite3.connect(path) as conn:
        cur = conn.execute("SELECT created_at FROM users WHERE email=?", (user["email"],))
        row = cur.fetchone()
        if row:
            conn.execute(
                "UPDATE users SET expires_at=?, usage_limit=?, notes=?, updated_at=? WHERE email=?",
                (
                    user["expires_at"],
                    user.get("usage_limit"),
                    user.get("notes"),
                    now,
                    user["email"],
                ),
            )
        else:
            conn.execute(
                "INSERT INTO users(email, expires_at, usage_limit, notes, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                (
                    user["email"],
                    user["expires_at"],
                    user.get("usage_limit"),
                    user.get("notes"),
                    now,
                    now,
                ),
            )


def delete_user(path: Path, email: str) -> None:
    """Remove a user by email."""
    path = Path(path)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM users WHERE email=?", (email,))
