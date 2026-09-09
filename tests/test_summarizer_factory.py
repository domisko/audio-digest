"""get_summarizer() provider selection and missing-key error handling."""

from pathlib import Path

import pytest
from audio_digest.config import Settings
from audio_digest.summarizer import get_summarizer
from audio_digest.summarizer.claude import ClaudeSummarizer
from audio_digest.summarizer.openrouter import OpenRouterSummarizer


def _settings(tmp_path: Path, **overrides: object) -> Settings:
    base = {"anthropic_api_key": "k", "api_key": "k", "output_dir": tmp_path}
    return Settings(**{**base, **overrides})  # type: ignore[arg-type]


def test_get_summarizer_returns_claude_by_default(tmp_path: Path) -> None:
    summarizer = get_summarizer(_settings(tmp_path))
    assert isinstance(summarizer, ClaudeSummarizer)


def test_get_summarizer_returns_openrouter(tmp_path: Path) -> None:
    settings = _settings(tmp_path, summarizer_provider="openrouter", openrouter_api_key="or-key")
    summarizer = get_summarizer(settings)
    assert isinstance(summarizer, OpenRouterSummarizer)


def test_get_summarizer_raises_without_matching_key(tmp_path: Path) -> None:
    settings = _settings(tmp_path, summarizer_provider="openrouter", openrouter_api_key=None)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        get_summarizer(settings)
