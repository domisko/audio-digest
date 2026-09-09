"""Default TTS backend: edge-tts (free, Microsoft Edge's online voices)."""

from pathlib import Path

import edge_tts

from audio_digest.models import WordTiming
from audio_digest.tts.base import TextToSpeech

# edge-tts reports WordBoundary offsets/durations in 100-nanosecond ticks
# (the same convention Azure Speech uses), not seconds.
TICKS_PER_SECOND = 10_000_000


class EdgeTTS(TextToSpeech):
    def __init__(self, voice: str = "en-US-GuyNeural"):
        self._voice = voice

    async def synthesize(self, text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        communicate = edge_tts.Communicate(text, self._voice)
        await communicate.save(str(output_path))
        return output_path

    async def synthesize_with_words(self, text: str, output_path: Path) -> list[WordTiming]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        communicate = edge_tts.Communicate(text, self._voice, boundary="WordBoundary")

        words: list[WordTiming] = []
        with output_path.open("wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    words.append(
                        WordTiming(
                            text=chunk["text"],
                            start_seconds=chunk["offset"] / TICKS_PER_SECOND,
                            duration_seconds=chunk["duration"] / TICKS_PER_SECOND,
                        )
                    )
        return words
