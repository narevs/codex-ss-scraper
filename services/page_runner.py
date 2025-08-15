from __future__ import annotations

import asyncio
import os
from typing import Callable, List

import aiohttp

from utils import html as html_utils, normalize, scraper


class PageRunner:
    """Process URLs page by page using a ``QWebEngineView``."""

    def __init__(
        self,
        view,
        email_callback: Callable[[str], None] | None = None,
        stats_manager=None,
        stats_callback: Callable[[], None] | None = None,
    ):
        self.view = view
        self.email_callback = email_callback
        self.stats = stats_manager
        self.stats_callback = stats_callback
        self.seen_emails: set[str] = set()
        self.records: List[dict] = []

    async def run_urls(self, urls: List[str], cap: int | None = None):
        use_ocr = os.getenv("USE_OCR", "1") == "1"
        check_mx = os.getenv("CHECK_MX", "1") == "1"
        timeout = int(os.getenv("TIMEOUT", "20"))
        limit = cap or len(urls)

        session_timeout = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=session_timeout) as session:
            for url in urls[:limit]:
                if self.stats:
                    self.stats.increment_pages()
                    if self.stats_callback:
                        self.stats_callback()
                html = html_utils.load_html(self.view, url)
                record = scraper.extract_from_dom(html, url)
                pdf_url = scraper.maybe_follow_pdf(html, url)
                if pdf_url and (use_ocr or not record["email"]):
                    try:
                        async with session.get(pdf_url) as resp:
                            pdf_bytes = await resp.read()
                        text = scraper.extract_text_from_pdf(pdf_bytes)
                        if not text and use_ocr:
                            text = scraper.ocr_pdf_bytes(pdf_bytes)
                        if text:
                            pdf_emails = {
                                normalize.normalize_email(e)
                                for e in scraper.EMAIL_RE.findall(text)
                            }
                            if pdf_emails:
                                first = next(iter(pdf_emails))
                                if not record["email"]:
                                    record["email"] = first
                                record["emails"] = list({*record["emails"], *pdf_emails})
                    except Exception:
                        pass

                email = record.get("email")
                if email:
                    email = normalize.normalize_email(email)
                    record["email"] = email
                    record["duplicate"] = email in self.seen_emails
                    if not record["duplicate"]:
                        self.seen_emails.add(email)
                        if self.stats:
                            self.stats.increment_data()
                            if self.stats_callback:
                                self.stats_callback()
                    if check_mx:
                        domain = email.split("@")[-1]
                        record["verified"] = scraper.mx_has_records(domain)
                    if self.email_callback:
                        self.email_callback(email)
                record["timestamp"] = normalize.current_timestamp()
                self.records.append(record)
        return self.records
