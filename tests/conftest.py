"""Shared test fixtures."""

import os

import pytest


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide the required env vars so Settings() can construct in every test."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("API_KEY", "test-api-key")
    os.environ.pop("TELEGRAM_BOT_TOKEN", None)
    os.environ.pop("TELEGRAM_CHAT_ID", None)

    from audio_digest.api.deps import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
