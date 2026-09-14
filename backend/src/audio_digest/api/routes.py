"""API routes: read today's digest, and trigger a new run."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse

from audio_digest.api.deps import get_effective_settings, get_settings, require_api_key
from audio_digest.config import Settings
from audio_digest.models import DigestResult
from audio_digest.pipeline import run_daily_digest
from audio_digest.settings_store import EditableSettings, load_overrides, save_overrides
from audio_digest.storage import latest_audio_path, load_latest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.get("/digest/today", response_model=DigestResult)
def get_today_digest(settings: Settings = Depends(get_settings)) -> DigestResult:
    result = load_latest(settings.output_dir)
    if result is None:
        raise HTTPException(status_code=404, detail="No digest has been generated yet")
    return result


@router.get("/digest/today/audio")
def get_today_audio(settings: Settings = Depends(get_settings)) -> FileResponse:
    audio_path = latest_audio_path(settings.output_dir)
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="No digest audio has been generated yet")
    return FileResponse(audio_path, media_type="audio/mpeg")


async def _run_and_log(settings: Settings) -> None:
    try:
        await run_daily_digest(settings)
    except Exception:
        logger.exception("Digest run failed")


@router.post("/trigger-digest", status_code=202, dependencies=[Depends(require_api_key)])
def trigger_digest(
    background_tasks: BackgroundTasks, settings: Settings = Depends(get_effective_settings)
) -> dict[str, str]:
    """Kick off a digest run in the background so the caller (e.g. cron) doesn't block."""
    background_tasks.add_task(_run_and_log, settings)
    return {"status": "accepted"}


@router.get("/settings", response_model=EditableSettings, dependencies=[Depends(require_api_key)])
def get_settings_route(settings: Settings = Depends(get_effective_settings)) -> EditableSettings:
    """Return the current values of the settings a user is allowed to edit at runtime."""
    return EditableSettings(
        summarizer_provider=settings.summarizer_provider,
        openrouter_model=settings.openrouter_model,
        tts_provider=settings.tts_provider,
        edge_tts_voice=settings.edge_tts_voice,
    )


@router.put("/settings", response_model=EditableSettings, dependencies=[Depends(require_api_key)])
def update_settings(
    update: EditableSettings, settings: Settings = Depends(get_settings)
) -> EditableSettings:
    """Merge non-null fields into the persisted overrides (secrets are never touched here)."""
    overrides = load_overrides(settings.output_dir)
    overrides.update(update.model_dump(exclude_none=True))
    save_overrides(overrides, settings.output_dir)

    effective = settings.model_copy(update=overrides)
    return EditableSettings(
        summarizer_provider=effective.summarizer_provider,
        openrouter_model=effective.openrouter_model,
        tts_provider=effective.tts_provider,
        edge_tts_voice=effective.edge_tts_voice,
    )
