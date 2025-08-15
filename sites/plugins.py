"""Site-specific link selection and normalization helpers."""
from __future__ import annotations

from typing import Callable, Dict, List

# Generic selectors used as a fallback when a hostname has no plugin entry.
GENERIC_SELECTORS: List[str] = [
    "a[href*='/article/']",
    "a[href*='/abs/']",
    "a[href*='/doi/']",
    "a[href*='/paper/']",
    "a[href*='?pii=']",
]


def _noop(url: str) -> str:
    """Return *url* unchanged."""
    return url


# Map of hostname -> plugin configuration.  Each entry may define CSS
# selectors and a ``normalize`` callable to tweak URLs.
PLUGIN_MAP: Dict[str, Dict[str, object]] = {
    "pubs.acs.org": {
        "selectors": ["a[href*='/doi/']", "a[href*='/abs/']"],
    },
    "www.hindawi.com": {
        "selectors": [
            "a[href*='/journals/']",
            "a[href*='/articles/']",
            "a[aria-label*='article']",
        ],
    },
    "www.researchsquare.com": {
        "selectors": ["a[href*='/article/']", "a[href*='/rs-']"],
    },
    "academic.oup.com": {
        "selectors": ["a[href*='/article/']", "a[href*='/doi/']"],
    },
    "journals.sagepub.com": {
        "selectors": ["a[href*='/doi/']", "a[class*='article']"],
    },
    "www.cureus.com": {
        "selectors": ["a[href*='/articles/']"],
    },
    "onlinelibrary.wiley.com": {
        "selectors": ["a[href*='/doi/']"],
    },
    "www.tandfonline.com": {
        "selectors": ["a[href*='/doi/']"],
    },
    "link.springer.com": {
        "selectors": ["a[href*='/article/']", "a[href*='/chapter/']"],
    },
    "journals.plos.org": {
        "selectors": [
            "a[href*='/article?id=']",
            "a[href*='/plosone/article?id=']",
        ],
    },
    "www.sciencedirect.com": {
        "selectors": [
            "a[href*='/science/article/']",
            "a[href*='/pii/']",
        ],
    },
}


def get_selectors(hostname: str) -> List[str]:
    """Return CSS selectors for *hostname* or a generic fallback."""
    return PLUGIN_MAP.get(hostname, {}).get("selectors", GENERIC_SELECTORS)  # type: ignore[index]


def get_normalizer(hostname: str) -> Callable[[str], str]:
    """Return URL normalizer for *hostname* if provided."""
    return PLUGIN_MAP.get(hostname, {}).get("normalize", _noop)  # type: ignore[index]
