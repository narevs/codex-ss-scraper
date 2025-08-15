import os
import sys

import pytest
from PyQt6.QtCore import QUrl

# Ensure project root is on the Python path when tests are executed
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ss_scraper.utils import to_qurl, normalize_host, is_same_host, navigate


class DummyView:
    def __init__(self):
        self.url = None

    def setUrl(self, url: QUrl):
        self.url = url


def test_to_qurl_returns_qurl():
    qurl = to_qurl("https://example.com")
    assert isinstance(qurl, QUrl)
    assert qurl.toString() == "https://example.com"

    blank = to_qurl("")
    assert isinstance(blank, QUrl)
    assert blank.isEmpty()


def test_navigate_requires_qurl():
    view = DummyView()
    qurl = to_qurl("https://example.com")
    navigate(view, qurl)
    assert view.url == qurl
    with pytest.raises(TypeError):
        navigate(view, "https://example.com")


def test_host_normalization_and_same_host():
    assert normalize_host("https://WWW.Example.com/path") == "example.com"
    assert is_same_host("https://sub.example.com/x", "https://example.com")
    assert not is_same_host("https://other.com", "https://example.com")
