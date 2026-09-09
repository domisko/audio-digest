"""Application settings, loaded from environment variables / .env."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration. Fails fast at startup if a required key is missing."""

    # Only the key matching `summarizer_provider` needs to actually be set.
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    openrouter_api_key: str | None = None

    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    api_key: str
    cors_origins: str = "http://localhost:5173"

    summarizer_provider: Literal["claude", "openai", "ollama", "openrouter"] = "claude"
    openrouter_model: str = "google/gemini-2.5-flash"
    tts_provider: Literal["edge", "openai", "elevenlabs"] = "edge"
    # The digest script is always German (see summarizer/prompts.py), so the
    # voice needs to be too — an English voice reading German text has a
    # heavy accent.
    edge_tts_voice: str = "de-DE-SeraphinaMultilingualNeural"

    output_dir: Path = Path("output")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS_ORIGINS as a parsed list, e.g. 'a,b' -> ['a', 'b']."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
