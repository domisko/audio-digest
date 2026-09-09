"""Manual local entrypoint for running the pipeline without the API — useful for debugging."""

import asyncio
import logging

from audio_digest.api.deps import get_settings
from audio_digest.pipeline import run_daily_digest


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    result = asyncio.run(run_daily_digest(settings))
    print(f"Digest delivered: {result.audio_path}")


if __name__ == "__main__":
    main()
