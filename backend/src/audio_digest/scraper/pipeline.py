"""Public scraper entrypoint: fetch_articles() -> list[Article].

This is the one function the rest of the app imports from `scraper`.
"""

import logging
from datetime import datetime

from pydantic import ValidationError

from audio_digest.models import Article
from audio_digest.scraper.extractor import extract_full_text, needs_full_text
from audio_digest.scraper.feeds import DEFAULT_FEED_SOURCES, FeedSource
from audio_digest.scraper.rss import fetch_feed

logger = logging.getLogger(__name__)

# Entries with barely any usable text (e.g. a video-bulletin stub with just a
# one-line description) give the summarizer nothing to actually summarize,
# which tends to produce filler content about the source instead of the story.
MIN_USABLE_CONTENT_LENGTH = 80

# Video-bulletin pages (no real article body — just a player and show
# blurbs) commonly live under a /video/ path. Extracting "full text" from one
# picks up generic show descriptions instead of the story, which then reads
# like an ad for the outlet once summarized. Skip these outright rather than
# trying to summarize placeholder text.
NON_ARTICLE_URL_MARKERS = ("/video/",)


def _looks_like_article(url: str) -> bool:
    return not any(marker in url for marker in NON_ARTICLE_URL_MARKERS)


def fetch_articles(
    sources: list[FeedSource] | None = None,
    since: datetime | None = None,
) -> list[Article]:
    """Fetch and validate articles from all configured feeds published after `since`."""
    sources = sources if sources is not None else DEFAULT_FEED_SOURCES
    fetched_at = datetime.now(since.tzinfo if since else None)
    articles: list[Article] = []

    for source in sources:
        for entry in fetch_feed(source):
            if since and entry.published_at < since:
                continue
            if not _looks_like_article(entry.url):
                logger.info("Skipping non-article entry from %s: %s", source.name, entry.url)
                continue

            full_text = None
            if needs_full_text(entry.summary_raw):
                full_text = extract_full_text(entry.url, source)

            usable_text = full_text or entry.summary_raw
            if len(usable_text) < MIN_USABLE_CONTENT_LENGTH:
                logger.info("Skipping near-empty article from %s: %s", source.name, entry.url)
                continue

            try:
                articles.append(
                    Article(
                        source=source.name,
                        source_display_name=source.display_name,
                        title=entry.title,
                        url=entry.url,  # type: ignore[arg-type]  # pydantic coerces str -> HttpUrl at runtime
                        published_at=entry.published_at,
                        summary_raw=entry.summary_raw,
                        full_text=full_text,
                        fetched_at=fetched_at,
                        category=source.category,
                    )
                )
            except ValidationError:
                logger.warning(
                    "Skipping invalid article from %s: %s", source.name, entry.url, exc_info=True
                )

    return articles


def select_articles(articles: list[Article], limit: int) -> list[Article]:
    """Pick a manageable, source-diverse subset for a short digest.

    Round-robins across sources (most recent first within each) so one
    prolific feed doesn't crowd out the others.
    """
    by_source: dict[str, list[Article]] = {}
    for article in sorted(articles, key=lambda a: a.published_at, reverse=True):
        by_source.setdefault(article.source, []).append(article)

    selected: list[Article] = []
    while len(selected) < limit and any(by_source.values()):
        for source_articles in by_source.values():
            if not source_articles:
                continue
            selected.append(source_articles.pop(0))
            if len(selected) >= limit:
                break

    return selected
