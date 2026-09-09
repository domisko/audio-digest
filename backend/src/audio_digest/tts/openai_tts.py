"""OpenAI TTS — not yet implemented.

Would use `client.audio.speech.create(model=..., voice=..., input=text)` and
stream the response to `output_path`.
"""

from pathlib import Path

from audio_digest.tts.base import TextToSpeech


class OpenAITTS(TextToSpeech):
    def __init__(self, api_key: str, voice: str = "alloy"):
        self._api_key = api_key
        self._voice = voice

    async def synthesize(self, text: str, output_path: Path) -> Path:
        raise NotImplementedError("OpenAI TTS is not implemented yet")
