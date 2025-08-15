"""Site-specific link selection heuristics.

This module exposes a ``get_selectors`` function returning a list of CSS
selectors for a given hostname.  For now it only provides a generic
fallback used by :mod:`utils.link_collector` tests.
"""
from __future__ import annotations

from typing import List

GENERIC_SELECTORS: List[str] = [
    "a[href*='/article/']",
    "a[href*='/abs/']",
    "a[href*='/doi/']",
    "a[href*='/paper/']",
    "a[href*='?pii=']",
]


def get_selectors(hostname: str) -> List[str]:
    """Return CSS selectors for *hostname*.

    The current implementation always returns :data:`GENERIC_SELECTORS`.
    """
    return GENERIC_SELECTORS
