FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY backend/src ./backend/src

# Playwright's browser binaries are NOT installed here — the extractor only
# falls back to Playwright for sources explicitly flagged needs_playwright=True.
# Add `RUN uv run playwright install --with-deps chromium` if you enable one.
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "audio_digest.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
