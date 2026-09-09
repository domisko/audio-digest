"""Data contracts shared across the pipeline.

`Article` is the stable boundary between the scraper and everything downstream:
whatever markup-scraping chaos happens inside `scraper/`, the rest of the
pipeline only ever sees a validated `Article` list.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, HttpUrl


class Article(BaseModel):
    source: str
    title: str
    url: HttpUrl
    published_at: datetime
    summary_raw: str
    full_text: str | None = None
    fetched_at: datetime
    category: Literal["general_news", "tech"]


class ScriptSegment(BaseModel):
    source_article_url: HttpUrl
    headline: str
    narration: str
    # Subjective, model-generated tone observation — never framed as fact-checking.
    tone_axis: str | None = None
    tone_score: int | None = None


class Script(BaseModel):
    digest_date: date
    intro: str
    segments: list[ScriptSegment]
    outro: str
    full_text: str


class DigestResult(BaseModel):
    digest_date: date
    articles_used: list[Article]
    script: Script
    audio_path: str
    delivered: bool
    delivery_message_id: str | None = None
