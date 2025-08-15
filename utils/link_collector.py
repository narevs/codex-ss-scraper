import time
from typing import Iterable, List, Set
from urllib.parse import urljoin

from bs4 import BeautifulSoup

# Heuristic substrings indicating article links
HEURISTIC_PARTS = [
    "/article/",
    "/abs/",
    "/doi/",
    "/paper/",
    "?pii=",
]


def _is_article_link(href: str) -> bool:
    return any(part in href for part in HEURISTIC_PARTS)


def collect_links(html: str, base_url: str = "", cap: int = 50) -> List[str]:
    """Collect article-like links from HTML, dedupe and respect cap."""
    soup = BeautifulSoup(html, "html.parser")
    results: List[str] = []
    seen: Set[str] = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        if not _is_article_link(href):
            continue
        if href in seen:
            continue
        seen.add(href)
        results.append(href)
        if len(results) >= cap:
            break
    return results
