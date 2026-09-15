"""Shared FastAPI dependencies: settings and API-key auth."""

from functools import lru_cache

from fastapi import Header, HTTPException

from audio_digest.config import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values are loaded from the environment/.env


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")
