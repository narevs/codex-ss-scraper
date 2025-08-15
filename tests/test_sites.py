import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.append(str(Path(__file__).resolve().parents[1]))
from site_loader import load_site_rules


def test_sites_json_structure():
    data = load_site_rules()
    assert data["rule_name"] == "Popular"
    sites = data["sites"]
    assert len(sites) == 11
    required_fields = {"name", "host_allowlist", "search_url", "journal_url"}
    for site in sites:
        assert required_fields.issubset(site.keys())
        for host in site["host_allowlist"]:
            parsed = urlparse(f"https://{host}")
            # ensure host contains no path or scheme beyond host
            assert parsed.path == ""
            assert parsed.scheme == "https"
            assert parsed.netloc == host
        # Ensure URLs contain placeholders for the query
        assert "{query}" in site["search_url"]
        assert site["journal_url"].startswith("https://")
