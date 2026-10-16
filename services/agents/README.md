# AEO Agents Service

FastAPI service exposing three working agents. Blocking scraper/LLM work runs in a thread pool.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | liveness |
| GET | `/agents` | agent catalog + JSON input schemas |
| POST | `/run` | run an agent: `{ "agent": "aeo\|seo\|competitor", "input": {...} }` |
| GET | `/docs` | Swagger UI |

## Run locally

```bash
python -m venv .venv && . .venv/Scripts/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env            # set ANTHROPIC_API_KEY
uvicorn app.main:app --reload --port 8000
```

## Example calls

```bash
# AEO — works with only ANTHROPIC_API_KEY (Claude is the always-on engine)
curl -s localhost:8000/run -H 'content-type: application/json' -d '{
  "agent":"aeo",
  "input":{"brand":"Acme CRM","domain":"acme.com",
           "prompts":["best CRM for startups","CRM with built-in email"]}}' | jq

# SEO
curl -s localhost:8000/run -H 'content-type: application/json' -d '{
  "agent":"seo",
  "input":{"keyword":"headless cms","domain":"mysite.com"}}' | jq

# Competitor
curl -s localhost:8000/run -H 'content-type: application/json' -d '{
  "agent":"competitor",
  "input":{"competitor_url":"https://stripe.com","your_url":"https://mysite.com"}}' | jq
```

## Layout

```
app/
├── main.py              FastAPI app + /run dispatch
├── registry.py          agent id -> metadata + runner
├── config.py            env settings
├── llm.py               Claude wrapper (complete / complete_json)
├── schemas.py           request/response models
├── agents/
│   ├── aeo.py           answer-engine visibility
│   ├── seo.py           SERP + content brief
│   └── competitor.py    competitor scrape + intel
└── scrapers/
    ├── web.py           httpx+trafilatura, Playwright fallback
    ├── serp.py          DuckDuckGo HTML SERP
    └── answer_engines.py Perplexity / OpenAI / Claude probes
```

## Add an agent

1. Create `app/agents/<id>.py` with `run(req) -> AgentResult`.
2. Add a request model in `schemas.py`.
3. Register it in `registry.py`. The web UI picks it up automatically from `/agents`.
