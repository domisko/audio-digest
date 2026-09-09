"""Summarizer tests — Anthropic client is mocked, no real API calls / cost."""

from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from audio_digest.models import Article
from audio_digest.summarizer.claude import _SCRIPT_TOOL_NAME, ClaudeSummarizer


def _make_article(title: str) -> Article:
    return Article(
        source="test",
        title=title,
        url="https://example.com/a",
        published_at=datetime.now(UTC),
        summary_raw="a short summary",
        fetched_at=datetime.now(UTC),
        category="general_news",
    )


def _fake_tool_use_response(payload: dict) -> SimpleNamespace:
    tool_use_block = SimpleNamespace(type="tool_use", name=_SCRIPT_TOOL_NAME, input=payload)
    return SimpleNamespace(content=[tool_use_block])


def test_summarize_parses_valid_script() -> None:
    payload = {
        "digest_date": "2026-09-06",
        "intro": "Good morning.",
        "segments": [
            {
                "source_article_url": "https://example.com/a",
                "headline": "First up",
                "narration": "Here's what happened.",
                "summary_short": "Something happened.",
                "tone_axis": "emotional vs. sachlich",
                "tone_score": 30,
            }
        ],
        "outro": "That's all for today.",
        "full_text": "Good morning. Here's what happened. That's all for today.",
    }
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_tool_use_response(payload)
    summarizer = ClaudeSummarizer(api_key="unused", client=mock_client)

    script = summarizer.summarize([_make_article("First")], digest_date=date(2026, 9, 6))

    assert script.intro == "Good morning."
    assert script.segments[0].tone_score == 30
    mock_client.messages.create.assert_called_once()


def test_summarize_retries_then_raises_on_persistent_bad_output() -> None:
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_tool_use_response({"not": "a valid script"})
    summarizer = ClaudeSummarizer(api_key="unused", client=mock_client)

    try:
        summarizer.summarize([_make_article("First")], digest_date=date(2026, 9, 6))
        raised = False
    except RuntimeError:
        raised = True

    assert raised
    assert mock_client.messages.create.call_count > 1
