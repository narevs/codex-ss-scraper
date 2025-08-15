import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.link_collector import collect_links


def test_collect_links_cap_and_dedupe():
    html = (Path(__file__).parent / "fixtures" / "sample_results.html").read_text()
    links = collect_links(
        "https://example.org/results",
        html,
        "example.org",
        cap=4,
        logger=lambda c, t: None,
    )
    assert len(links) == 4
    assert len(links) == len(set(links))


def test_normalize_strips_tracking_and_fragments():
    html = '<a href="/article/1?utm_source=a&fbclid=1#section">A</a>'
    links = collect_links(
        "https://example.org/results",
        html,
        "example.org",
        cap=5,
        logger=lambda c, t: None,
    )
    assert links == ["https://example.org/article/1"]
