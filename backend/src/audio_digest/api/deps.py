"""Shared FastAPI dependencies: settings and API-key auth."""

import hmac
from functools import lru_cache

from fastapi import Header, HTTPException

from audio_digest.config import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values are loaded from the environment/.env


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    # Constant-time comparison — a plain `!=` leaks how many leading bytes
    # matched via response timing, letting an attacker guess the key byte by
    # byte.
    if x_api_key is None or not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")
