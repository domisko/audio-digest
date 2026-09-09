"""Full-text extraction for articles whose RSS summary is too thin on its own.

Cheap path (httpx + BeautifulSoup) is tried first; Playwright is only used for
sources explicitly flagged `needs_playwright=True`, since it's much slower.
Any failure here is caught and logged — the pipeline falls back to the RSS
summary rather than losing the article entirely.
"""

import logging

import httpx
from bs4 import BeautifulSoup

from audio_digest.scraper.feeds import FeedSource

logger = logging.getLogger(__name__)

MIN_SUMMARY_LENGTH = 400
REQUEST_TIMEOUT_SECONDS = 10.0


def needs_full_text(summary_raw: str) -> bool:
    return len(summary_raw) < MIN_SUMMARY_LENGTH


def extract_full_text(url: str, source: FeedSource) -> str | None:
    try:
        if source.needs_playwright:
            return _extract_with_playwright(url)
        return _extract_with_httpx(url)
    except Exception:
        logger.warning("Full-text extraction failed for %s (%s)", url, source.name, exc_info=True)
        return None


def _extract_with_httpx(url: str) -> str | None:
    response = httpx.get(url, timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    text = "\n".join(p for p in paragraphs if p)
    return text or None


def _extract_with_playwright(url: str) -> str | None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(url, timeout=REQUEST_TIMEOUT_SECONDS * 1000)
            html = page.content()
        finally:
            browser.close()
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    text = "\n".join(p for p in paragraphs if p)
    return text or None
