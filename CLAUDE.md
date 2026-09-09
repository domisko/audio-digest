# Audio Daily Digest

## Why this project exists
Part of a job-hunt skill-building plan (see `~/Projects/Homelab` career-ops session for full context). Goal: qualify for AI/Automation Engineer + Platform/DevOps roles in the Lausanne/Geneva area by closing three CV gaps identified from analyzing 187 real job-fit evaluations:
- Python (68 gap mentions) — candidate's real stack is TypeScript/Node.js
- Kubernetes (52 gap mentions, the single biggest theme)
- AWS/cloud (43 AWS-specific mentions, dominant over Azure/GCP)

This one project is the vehicle for all three — built in phases, not three separate throwaway exercises.

## What it does
A personal daily habit tool: every morning, scrape a handful of news sources, have an LLM summarize them into a casual radio-style script, convert that to speech (TTS), and deliver an MP3 the user can listen to (e.g. while driving). Real daily-use value, not a tutorial clone.

Deliberately scoped down from a fancier original idea: skip bias-scoring / fact-checking for the MVP (LLMs are unreliable at authoritative fact-checking — don't ship false confidence). Add back only if there's real appetite once the MVP is running.

## Phases (sequential, each one resume-worthy on completion)

**Phase 1 — Python MVP (~6 weeks)**
- Fetch articles: `feedparser` (RSS) + `BeautifulSoup`/`Playwright` for full-text extraction where needed
- Summarize via LLM into a spoken-style script (structured output, e.g. via Pydantic)
- TTS: `edge-tts` (free) as the default; OpenAI TTS / ElevenLabs as a paid upgrade path
- Delivery for MVP: simplest thing that works (e.g. drop the MP3 somewhere reachable + a Telegram link) — don't build the podcast RSS feed until Phase 1 is solid
- **Resume-ready once:** it runs daily and the user actually listens to it

**Phase 2 — Kubernetes (~1-2 weeks after Phase 1)**
- Deploy on the user's homelab via **k3s** (lightweight, single-node — NOT full kubeadm k8s)
- This is a new, isolated k3s cluster alongside the existing Docker Compose stack on the homelab server (192.168.0.100) — do NOT migrate the existing ~25 Docker Compose services to Kubernetes, there's no operational need and the box is already memory-tight (was swap-maxed once; freed by restarting open-webui/open_notebook, which were the biggest RAM/swap hogs)
- Rough resource math: k3s control plane ~0.5-1GB RAM + workload; server had ~5GB "available" after cleanup, comfortably enough
- **Resume-ready once:** it's deployed and running reliably on k3s

**Phase 3 — AWS (parallel-ish with Phase 2, or right after)**
- Use **S3** for MP3 storage + delivery (presigned URLs), not the whole compute stack — homelab k3s stays the compute, AWS is just object storage. This is a legitimate, explainable hybrid architecture for interviews.
- Separate from this: AWS Certified Solutions Architect – Associate (SAA-C03) certification is being pursued independently (see `~/Projects/Job Hunt/aws-saa-c03/`) — not tied to this project's timeline, but the S3 usage here is good hands-on practice alongside that study.
- **Resume-ready once:** S3 integration is live in the project

## Constraints / decisions already made
- No fabricated "fact-checking" claims — frame any misinformation-adjacent feature as tone/bias observation at most, not authoritative fact-checking
- Keep it modular (scraper / analyzer / TTS / delivery as separate concerns) — if a news site changes its markup, only the scraper module should break
- Don't over-build before Phase 1 MVP is genuinely in daily use
