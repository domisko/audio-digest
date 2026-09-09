"""TTS tests. edge_tts.Communicate is mocked so CI doesn't need network access."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from audio_digest.tts.edge import EdgeTTS


@pytest.mark.asyncio
async def test_synthesize_writes_file(tmp_path: Path) -> None:
    output_path = tmp_path / "digest.mp3"
    tts = EdgeTTS(voice="en-US-GuyNeural")

    with patch("audio_digest.tts.edge.edge_tts.Communicate") as mock_communicate_cls:
        mock_communicate = mock_communicate_cls.return_value
        mock_communicate.save = AsyncMock()

        result = await tts.synthesize("Hello, world.", output_path)

        mock_communicate_cls.assert_called_once_with("Hello, world.", "en-US-GuyNeural")
        mock_communicate.save.assert_awaited_once_with(str(output_path))
        assert result == output_path
        assert output_path.parent.exists()


@pytest.mark.asyncio
async def test_synthesize_with_words_writes_audio_and_returns_timings(tmp_path: Path) -> None:
    output_path = tmp_path / "digest.mp3"
    tts = EdgeTTS(voice="de-DE-SeraphinaMultilingualNeural")

    async def fake_stream():
        yield {"type": "WordBoundary", "offset": 500_000, "duration": 4_750_000, "text": "Guten"}
        yield {"type": "audio", "data": b"abc"}
        yield {"type": "WordBoundary", "offset": 5_250_000, "duration": 5_750_000, "text": "Morgen"}
        yield {"type": "audio", "data": b"def"}

    with patch("audio_digest.tts.edge.edge_tts.Communicate") as mock_communicate_cls:
        mock_communicate = mock_communicate_cls.return_value
        mock_communicate.stream = fake_stream

        words = await tts.synthesize_with_words("Guten Morgen", output_path)

        mock_communicate_cls.assert_called_once_with(
            "Guten Morgen", "de-DE-SeraphinaMultilingualNeural", boundary="WordBoundary"
        )
        assert output_path.read_bytes() == b"abcdef"
        assert [w.text for w in words] == ["Guten", "Morgen"]
        assert words[0].start_seconds == 0.05
        assert words[1].start_seconds == 0.525
