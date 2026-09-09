# Audio Daily Digest

Daily news digest: scrape RSS sources, summarize into a spoken-style script via an LLM,
synthesize speech, and serve it through a small API + frontend (plus optional Telegram push).

See `CLAUDE.md` for the full project context and phased roadmap.

## Setup

```bash
cp .env.example .env   # fill in ANTHROPIC_API_KEY, API_KEY, etc.
uv sync
```

## Run the API locally

```bash
uv run uvicorn audio_digest.api.app:app --reload
```

- `GET /api/digest/today` — today's digest as JSON
- `GET /api/digest/today/audio` — today's digest MP3
- `POST /api/trigger-digest` (header `X-API-Key: <API_KEY>`) — trigger a new run

## Choosing a summarizer

Set `SUMMARIZER_PROVIDER` in `.env`:

- `claude` (default) — needs `ANTHROPIC_API_KEY`
- `openrouter` — needs `OPENROUTER_API_KEY` ([openrouter.ai/keys](https://openrouter.ai/keys)); model is configurable via
  `OPENROUTER_MODEL` (default `google/gemini-2.5-flash`), see the [model catalog](https://openrouter.ai/models)
  for alternatives — pick one with structured-output support

## Run once from the CLI (debugging)

```bash
uv run python -m audio_digest.cli
```

## First-time Telegram setup (optional)

1. Create a bot via [@BotFather](https://t.me/BotFather), copy its token into `TELEGRAM_BOT_TOKEN`.
2. Send the bot any message, then visit `https://api.telegram.org/bot<token>/getUpdates`
   to find your numeric `chat_id`, and set `TELEGRAM_CHAT_ID`.

## Tests

```bash
uv run pytest
uv run ruff check .
uv run mypy backend/src
```
