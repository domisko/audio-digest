"""Telegram delivery: push the finished MP3 to a chat via bot API.

Optional — the frontend is the primary delivery surface now, but Telegram is
kept as a secondary push channel since it costs nothing to keep. Only used
when TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are configured.
"""

from pathlib import Path

import telegram


async def send_digest(bot_token: str, chat_id: str, audio_path: Path, caption: str) -> str:
    """Send `audio_path` to `chat_id`, returning the resulting Telegram message id."""
    bot = telegram.Bot(token=bot_token)
    async with bot:
        with audio_path.open("rb") as audio_file:
            message = await bot.send_audio(
                chat_id=chat_id,
                audio=audio_file,
                caption=caption,
                title=caption,
            )
    return str(message.message_id)
