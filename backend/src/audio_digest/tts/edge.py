"""Default TTS backend: edge-tts (free, Microsoft Edge's online voices)."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

import edge_tts
from edge_tts.exceptions import NoAudioReceived

from audio_digest.models import WordTiming
from audio_digest.tts.base import TextToSpeech

# edge-tts reports WordBoundary offsets/durations in 100-nanosecond ticks
# (the same convention Azure Speech uses), not seconds.
TICKS_PER_SECOND = 10_000_000

logger = logging.getLogger(__name__)

# The free Edge endpoint intermittently answers with no audio at all
# (NoAudioReceived), even for text that synthesizes fine on the next try.
MAX_ATTEMPTS = 4
RETRY_DELAY_SECONDS = 2.0


async def _with_retries[T](operation: Callable[[], Awaitable[T]]) -> T:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return await operation()
        except NoAudioReceived:
            if attempt == MAX_ATTEMPTS:
                raise
            logger.warning("Edge TTS returned no audio (attempt %d/%d)", attempt, MAX_ATTEMPTS)
            await asyncio.sleep(RETRY_DELAY_SECONDS * attempt)
    raise AssertionError("unreachable")


class EdgeTTS(TextToSpeech):
    def __init__(self, voice: str = "en-US-GuyNeural"):
        self._voice = voice

    async def synthesize(self, text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        async def attempt() -> None:
            await edge_tts.Communicate(text, self._voice).save(str(output_path))

        await _with_retries(attempt)
        return output_path

    async def synthesize_with_words(self, text: str, output_path: Path) -> list[WordTiming]:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        async def attempt() -> list[WordTiming]:
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

        return await _with_retries(attempt)
