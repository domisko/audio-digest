"""Telegram delivery tests — the bot client is mocked, no real network call."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from audio_digest.delivery.telegram import send_digest


@pytest.mark.asyncio
async def test_send_digest_sends_audio_and_returns_message_id(tmp_path: Path) -> None:
    audio_path = tmp_path / "digest.mp3"
    audio_path.write_bytes(b"fake-mp3-bytes")

    mock_message = MagicMock(message_id=42)
    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock()
    mock_bot.send_audio = AsyncMock(return_value=mock_message)
    mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
    mock_bot.__aexit__ = AsyncMock(return_value=False)

    with patch("audio_digest.delivery.telegram.telegram.Bot", return_value=mock_bot):
        message_id = await send_digest(
            "token", "chat-id", audio_path, caption="Digest for today", text="Guten Morgen..."
        )

    assert message_id == "42"
    mock_bot.send_message.assert_awaited_once_with(chat_id="chat-id", text="Guten Morgen...")
    mock_bot.send_audio.assert_awaited_once()
