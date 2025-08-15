from pathlib import Path
from pathlib import Path
from pathlib import Path
from utils import scraper

FIXTURES = Path(__file__).parent / "fixtures"


def test_extract_from_dom_emails_and_meta():
    html = (FIXTURES / "sample_article.html").read_text()
    result = scraper.extract_from_dom(html, "https://example.com/article")
    assert result["email"] == "contact@example.com"
    assert sorted(result["emails"]) == ["admin@test.org", "contact@example.com"]
    assert result["name"] == "John Doe"
    assert result["journal"] == "Journal of Testing"
    assert result["topic"] == "biology, cell"


def test_extract_from_dom_schemaorg_author():
    html = (FIXTURES / "sample_article_schemaorg.html").read_text()
    result = scraper.extract_from_dom(html, "https://example.com/other")
    assert result["name"] == "Jane Roe"
    assert result["email"] == "jane@example.com"


def test_mx_has_records_handles_errors(monkeypatch):
    def raiser(domain, record):  # pragma: no cover - mocked
        raise RuntimeError("boom")

    monkeypatch.setattr(scraper.dns.resolver, "resolve", raiser)
    assert scraper.mx_has_records("example.com") is False
