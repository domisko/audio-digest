"""Runtime-editable settings overrides, persisted alongside the digest output.

Secrets (API keys, Telegram config) always come from the environment/.env and
are never stored or exposed here — only the non-secret knobs someone might
want to tweak from the settings UI without redeploying (provider choice,
model, voice) are editable this way.
"""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

SETTINGS_FILE_NAME = "settings_overrides.json"


class EditableSettings(BaseModel):
    """Partial overrides for the non-secret Settings fields. Unset fields are left as-is."""

    summarizer_provider: Literal["claude", "openai", "ollama", "openrouter"] | None = None
    openrouter_model: str | None = None
    tts_provider: Literal["edge", "openai", "elevenlabs"] | None = None
    edge_tts_voice: str | None = None


def _path(output_dir: Path) -> Path:
    return output_dir / SETTINGS_FILE_NAME


def load_overrides(output_dir: Path) -> dict[str, str]:
    path = _path(output_dir)
    if not path.exists():
        return {}
    return dict(json.loads(path.read_text()))


def save_overrides(overrides: dict[str, str], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _path(output_dir).write_text(json.dumps(overrides, indent=2))
