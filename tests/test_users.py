import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).resolve().parents[1]))

from auth import users


def test_user_crud(tmp_path):
    db = tmp_path / "auth.db"
    users.init_db(db)
    assert db.exists()
    assert users.list_users(db) == []

    user = {
        "email": "test@example.com",
        "expires_at": (datetime.utcnow() + timedelta(days=1)).date().isoformat(),
        "usage_limit": 5,
        "notes": "note",
    }
    users.upsert_user(db, user)
    rows = users.list_users(db)
    assert len(rows) == 1
    assert rows[0]["usage_limit"] == 5

    user["usage_limit"] = 10
    users.upsert_user(db, user)
    rows = users.list_users(db)
    assert rows[0]["usage_limit"] == 10

    users.delete_user(db, user["email"])
    assert users.list_users(db) == []
