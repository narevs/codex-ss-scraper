from __future__ import annotations

import io
import json
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .normalize import normalize_email

try:  # pragma: no cover - optional dependencies
    import fitz  # PyMuPDF
    from PIL import Image
    import pytesseract
except Exception:  # pragma: no cover
    fitz = None  # type: ignore
    Image = None  # type: ignore
    pytesseract = None  # type: ignore

try:  # pragma: no cover
    import dns.resolver
except Exception:  # pragma: no cover
    dns = None  # type: ignore

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def extract_from_dom(html: str, url: str) -> Dict:
    """Extract fields from page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ")
    emails = {normalize_email(e) for e in EMAIL_RE.findall(text)}
    for a in soup.select('a[href^="mailto:"]'):
        href = a.get('href', '')
        addr = href.split(':', 1)[1].split('?')[0]
        emails.add(normalize_email(addr))
    first_email = next(iter(emails)) if emails else ""

    name = ""
    meta = soup.find("meta", attrs={"name": "author"})
    if meta and meta.get("content"):
        name = meta["content"]
    if not name:
        meta = soup.find("meta", attrs={"property": "article:author"})
        if meta and meta.get("content"):
            name = meta["content"]
    if not name:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "{}")
            except Exception:
                continue
            auth = data.get("author")
            if isinstance(auth, dict) and isinstance(auth.get("name"), str):
                name = auth["name"]
                break
            if isinstance(auth, list) and auth:
                first = auth[0]
                if isinstance(first, dict) and isinstance(first.get("name"), str):
                    name = first["name"]
                    break

    journal = ""
    meta = soup.find("meta", attrs={"name": "citation_journal_title"})
    if meta and meta.get("content"):
        journal = meta["content"]
    if not journal:
        journal = urlparse(url).hostname or ""

    topic = ""
    meta = soup.find("meta", attrs={"name": "keywords"})
    if meta and meta.get("content"):
        topic = meta["content"]
    else:
        kw = soup.select_one(".keywords")
        if kw:
            topic = kw.get_text(" ")

    return {
        "name": name,
        "email": first_email,
        "emails": list(emails),
        "journal": journal,
        "topic": topic,
        "verified": False,
        "duplicate": False,
        "source_url": url,
        "timestamp": "",
    }


def maybe_follow_pdf(html: str, url: str) -> Optional[str]:
    """Return a PDF URL if one is advertised in the page."""
    soup = BeautifulSoup(html, "html.parser")
    link = soup.find("link", attrs={"rel": "alternate", "type": "application/pdf"})
    if link and link.get("href"):
        return urljoin(url, link["href"])
    meta = soup.find("meta", attrs={"name": "citation_pdf_url"})
    if meta and meta.get("content"):
        return urljoin(url, meta["content"])
    a = soup.find("a", href=lambda h: h and h.lower().endswith(".pdf"))
    if a and a.get("href"):
        return urljoin(url, a["href"])
    return None


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    if not fitz:  # pragma: no cover - dependency missing
        return ""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    except Exception:
        return ""


def ocr_pdf_bytes(pdf_bytes: bytes) -> str:
    if not (fitz and Image and pytesseract):  # pragma: no cover
        return ""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        texts: List[str] = []
        for page in doc:
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            texts.append(pytesseract.image_to_string(img))
        doc.close()
        return "\n".join(texts)
    except Exception:
        return ""


def mx_has_records(email_domain: str) -> bool:
    """Return True if the domain has MX records."""
    try:
        if dns is None:  # pragma: no cover
            return False
        answers = dns.resolver.resolve(email_domain, "MX")
        return bool(answers)
    except Exception:
        return False
