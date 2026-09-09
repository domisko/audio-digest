"""Default TTS backend: edge-tts (free, Microsoft Edge's online voices)."""

from pathlib import Path

import edge_tts

from audio_digest.tts.base import TextToSpeech


class EdgeTTS(TextToSpeech):
    def __init__(self, voice: str = "en-US-GuyNeural"):
        self._voice = voice

    async def synthesize(self, text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        communicate = edge_tts.Communicate(text, self._voice)
        await communicate.save(str(output_path))
        return output_path
