"""Text-to-speech interface — implementations are interchangeable via TTS_PROVIDER."""

from abc import ABC, abstractmethod
from pathlib import Path

from audio_digest.models import WordTiming


class TextToSpeech(ABC):
    @abstractmethod
    async def synthesize(self, text: str, output_path: Path) -> Path:
        """Render `text` to speech, writing an MP3 at `output_path`, and return that path."""
        raise NotImplementedError

    async def synthesize_with_words(self, text: str, output_path: Path) -> list[WordTiming]:
        """Like `synthesize`, but also returns per-word timing within this clip
        (offsets relative to the start of THIS clip, not the final concatenated
        audio — the caller is responsible for shifting them).

        Default implementation: just synthesize and report no word timing, for
        backends that don't expose word boundaries. EdgeTTS overrides this.
        """
        await self.synthesize(text, output_path)
        return []
