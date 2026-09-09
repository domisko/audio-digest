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

            full_text = None
            if needs_full_text(entry.summary_raw):
                full_text = extract_full_text(entry.url, source)

            try:
                articles.append(
                    Article(
                        source=source.name,
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
