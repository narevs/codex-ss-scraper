import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ss_ui import DEFAULT_HOME


def test_default_homepage_is_google():
    assert DEFAULT_HOME == "https://www.google.com/"
