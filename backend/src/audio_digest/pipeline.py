"""Daily digest orchestration — the one function every caller (API, CLI) wires up to."""

import logging
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from mutagen.mp3 import MP3

from audio_digest.config import Settings
from audio_digest.delivery.telegram import send_digest
from audio_digest.models import Article, DigestResult, Script
from audio_digest.scraper.pipeline import fetch_articles, select_articles
from audio_digest.storage import latest_audio_path, save_latest
from audio_digest.summarizer import get_summarizer
from audio_digest.tts import get_tts
from audio_digest.tts.base import TextToSpeech

logger = logging.getLogger(__name__)

# Keeps the spoken digest around ~5 minutes rather than growing with however
# many articles happened to be published that day.
MAX_DIGEST_ARTICLES = 8


class NoArticlesError(RuntimeError):
    """Raised when no articles were found — better to fail loudly than send an empty digest."""


def _attach_source_names(script: Script, articles: list[Article]) -> None:
    """Match each segment back to its Article by URL to fill in source_name.

    The LLM only ever sees article URLs, not our internal source labels, so
    this is resolved locally rather than trusted from the model's output.
    Falls back to a prefix match since the model occasionally echoes a long
    URL back slightly truncated.
    """
    by_url = {str(article.url): article.source_display_name for article in articles}
    for segment in script.segments:
        segment_url = str(segment.source_article_url)
        name = by_url.get(segment_url)
        if name is None:
            name = next(
                (
                    display_name
                    for url, display_name in by_url.items()
                    if url.startswith(segment_url) or segment_url.startswith(url)
                ),
                None,
            )
        segment.source_name = name


def _mp3_duration_seconds(path: Path) -> float:
    # mutagen ships without type stubs.
    return float(MP3(path).info.length)  # type: ignore[no-untyped-call,attr-defined]


async def _synthesize_script_audio(tts: TextToSpeech, script: Script, output_path: Path) -> None:
    """Synthesize intro/segments/outro as separate clips, concatenate them, and
    record each segment's start offset (mutating `script.segments` in place) so
    the frontend can jump straight to a segment's point in the audio.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        parts: list[Path] = []

        intro_path = tmp / "000_intro.mp3"
        await tts.synthesize(script.intro, intro_path)
        parts.append(intro_path)
        cumulative_seconds = _mp3_duration_seconds(intro_path)

        for index, segment in enumerate(script.segments):
            segment_path = tmp / f"{index + 1:03d}_segment.mp3"
            await tts.synthesize(segment.narration, segment_path)
            segment.audio_start_seconds = cumulative_seconds
            cumulative_seconds += _mp3_duration_seconds(segment_path)
            parts.append(segment_path)

        outro_path = tmp / "999_outro.mp3"
        await tts.synthesize(script.outro, outro_path)
        parts.append(outro_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as combined:
            for part in parts:
                combined.write(part.read_bytes())


async def run_daily_digest(settings: Settings) -> DigestResult:
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    articles = fetch_articles(since=today_start)
    if not articles:
        raise NoArticlesError("No articles found for today's digest")
    articles = select_articles(articles, limit=MAX_DIGEST_ARTICLES)

    summarizer = get_summarizer(settings)
    script = summarizer.summarize(articles, digest_date=now.date())
    _attach_source_names(script, articles)

    tts = get_tts(settings)
    audio_path = latest_audio_path(settings.output_dir)
    await _synthesize_script_audio(tts, script, audio_path)

    delivered = False
    delivery_message_id = None
    if settings.telegram_bot_token and settings.telegram_chat_id:
        try:
            delivery_message_id = await send_digest(
                settings.telegram_bot_token,
                settings.telegram_chat_id,
                audio_path,
                caption=f"Digest for {now.date().isoformat()}",
            )
            delivered = True
        except Exception:
            logger.warning("Telegram delivery failed", exc_info=True)

    result = DigestResult(
        digest_date=now.date(),
        articles_used=articles,
        script=script,
        audio_path=str(audio_path),
        delivered=delivered,
        delivery_message_id=delivery_message_id,
    )
    save_latest(result, settings.output_dir)
    return result
