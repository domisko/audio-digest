"""FastAPI application entrypoint. Run with: uvicorn audio_digest.api.app:app"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
