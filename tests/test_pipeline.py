"""Pipeline orchestration tests — scraper/summarizer/delivery are mocked; TTS uses
a fake that copies a tiny real MP3 fixture so segment-timing logic runs for real.
"""

import shutil
from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from audio_digest.config import Settings
from audio_digest.models import Article, Script, ScriptSegment
from audio_digest.pipeline import NoArticlesError, run_daily_digest
from audio_digest.tts.base import TextToSpeech

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FakeTTS(TextToSpeech):
    """Copies a small real MP3 fixture instead of doing real speech synthesis."""

    async def synthesize(self, text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(FIXTURES_DIR / "silence.mp3", output_path)
        return output_path


def _settings(tmp_path: Path) -> Settings:
    return Settings(anthropic_api_key="k", api_key="k", output_dir=tmp_path)  # type: ignore[call-arg]


def _article() -> Article:
    return Article(
        source="test",
        title="Title",
        url="https://example.com/a",
        published_at=datetime.now(UTC),
        summary_raw="summary",
        fetched_at=datetime.now(UTC),
        category="general_news",
    )


def _script() -> Script:
    return Script(
        digest_date=date.today(),
        intro="Hi",
        segments=[
            ScriptSegment(
                source_article_url="https://example.com/a",
                headline="H",
                narration="N",
                summary_short="S",
            ),
            ScriptSegment(
                source_article_url="https://example.com/a",
                headline="H2",
                narration="N2",
                summary_short="S2",
            ),
        ],
        outro="Bye",
        full_text="Hi N N2 Bye",
    )


@pytest.mark.asyncio
async def test_run_daily_digest_happy_path(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    with (
        patch("audio_digest.pipeline.fetch_articles", return_value=[_article()]),
        patch("audio_digest.pipeline.get_summarizer") as mock_get_summarizer,
        patch("audio_digest.pipeline.get_tts", return_value=FakeTTS()),
    ):
        mock_get_summarizer.return_value.summarize.return_value = _script()

        result = await run_daily_digest(settings)

        assert result.delivered is False  # no Telegram config in these settings
        assert result.script.intro == "Hi"
        assert (tmp_path / "latest.json").exists()
        assert (tmp_path / "latest.mp3").stat().st_size > 0


@pytest.mark.asyncio
async def test_run_daily_digest_sets_segment_audio_offsets(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    with (
        patch("audio_digest.pipeline.fetch_articles", return_value=[_article()]),
        patch("audio_digest.pipeline.get_summarizer") as mock_get_summarizer,
        patch("audio_digest.pipeline.get_tts", return_value=FakeTTS()),
    ):
        mock_get_summarizer.return_value.summarize.return_value = _script()

        result = await run_daily_digest(settings)

        first, second = result.script.segments
        assert first.audio_start_seconds is not None
        assert second.audio_start_seconds is not None
        # Segment 2 starts after intro + segment 1's clip, so strictly later.
        assert second.audio_start_seconds > first.audio_start_seconds > 0


@pytest.mark.asyncio
async def test_run_daily_digest_raises_without_articles(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    with (
        patch("audio_digest.pipeline.fetch_articles", return_value=[]),
        pytest.raises(NoArticlesError),
    ):
        await run_daily_digest(settings)


@pytest.mark.asyncio
async def test_run_daily_digest_delivers_via_telegram_when_configured(tmp_path: Path) -> None:
    settings = Settings(  # type: ignore[call-arg]
        anthropic_api_key="k",
        api_key="k",
        output_dir=tmp_path,
        telegram_bot_token="t",
        telegram_chat_id="c",
    )

    with (
        patch("audio_digest.pipeline.fetch_articles", return_value=[_article()]),
        patch("audio_digest.pipeline.get_summarizer") as mock_get_summarizer,
        patch("audio_digest.pipeline.get_tts", return_value=FakeTTS()),
        patch("audio_digest.pipeline.send_digest", new=AsyncMock(return_value="123")),
    ):
        mock_get_summarizer.return_value.summarize.return_value = _script()

        result = await run_daily_digest(settings)

        assert result.delivered is True
        assert result.delivery_message_id == "123"


@pytest.mark.asyncio
async def test_run_daily_digest_survives_telegram_failure(tmp_path: Path) -> None:
    settings = Settings(  # type: ignore[call-arg]
        anthropic_api_key="k",
        api_key="k",
        output_dir=tmp_path,
        telegram_bot_token="t",
        telegram_chat_id="c",
    )

    with (
        patch("audio_digest.pipeline.fetch_articles", return_value=[_article()]),
        patch("audio_digest.pipeline.get_summarizer") as mock_get_summarizer,
        patch("audio_digest.pipeline.get_tts", return_value=FakeTTS()),
        patch(
            "audio_digest.pipeline.send_digest",
            new=AsyncMock(side_effect=RuntimeError("network down")),
        ),
    ):
        mock_get_summarizer.return_value.summarize.return_value = _script()

        result = await run_daily_digest(settings)

        assert result.delivered is False
