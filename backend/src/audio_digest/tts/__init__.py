"""Pluggable text-to-speech backends."""

from audio_digest.config import Settings
from audio_digest.tts.base import TextToSpeech


def get_tts(settings: Settings) -> TextToSpeech:
    """Factory selecting a TextToSpeech implementation based on TTS_PROVIDER."""
    if settings.tts_provider == "edge":
        from audio_digest.tts.edge import EdgeTTS

        return EdgeTTS(voice=settings.edge_tts_voice)
    if settings.tts_provider == "openai":
        from audio_digest.tts.openai_tts import OpenAITTS

        return OpenAITTS(api_key=settings.openai_api_key or "")
    if settings.tts_provider == "elevenlabs":
        from audio_digest.tts.elevenlabs import ElevenLabsTTS

        return ElevenLabsTTS(api_key="")
    raise ValueError(f"Unknown TTS provider: {settings.tts_provider}")
