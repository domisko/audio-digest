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
