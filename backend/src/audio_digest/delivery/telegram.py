"""Telegram delivery: push the finished MP3 to a chat via bot API.

Optional — the frontend is the primary delivery surface now, but Telegram is
kept as a secondary push channel since it costs nothing to keep. Only used
when TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are configured.
"""

from pathlib import Path

import telegram


async def send_digest(
    bot_token: str, chat_id: str, audio_path: Path, caption: str, text: str
) -> str:
    """Send the newsletter text followed by the audio file, returning the audio message id."""
    bot = telegram.Bot(token=bot_token)
    async with bot:
        # Telegram's caption field is capped at 1024 chars, too short for a full
        # digest — send the readable text as its own message instead.
        await bot.send_message(chat_id=chat_id, text=text)
        with audio_path.open("rb") as audio_file:
            message = await bot.send_audio(
                chat_id=chat_id,
                audio=audio_file,
                caption=caption,
                title=caption,
            )
    return str(message.message_id)
