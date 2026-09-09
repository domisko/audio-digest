"""ElevenLabs TTS — not yet implemented.

Would use the ElevenLabs SDK's `generate()` call and write the resulting
audio bytes to `output_path`.
"""

from pathlib import Path

from audio_digest.tts.base import TextToSpeech


class ElevenLabsTTS(TextToSpeech):
    def __init__(self, api_key: str, voice: str = "Rachel"):
        self._api_key = api_key
        self._voice = voice

    async def synthesize(self, text: str, output_path: Path) -> Path:
        raise NotImplementedError("ElevenLabs TTS is not implemented yet")
