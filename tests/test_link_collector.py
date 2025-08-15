import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.link_collector import collect_links


def test_collect_links_dedupe_and_cap():
    html = (Path(__file__).parent / "fixtures" / "sample_results.html").read_text()
    links = collect_links(html, base_url="https://example.org", cap=5)
    assert len(links) == 5
    assert len(links) == len(set(links))
