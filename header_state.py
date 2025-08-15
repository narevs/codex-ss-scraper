from dataclasses import dataclass


@dataclass
class HeaderState:
    """Represents the state of the scraper header controls."""
    rule: str = ""
    site: str = ""
    page_type: str = ""
    n: int = 0
    address: str = ""


def default_header_state() -> "HeaderState":
    """Return a fresh HeaderState with neutral defaults."""
    return HeaderState()
