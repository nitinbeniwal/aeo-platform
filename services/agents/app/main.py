from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import llm, registry
from .schemas import AgentInfo, AgentResult, RunRequest

app = FastAPI(
    title="AEO Agents Service",
    version="0.1.0",
    description="Working agents for Answer Engine Optimization, SEO/content, and competitor intel.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# agents do blocking I/O (httpx sync, playwright sync); run off the event loop
_pool = ThreadPoolExecutor(max_workers=4)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/providers")
def providers() -> dict:
    """Active LLM provider + which backends are configured."""
    return llm.status()


@app.get("/agents", response_model=list[AgentInfo])
def agents() -> list[AgentInfo]:
    return registry.list_agents()


@app.post("/run", response_model=AgentResult)
async def run(req: RunRequest) -> AgentResult:
    import asyncio

    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(_pool, registry.run_agent, req.agent, req.input)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {req.agent}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))
