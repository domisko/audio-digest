# Audio Daily Digest

## What it does
A personal daily habit tool: every morning, scrape a handful of news sources, have an LLM
summarize them into a casual radio-style script, convert that to speech (TTS), and deliver an
MP3 the user can listen to (e.g. while driving). Real daily-use value, not a tutorial clone.

Deliberately scoped down from a fancier original idea: skip bias-scoring / fact-checking beyond
a clearly-labeled subjective tone observation (LLMs are unreliable at authoritative
fact-checking — don't ship false confidence).

## Architecture
- Backend (`backend/`): FastAPI app exposing a public read endpoint and an API-key-protected
  trigger endpoint; scraper/summarizer/TTS/delivery are separate modules
- Frontend (`frontend/`): a small static page (no build step) showing today's digest
- Both run as separate Docker containers (see `docker-compose.yml`)
- Currently deployed via Docker Compose only — no Kubernetes involved yet

## Constraints / decisions already made
- No fabricated "fact-checking" claims — frame any misinformation-adjacent feature as tone/bias
  observation at most, clearly labeled as subjective and AI-generated, never authoritative
- Keep it modular (scraper / summarizer / TTS / delivery as separate concerns) — if a news site
  changes its markup, only the scraper module should break
- The digest script is always German; TTS voice and prompts are tuned accordingly
- Don't over-build before the MVP is genuinely in daily use
