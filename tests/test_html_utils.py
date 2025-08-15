import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

def test_to_qurl_creates_qurl():
    from utils.html import to_qurl
    from PyQt6.QtCore import QUrl
    q = to_qurl('https://example.com')
    assert isinstance(q, QUrl)
