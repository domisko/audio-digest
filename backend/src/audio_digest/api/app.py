"""FastAPI application entrypoint. Run with: uvicorn audio_digest.api.app:app"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from audio_digest.api.deps import get_settings
from audio_digest.api.routes import router

app = FastAPI(title="Audio Daily Digest")

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router)

# The frontend is a static, no-build page bundled into the same image so the
# whole app ships and runs as a single container. Mounted last (and at root)
# so it doesn't shadow the /api routes above.
_frontend_dir = Path(__file__).resolve().parents[4] / "frontend"
if _frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
