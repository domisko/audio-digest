"""Text-to-speech interface — implementations are interchangeable via TTS_PROVIDER."""

from abc import ABC, abstractmethod
from pathlib import Path


class TextToSpeech(ABC):
    @abstractmethod
    async def synthesize(self, text: str, output_path: Path) -> Path:
        """Render `text` to speech, writing an MP3 at `output_path`, and return that path."""
        raise NotImplementedError
