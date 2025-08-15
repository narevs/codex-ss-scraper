from __future__ import annotations

from typing import Iterable, List
from urllib.parse import urlparse, urlunparse

from PyQt6.QtCore import QUrl

EXCLUDED_SCHEMES = {"mailto", "javascript"}
EXCLUDED_HOSTS = {"doi.org", "dx.doi.org"}


def to_qurl(s: str) -> QUrl:
    """Return a QUrl built from user input.

    QUrl.fromUserInput applies permissive parsing that accepts a wide range
    of URL-like strings. It also ensures the URL is considered valid by Qt.
    """
    return QUrl.fromUserInput(s)


def filter_normalize_dedupe(urls: Iterable[str], max_n: int, allowlist: List[str]) -> List[str]:
    """Filter, normalise and deduplicate a collection of URLs.

    Parameters
    ----------
    urls:
        Iterable of raw URLs.
    max_n:
        Maximum number of links to return after filtering.
    allowlist:
        List of hostnames that links must match to be kept.

    Returns
    -------
    List[str]
        Normalised, deduplicated URLs that satisfy the allowlist and
        exclusion rules.
    """
    allowset = {h.lower() for h in allowlist}
    seen = set()
    results: List[str] = []

    for raw in urls:
        if len(results) >= max_n:
            break
        if not raw:
            continue
        url = raw.strip()
        if url.startswith("#"):
            continue
        parsed = urlparse(url)
        if parsed.scheme.lower() in EXCLUDED_SCHEMES:
            continue
        host = (parsed.hostname or "").lower()
        if host in EXCLUDED_HOSTS:
            continue
        if host not in allowset:
            continue
        if parsed.path.lower().endswith(".pdf"):
            continue

        scheme = parsed.scheme or "https"
        normalized = urlunparse((scheme, host, parsed.path, "", parsed.query, ""))
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(normalized)

    return results


__all__ = ["to_qurl", "filter_normalize_dedupe"]
