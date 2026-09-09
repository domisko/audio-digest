"""Shared test fixtures."""

import os

import pytest


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide known env vars for every test, overriding whatever a local .env has.

    pydantic-settings reads .env from disk regardless of the test process's cwd
    tricks; env vars take priority over it, so setting them here — including
    ones with class defaults — keeps tests deterministic on any developer machine.
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("API_KEY", "test-api-key")
    monkeypatch.setenv("SUMMARIZER_PROVIDER", "claude")
    monkeypatch.setenv("TTS_PROVIDER", "edge")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")
    for var in ("OPENAI_API_KEY", "OPENROUTER_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        os.environ.pop(var, None)

    from audio_digest.api.deps import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
