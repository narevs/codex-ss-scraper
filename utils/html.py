from __future__ import annotations

from urllib.parse import urljoin

from PyQt6.QtCore import QEventLoop, QUrl


def to_qurl(url: str) -> QUrl:
    """Return a :class:`QUrl` from user input."""
    return QUrl.fromUserInput(url)


def get_inner_html(view) -> str:  # pragma: no cover - GUI helper
    if not view or not QEventLoop:
        return ""
    loop = QEventLoop()
    result = {}
    view.page().runJavaScript(
        "document.body.innerHTML", lambda r: (result.setdefault("r", r), loop.quit())
    )
    loop.exec()
    return result.get("r", "")


def load_html(view, url: str) -> str:  # pragma: no cover - GUI helper
    if not view or not QEventLoop:
        return ""
    loop = QEventLoop()
    view.load(to_qurl(url))
    view.loadFinished.connect(lambda _: loop.quit())
    loop.exec()
    return get_inner_html(view)


def absolute_url(base: str, href: str) -> str:
    """Return an absolute URL for ``href`` relative to ``base``."""
    return urljoin(base, href)
