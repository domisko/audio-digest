"""Feed source configuration. Plain data — adding a feed is a one-line change."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class FeedSource:
    name: str
    url: str
    category: Literal["general_news", "tech"]
    # Some sites are JS-heavy and need Playwright rather than a plain HTTP GET
    # for full-text extraction. Keep this False by default — Playwright is slow.
    needs_playwright: bool = False


DEFAULT_FEED_SOURCES: list[FeedSource] = [
    FeedSource(
        name="tagesschau", url="https://www.tagesschau.de/xml/rss2/", category="general_news"
    ),
    FeedSource(
        name="bbc_world", url="http://feeds.bbci.co.uk/news/world/rss.xml", category="general_news"
    ),
    FeedSource(
        name="euronews",
        url="https://www.euronews.com/rss?level=theme&name=news",
        category="general_news",
    ),
    FeedSource(name="hackernews", url="https://hnrss.org/frontpage", category="tech"),
]
