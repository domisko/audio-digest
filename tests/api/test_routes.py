"""API route tests, including the trigger endpoint's auth check."""

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from audio_digest.models import Article, DigestResult, Script, ScriptSegment
from fastapi.testclient import TestClient


def _digest_result() -> DigestResult:
    return DigestResult(
        digest_date=date.today(),
        articles_used=[
            Article.model_validate(
                {
                    "source": "test",
                    "source_display_name": "Test",
                    "title": "Title",
                    "url": "https://example.com/a",
                    "published_at": "2026-09-06T08:00:00Z",
                    "summary_raw": "summary",
                    "fetched_at": "2026-09-06T08:00:00Z",
                    "category": "general_news",
                }
            )
        ],
        script=Script(
            digest_date=date.today(),
            intro="Hi",
            segments=[
                ScriptSegment(
                    source_article_url="https://example.com/a",
                    headline="H",
                    narration="N",
                    summary_short="S",
                )
            ],
            outro="Bye",
            full_text="Hi N Bye",
        ),
        audio_path="output/latest.mp3",
        delivered=True,
    )


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    from audio_digest.api.app import app
    from audio_digest.api.deps import get_settings

    get_settings.cache_clear()
    return TestClient(app)


def test_get_today_digest_returns_404_when_missing(client: TestClient) -> None:
    response = client.get("/api/digest/today")

    assert response.status_code == 404


def test_get_today_digest_returns_saved_digest(client: TestClient, tmp_path: Path) -> None:
    from audio_digest.storage import save_latest

    save_latest(_digest_result(), tmp_path)

    response = client.get("/api/digest/today")

    assert response.status_code == 200
    assert response.json()["script"]["intro"] == "Hi"


def test_trigger_digest_requires_api_key(client: TestClient) -> None:
    response = client.post("/api/trigger-digest")

    assert response.status_code == 401


def test_trigger_digest_rejects_wrong_api_key(client: TestClient) -> None:
    response = client.post("/api/trigger-digest", headers={"X-API-Key": "wrong"})

    assert response.status_code == 401


def test_trigger_digest_accepts_correct_api_key(client: TestClient) -> None:
    with patch("audio_digest.api.routes.run_daily_digest"):
        response = client.post("/api/trigger-digest", headers={"X-API-Key": "test-api-key"})

    assert response.status_code == 202


def test_get_settings_requires_api_key(client: TestClient) -> None:
    response = client.get("/api/settings")

    assert response.status_code == 401


def test_get_settings_returns_defaults(client: TestClient) -> None:
    response = client.get("/api/settings", headers={"X-API-Key": "test-api-key"})

    assert response.status_code == 200
    assert response.json() == {
        "summarizer_provider": "claude",
        "openrouter_model": "google/gemini-2.5-flash",
        "tts_provider": "edge",
        "edge_tts_voice": "de-DE-SeraphinaMultilingualNeural",
    }


def test_put_settings_requires_api_key(client: TestClient) -> None:
    response = client.put("/api/settings", json={"tts_provider": "openai"})

    assert response.status_code == 401


def test_put_settings_persists_and_merges_partial_update(client: TestClient) -> None:
    first = client.put(
        "/api/settings",
        headers={"X-API-Key": "test-api-key"},
        json={"tts_provider": "openai"},
    )
    assert first.status_code == 200
    assert first.json()["tts_provider"] == "openai"
    # Untouched fields keep their (default) value.
    assert first.json()["summarizer_provider"] == "claude"

    second = client.put(
        "/api/settings",
        headers={"X-API-Key": "test-api-key"},
        json={"summarizer_provider": "openrouter"},
    )
    assert second.status_code == 200
    # Previous override survives a later, unrelated partial update.
    assert second.json()["tts_provider"] == "openai"
    assert second.json()["summarizer_provider"] == "openrouter"

    readback = client.get("/api/settings", headers={"X-API-Key": "test-api-key"})
    assert readback.json()["tts_provider"] == "openai"
    assert readback.json()["summarizer_provider"] == "openrouter"
