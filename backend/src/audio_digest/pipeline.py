"""Daily digest orchestration — the one function every caller (API, CLI) wires up to."""

import logging
from datetime import UTC, datetime

from audio_digest.config import Settings
from audio_digest.delivery.telegram import send_digest
from audio_digest.models import DigestResult
from audio_digest.scraper.pipeline import fetch_articles, select_articles
from audio_digest.storage import latest_audio_path, save_latest
from audio_digest.summarizer import get_summarizer
from audio_digest.tts import get_tts

logger = logging.getLogger(__name__)

# Keeps the spoken digest around ~5 minutes rather than growing with however
# many articles happened to be published that day.
MAX_DIGEST_ARTICLES = 8


class NoArticlesError(RuntimeError):
    """Raised when no articles were found — better to fail loudly than send an empty digest."""


async def run_daily_digest(settings: Settings) -> DigestResult:
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    articles = fetch_articles(since=today_start)
    if not articles:
        raise NoArticlesError("No articles found for today's digest")
    articles = select_articles(articles, limit=MAX_DIGEST_ARTICLES)

    summarizer = get_summarizer(settings)
    script = summarizer.summarize(articles, digest_date=now.date())

    tts = get_tts(settings)
    audio_path = latest_audio_path(settings.output_dir)
    await tts.synthesize(script.full_text, audio_path)

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
