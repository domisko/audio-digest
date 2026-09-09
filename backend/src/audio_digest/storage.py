"""Persist and read back "the latest digest" — no database needed for a single-record MVP.

The frontend only ever shows today's digest, so a fixed-path overwrite is enough:
each run replaces output/latest.json and output/latest.mp3.
"""

from pathlib import Path

from audio_digest.models import DigestResult

LATEST_JSON_NAME = "latest.json"
LATEST_AUDIO_NAME = "latest.mp3"


def latest_json_path(output_dir: Path) -> Path:
    return output_dir / LATEST_JSON_NAME


def latest_audio_path(output_dir: Path) -> Path:
    return output_dir / LATEST_AUDIO_NAME


def save_latest(result: DigestResult, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    latest_json_path(output_dir).write_text(result.model_dump_json(indent=2))


def load_latest(output_dir: Path) -> DigestResult | None:
    path = latest_json_path(output_dir)
    if not path.exists():
        return None
    return DigestResult.model_validate_json(path.read_text())
