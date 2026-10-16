# AEO Web

Next.js 14 (App Router, TypeScript, Tailwind) dashboard. Talks to the Python agents service and persists runs in Postgres via Prisma.

## Dev

```bash
npm install
cp .env.local.example .env.local      # set AGENTS_BASE_URL + DATABASE_URL
npx prisma generate
npx prisma migrate dev                # needs Postgres (docker compose up postgres)
npm run dev                           # http://localhost:3000
```

The agents service must be running (`AGENTS_BASE_URL`, default `http://localhost:8000`).
Postgres is optional for dev: without it the dashboard still runs agents, it just won't
persist history (the `/api/run` route swallows DB errors).

## Routes

| Path | What |
|------|------|
| `/` | Agent catalog + dynamic run form (schema-driven from `/api/agents`) |
| `/history` | Past runs (requires DB) |
| `/api/agents` | GET — proxy to agents `/agents` |
| `/api/run` | POST `{agent,input}` — runs agent, persists, returns result |
| `/api/runs` | GET — recent runs |

The run form is generated automatically from each agent's JSON input schema, so new agents
registered in the Python service appear in the UI with no frontend changes.
