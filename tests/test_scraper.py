"""Scraper tests — fixture-based, no network access."""

from datetime import UTC, datetime
from pathlib import Path

from audio_digest.models import Article
from audio_digest.scraper.extractor import needs_full_text
from audio_digest.scraper.feeds import FeedSource
from audio_digest.scraper.pipeline import select_articles
from audio_digest.scraper.rss import fetch_feed

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_fetch_feed_parses_entries() -> None:
    source = FeedSource(
        name="sample",
        display_name="Sample",
        url=(FIXTURES_DIR / "sample_feed.xml").as_uri(),
        category="general_news",
    )

    entries = fetch_feed(source)

    assert len(entries) == 2
    assert entries[0].title == "First Article"
    assert entries[0].url == "https://example.com/first-article"
    assert entries[0].source is source


def test_fetch_feed_returns_empty_list_for_broken_url() -> None:
    source = FeedSource(
        name="broken", display_name="Broken", url="not-a-valid-url", category="tech"
    )

    entries = fetch_feed(source)

    assert entries == []


def test_needs_full_text_short_summary() -> None:
    assert needs_full_text("short") is True


def test_needs_full_text_long_summary() -> None:
    assert needs_full_text("x" * 500) is False


def _article(source: str, minutes_ago: int) -> Article:
    return Article(
        source=source,
        source_display_name=source,
        title=f"{source} article {minutes_ago}",
        url=f"https://example.com/{source}-{minutes_ago}",
        published_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC).replace(minute=59 - minutes_ago),
        summary_raw="summary",
        fetched_at=datetime.now(UTC),
        category="general_news",
    )


def test_select_articles_respects_limit() -> None:
    articles = [_article("a", i) for i in range(10)]

    selected = select_articles(articles, limit=4)

    assert len(selected) == 4


def test_select_articles_diversifies_across_sources() -> None:
    articles = [_article("nzz", i) for i in range(10)] + [_article("hn", i) for i in range(2)]

    selected = select_articles(articles, limit=4)

    sources = [a.source for a in selected]
    assert sources.count("hn") == 2
    assert sources.count("nzz") == 2


def test_select_articles_prefers_most_recent_per_source() -> None:
    articles = [_article("a", minutes_ago) for minutes_ago in [50, 5, 30]]

    selected = select_articles(articles, limit=1)

    assert selected[0].title == "a article 5"
