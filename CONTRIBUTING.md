# Contributing

Thanks for helping build an open, provider-agnostic AEO/SEO/competitor-intel platform.

## Principles

1. **Keyless-first.** Every feature must work with no API key (heuristic mode). LLMs enhance; they are never required.
2. **Bring your own model.** Never hardcode a provider. Route LLM calls through `services/agents/app/llm.py`.
3. **Scrapers degrade gracefully.** Network/parse failures return empty, not exceptions.

## Dev setup

```bash
# agents
cd services/agents
python -m venv .venv && . .venv/Scripts/activate   # or source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env            # optional: add any provider key
uvicorn app.main:app --reload --port 8000

# web
cd apps/web
npm install && cp .env.local.example .env.local
npm run dev
```

## Adding an LLM provider

Edit `services/agents/app/llm.py`:
1. Add a `_yourprovider(...)` backend function.
2. Wire it into `complete()` dispatch and `provider()` auto-resolution.
3. Add config fields in `config.py` and document them in `.env.example`.

If it speaks the OpenAI chat-completions format, you probably don't need a new
provider at all — just set `OPENAI_BASE_URL` / `OPENAI_MODEL` / `OPENAI_API_KEY`.

## Adding an agent

1. Create `services/agents/app/agents/<id>.py` exposing `run(req) -> AgentResult`.
2. Give it a `_heuristic_*` fallback that works with no LLM.
3. Add a request model in `schemas.py` and register in `registry.py`.
   The web UI picks it up automatically from `/agents` — no frontend changes.

## Before opening a PR

```bash
cd services/agents && python -m py_compile app/*.py app/**/*.py
cd apps/web && npm run build
```

Keep PRs focused. Describe which provider tier(s) you tested (heuristic / ollama / key).

## License

By contributing you agree your contributions are licensed under the [MIT License](LICENSE).
