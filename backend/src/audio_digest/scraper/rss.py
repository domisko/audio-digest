"""Fetch and parse RSS feeds into raw entries, tolerant of individual feed failures."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

import feedparser

from audio_digest.scraper.feeds import FeedSource

logger = logging.getLogger(__name__)


@dataclass
class RawEntry:
    source: FeedSource
    title: str
    url: str
    published_at: datetime
    summary_raw: str


def fetch_feed(source: FeedSource) -> list[RawEntry]:
    """Fetch one feed. Never raises — a broken feed is logged and yields no entries,
    so one bad source can't take down the whole day's digest.
    """
    try:
        parsed = feedparser.parse(source.url)
    except Exception:
        logger.warning("Failed to fetch feed %s (%s)", source.name, source.url, exc_info=True)
        return []

    if parsed.bozo:
        logger.warning(
            "Feed %s parsed with warnings: %s", source.name, parsed.get("bozo_exception")
        )

    entries: list[RawEntry] = []
    for entry in parsed.entries:
        url = entry.get("link")
        title = entry.get("title")
        if not url or not title:
            continue
        published_at = _parse_published(entry)
        entries.append(
            RawEntry(
                source=source,
                title=title,
                url=url,
                published_at=published_at,
                summary_raw=entry.get("summary", ""),
            )
        )
    return entries


def _parse_published(entry: feedparser.FeedParserDict) -> datetime:
    """feedparser gives a time.struct_time in UTC via *_parsed fields; fall back to now."""
    for field in ("published_parsed", "updated_parsed"):
        struct_time = entry.get(field)
        if struct_time:
            year, month, day, hour, minute, second = struct_time[:6]
            return datetime(year, month, day, hour, minute, second, tzinfo=UTC)
    return datetime.now(UTC)
