"""Scraper tests — fixture-based, no network access."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from audio_digest.models import Article
from audio_digest.scraper.extractor import needs_full_text
from audio_digest.scraper.feeds import FeedSource
from audio_digest.scraper.pipeline import fetch_articles, select_articles
from audio_digest.scraper.rss import RawEntry, fetch_feed

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


def test_fetch_articles_skips_video_bulletin_urls() -> None:
    source = FeedSource(
        name="euronews", display_name="Euronews", url="ignored", category="general_news"
    )
    entries = [
        RawEntry(
            source=source,
            title="Latest news bulletin",
            url="https://www.euronews.com/video/2026/09/09/latest-news-bulletin",
            published_at=datetime.now(UTC),
            summary_raw="x" * 200,
        ),
        RawEntry(
            source=source,
            title="A real article",
            url="https://www.euronews.com/2026/09/09/a-real-article",
            published_at=datetime.now(UTC),
            summary_raw="x" * 200,
        ),
    ]

    with (
        patch("audio_digest.scraper.pipeline.fetch_feed", return_value=entries),
        patch("audio_digest.scraper.pipeline.extract_full_text", return_value=None),
    ):
        articles = fetch_articles(sources=[source])

    assert len(articles) == 1
    assert articles[0].title == "A real article"


def test_fetch_articles_skips_near_empty_entries() -> None:
    source = FeedSource(name="thin", display_name="Thin", url="ignored", category="general_news")
    entries = [
        RawEntry(
            source=source,
            title="Just a stub",
            url="https://example.com/stub",
            published_at=datetime.now(UTC),
            summary_raw="Too short",
        ),
        RawEntry(
            source=source,
            title="A real article",
            url="https://example.com/real",
            published_at=datetime.now(UTC),
            summary_raw="x" * 200,
        ),
    ]

    with (
        patch("audio_digest.scraper.pipeline.fetch_feed", return_value=entries),
        patch("audio_digest.scraper.pipeline.extract_full_text", return_value=None),
    ):
        articles = fetch_articles(sources=[source])

    assert len(articles) == 1
    assert articles[0].title == "A real article"


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
