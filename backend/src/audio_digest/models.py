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
    source_display_name: str
    title: str
    url: HttpUrl
    published_at: datetime
    summary_raw: str
    full_text: str | None = None
    fetched_at: datetime
    category: Literal["general_news", "tech"]


class WordTiming(BaseModel):
    """One spoken word's position in the final concatenated audio file."""

    text: str
    start_seconds: float
    duration_seconds: float


class ScriptSegment(BaseModel):
    source_article_url: HttpUrl
    # Populated by the pipeline (not the LLM) from the matching Article — a
    # human-readable outlet name (e.g. "Euronews") for display next to the link.
    source_name: str | None = None
    headline: str
    narration: str
    # A single condensed sentence for the frontend's read view, distinct from
    # `narration` (the full spoken-audio paragraph) — the two audiences (skim
    # vs. listen) want different lengths.
    summary_short: str
    # Short, reusable category labels (e.g. "Politik", "Wirtschaft") the
    # frontend renders as pills and uses to build its tag filter bar.
    tags: list[str] = []
    # Subjective, model-generated tone observation — never framed as fact-checking.
    tone_axis: str | None = None
    tone_score: int | None = None
    # Populated by the pipeline after TTS synthesis (not by the LLM) — the
    # offset in the final audio file where this segment's narration starts,
    # so the frontend can link a segment straight to its point in the audio.
    audio_start_seconds: float | None = None
    # Per-word timing within the final audio, for karaoke-style caption
    # highlighting. Empty if the active TTS backend doesn't expose word
    # boundaries (only EdgeTTS currently does).
    words: list[WordTiming] = []


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
