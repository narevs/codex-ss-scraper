import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.stats import StatsManager


def test_load_and_increment(tmp_path):
    path = tmp_path / "state.json"
    sm = StatsManager(path)
    sm.ensure_today_date()
    assert sm.data_today == 0
    sm.increment_data()
    sm.increment_pages(2)
    assert sm.data_today == 1
    assert sm.data_session == 1
    assert sm.pages_today == 2
    assert sm.pages_session == 2


def test_daily_reset(tmp_path):
    path = tmp_path / "state.json"
    sm = StatsManager(path)
    sm.ensure_today_date()
    sm.increment_data()
    sm.increment_pages()
    saved_date = sm.current_date
    # simulate next day
    sm.current_date = "1999-01-01"
    sm.save()
    sm.ensure_today_date()
    assert sm.data_today == 0
    assert sm.pages_today == 0
    assert sm.data_session == 1
    assert sm.pages_session == 1


def test_reset_session(tmp_path):
    path = tmp_path / "state.json"
    sm = StatsManager(path)
    sm.ensure_today_date()
    sm.increment_data()
    sm.increment_pages()
    sm.reset_session()
    assert sm.data_session == 0
    assert sm.pages_session == 0
    assert sm.data_today == 1
