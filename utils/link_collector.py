"""Utilities for collecting article links from web pages.

The ``collect_links`` function can operate on a raw HTML string or, when
``html`` is ``None``, interact with a ``QWebEngineView`` set via
``CURRENT_VIEW`` to perform a short scrolling loop.
"""
from __future__ import annotations

import random
import time
from typing import Callable, List, Set
from urllib.parse import parse_qsl, urljoin, urlsplit, urlunsplit, urlencode

from bs4 import BeautifulSoup

from sites.plugins import GENERIC_SELECTORS, get_normalizer, get_selectors

try:  # pragma: no cover - Qt is optional for tests
    from PyQt6.QtCore import QEventLoop
    from PyQt6.QtWebEngineWidgets import QWebEngineView
except Exception:  # pragma: no cover
    QEventLoop = None  # type: ignore
    QWebEngineView = None  # type: ignore

# ``CURRENT_VIEW`` is set by the UI before calling :func:`collect_links`
# when browser-driven scraping is desired.
CURRENT_VIEW: QWebEngineView | None = None


def _run_js(view: QWebEngineView, script: str):  # pragma: no cover - GUI helper
    loop = QEventLoop()
    result: dict = {}
    view.page().runJavaScript(script, lambda r: (result.setdefault("r", r), loop.quit()))
    loop.exec()
    return result.get("r")


def _normalize_url(page_url: str, href: str, host: str) -> str:
    url = urljoin(page_url, href)
    url = get_normalizer(host)(url)
    parts = urlsplit(url)
    # strip tracking query params and fragments
    query = [(k, v) for k, v in parse_qsl(parts.query) if not (k.startswith("utm_") or k == "fbclid")]
    cleaned = parts._replace(query=urlencode(query), fragment="")
    return urlunsplit(cleaned)


def _extract_links(html: str, page_url: str, host: str, cap: int, results: List[str], seen: Set[str]) -> None:
    soup = BeautifulSoup(html, "html.parser")
    selectors = get_selectors(host)
    anchors: List[str] = []
    for sel in selectors:
        anchors.extend(soup.select(sel))
    # Fallback to generic selectors if none matched
    if not anchors:
        for sel in GENERIC_SELECTORS:
            anchors.extend(soup.select(sel))
    for a in anchors:
        href = a.get("href")
        if not href:
            continue
        url = _normalize_url(page_url, href, host)
        if url in seen:
            continue
        seen.add(url)
        results.append(url)
        if len(results) >= cap:
            break
    # end function


def collect_links(page_url: str, html: str | None, host: str, cap: int, logger: Callable[[int, int], None]) -> List[str]:
    """Collect article-like links.

    Parameters
    ----------
    page_url:
        Base URL of the page being processed.
    html:
        Raw HTML string.  When ``None`` the function will attempt to use
        ``CURRENT_VIEW`` (a ``QWebEngineView``) to scroll and fetch HTML.
    host:
        Hostname of the page; used to select site plugins.
    cap:
        Maximum number of links to return.
    logger:
        Callback accepting ``(collected, cap)`` used to update UI status.
    """
    results: List[str] = []
    seen: Set[str] = set()

    if html is not None:
        _extract_links(html, page_url, host, cap, results, seen)
        logger(len(results), cap)
        return results

    view = CURRENT_VIEW
    if not view or not QWebEngineView:  # pragma: no cover - requires GUI
        return results

    start = time.time()
    last_height = 0
    while time.time() - start < 8 and len(results) < cap:  # pragma: no branch - GUI
        page_html = _run_js(view, "document.body.innerHTML")
        _extract_links(page_html, page_url, host, cap, results, seen)
        logger(len(results), cap)
        if len(results) >= cap:
            break
        height = _run_js(view, "document.body.scrollHeight")
        _run_js(view, "window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(0.25 + random.random() * 0.15)
        new_height = _run_js(view, "document.body.scrollHeight")
        if new_height == height:
            break
        last_height = new_height
    return results
