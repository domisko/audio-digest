"""Scraper tests — fixture-based, no network access."""

from pathlib import Path

from audio_digest.scraper.extractor import needs_full_text
from audio_digest.scraper.feeds import FeedSource
from audio_digest.scraper.rss import fetch_feed

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_fetch_feed_parses_entries() -> None:
    source = FeedSource(
        name="sample", url=(FIXTURES_DIR / "sample_feed.xml").as_uri(), category="general_news"
    )

    entries = fetch_feed(source)

    assert len(entries) == 2
    assert entries[0].title == "First Article"
    assert entries[0].url == "https://example.com/first-article"
    assert entries[0].source is source


def test_fetch_feed_returns_empty_list_for_broken_url() -> None:
    source = FeedSource(name="broken", url="not-a-valid-url", category="tech")

    entries = fetch_feed(source)

    assert entries == []


def test_needs_full_text_short_summary() -> None:
    assert needs_full_text("short") is True


def test_needs_full_text_long_summary() -> None:
    assert needs_full_text("x" * 500) is False
