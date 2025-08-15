"""Utility helpers for Scholar Summit Email Scraper.

This module contains small helper functions used across the
application. Functions are intentionally tiny and easily testable.
"""

from __future__ import annotations

from typing import Iterable, List
from urllib.parse import urlparse

from PyQt6.QtCore import QUrl


def to_qurl(s: str) -> QUrl:
    """Create a :class:`QUrl` from ``s``.

    ``QUrl.fromUserInput`` is forgiving and understands a large variety of
    input strings.  This wrapper adds a small amount of safety by
    normalising blank strings and ``about:blank`` to an empty ``QUrl``.
    """

    if not s:
        return QUrl()
    s = s.strip()
    if not s or s.lower() == "about:blank":
        return QUrl()
    url = QUrl.fromUserInput(s)
    if not url.isValid():
        return QUrl()
    return url


def normalize_host(url: str) -> str:
    """Normalise the host portion of ``url``.

    ``www.`` prefixes are stripped and the result is always lower case.  If
    ``url`` does not contain a scheme it is still handled gracefully.
    """

    if not url:
        return ""

    parsed = urlparse(url if "://" in url else f"http://{url}")
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def is_same_host(url: str, base: str) -> bool:
    """Return ``True`` if ``url`` belongs to ``base``.

    Sub‑domains of ``base`` are considered a match.
    """

    url_host = normalize_host(url)
    base_host = normalize_host(base)
    if not url_host or not base_host:
        return False
    return url_host == base_host or url_host.endswith("." + base_host)


def deduplicate(urls: Iterable[str]) -> List[str]:
    """Return ``urls`` with duplicates removed preserving order."""

    seen = set()
    result: List[str] = []
    for u in urls:
        norm = QUrl.fromUserInput(u).toString()
        if norm.lower() not in seen:
            seen.add(norm.lower())
            result.append(u)
    return result


def navigate(view, qurl: QUrl) -> None:
    """Navigate ``view`` to ``qurl``.

    The function is intentionally tiny to make it easy to unit test.  It
    only accepts :class:`QUrl` instances; passing any other type raises a
    :class:`TypeError`.
    """

    if not isinstance(qurl, QUrl):
        raise TypeError("navigate() requires a QUrl instance")
    view.setUrl(qurl)
