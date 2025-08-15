from url_utils import filter_normalize_dedupe, to_qurl


def test_qurl():
    qurl = to_qurl("https://example.com")
    assert qurl.isValid()
    assert qurl.toString() == "https://example.com"


def test_filter_normalize_dedupe():
    urls = [
        "https://www.sciencedirect.com/science/article/pii/S123",
        "https://www.sciencedirect.com/science/article/pii/S123",  # duplicate
        "https://www.sciencedirect.com/science/article.pdf",  # pdf
        "mailto:author@example.com",
        "#",
        "https://doi.org/10.1000/xyz",
        "https://WWW.ScienceDirect.com/science/article/pii/S456",
    ]
    allowlist = ["www.sciencedirect.com"]
    result = filter_normalize_dedupe(urls, max_n=10, allowlist=allowlist)
    assert result == [
        "https://www.sciencedirect.com/science/article/pii/S123",
        "https://www.sciencedirect.com/science/article/pii/S456",
    ]
