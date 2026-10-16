# AEO Platform

[![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](./.github/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

Open-source, **provider-agnostic** **Answer Engine Optimization + SEO/content + competitor intelligence** platform.

Three working agents backed by real web scrapers. **Bring your own model** — run it fully free with no keys (heuristic or local Ollama), or plug in any LLM: Anthropic Claude, OpenAI, OpenRouter, Groq, Mistral, LM Studio, vLLM — anything OpenAI-compatible. Exposed through a Next.js dashboard and a FastAPI agent service.

## Architecture

```
AEO/
├── apps/web            Next.js 14 (TypeScript) — dashboard + API routes + Prisma/Postgres
├── services/agents     FastAPI (Python) — agents, scrapers, LLM analysis
├── docker-compose.yml  Postgres + agent service + web
└── .env.example
```

```
Browser ──▶ Next.js (apps/web) ──▶ /api/* ──▶ FastAPI (services/agents) ──▶ scrapers + Claude
                 │                                        │
              Postgres (jobs, runs, results)         Playwright / trafilatura / httpx
```

## Agents

| Agent | What it does | Scrapers / sources |
|-------|--------------|--------------------|
| **AEO** | Runs your prompts across answer engines, detects brand mentions + citations, scores visibility, recommends fixes | Perplexity/OpenAI/Claude APIs, live web |
| **SEO / Content** | Keyword + SERP analysis, content gap finder, generates optimized content briefs | Google SERP scrape, page content extraction |
| **Competitor Intel** | Scrapes competitor sites (pricing, positioning, messaging), summarizes + diffs vs. you | Playwright + trafilatura |

## Quick start

### Option A — Docker (everything)

```bash
cp .env.example .env          # works as-is (heuristic mode). Add keys later to upgrade quality.
docker compose up --build
# web:    http://localhost:3000
# agents: http://localhost:8000/docs
```

### Option B — local dev

```bash
# 1. Agent service
cd services/agents
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env          # add ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000

# 2. Web (new terminal)
cd apps/web
npm install
cp .env.local.example .env.local
npx prisma migrate dev        # needs a running Postgres (see docker-compose for one)
npm run dev
```

## Bring your own model (or none)

`LLM_PROVIDER=auto` picks the best available tier. **No key is ever required** — scrapers are always keyless; only the *analysis* layer changes.

| Tier | Setup | Quality | Cost |
|------|-------|---------|------|
| **heuristic** | nothing (default) | Good — live scraping + rule-based analysis (TF content-gaps, price/feature extraction, SERP-presence scoring) | **Free** |
| **ollama** | install [Ollama](https://ollama.com), `ollama pull llama3.2` | Better — real local LLM, private | **Free** |
| **openai-compatible** | `OPENAI_API_KEY` + `OPENAI_BASE_URL` + `OPENAI_MODEL` | Best — your choice of OpenAI / OpenRouter / Groq / Mistral / Together / LM Studio / vLLM | Your plan |
| **anthropic** | `ANTHROPIC_API_KEY` | Best — Claude | Paid |

The dashboard shows the active engine as a badge. Switch tiers anytime by editing `.env` — no code changes.

### Point `openai-compatible` at any provider

```bash
# OpenAI
OPENAI_BASE_URL=https://api.openai.com/v1      OPENAI_MODEL=gpt-4o-mini
# OpenRouter (hundreds of models, one key)
OPENAI_BASE_URL=https://openrouter.ai/api/v1   OPENAI_MODEL=meta-llama/llama-3.1-70b-instruct
# Groq (fast + free tier)
OPENAI_BASE_URL=https://api.groq.com/openai/v1 OPENAI_MODEL=llama-3.3-70b-versatile
# LM Studio (local, no key)
OPENAI_BASE_URL=http://localhost:1234/v1       OPENAI_MODEL=<loaded-model>
```

### Optional keys (enhance, never required)

| Key | Enhances |
|-----|----------|
| `PERPLEXITY_API_KEY` | AEO — probe real Perplexity answers + citations |
| `DATABASE_URL` | Persist run history (agents run fine without it) |

## Contributing

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Keyless-first, provider-agnostic. Licensed under [MIT](LICENSE).

## Roadmap

- [ ] Scheduled monitoring + visibility-over-time charts
- [ ] More answer engines (Google AI Overviews, Gemini, Copilot)
- [ ] Auth + multi-tenant workspaces
- [ ] Background job queue for large batches
- [ ] Export reports (PDF/CSV)

See `services/agents/README.md` for agent internals and `apps/web/README.md` for the dashboard.
