"""Pluggable LLM summarizers: turn a list of Article into a spoken-style Script."""

from audio_digest.config import Settings
from audio_digest.summarizer.base import Summarizer


def _require(value: str | None, env_var: str) -> str:
    if not value:
        raise ValueError(f"{env_var} must be set to use this SUMMARIZER_PROVIDER")
    return value


def get_summarizer(settings: Settings) -> Summarizer:
    """Factory selecting a Summarizer implementation based on SUMMARIZER_PROVIDER."""
    if settings.summarizer_provider == "claude":
        from audio_digest.summarizer.claude import ClaudeSummarizer

        return ClaudeSummarizer(api_key=_require(settings.anthropic_api_key, "ANTHROPIC_API_KEY"))
    if settings.summarizer_provider == "openai":
        from audio_digest.summarizer.openai import OpenAISummarizer

        return OpenAISummarizer(api_key=_require(settings.openai_api_key, "OPENAI_API_KEY"))
    if settings.summarizer_provider == "openrouter":
        from audio_digest.summarizer.openrouter import OpenRouterSummarizer

        return OpenRouterSummarizer(
            api_key=_require(settings.openrouter_api_key, "OPENROUTER_API_KEY"),
            model=settings.openrouter_model,
        )
    if settings.summarizer_provider == "ollama":
        from audio_digest.summarizer.ollama import OllamaSummarizer

        return OllamaSummarizer()
    raise ValueError(f"Unknown summarizer provider: {settings.summarizer_provider}")
