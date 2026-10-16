"""Agent registry: maps agent id -> metadata + runner.

The web layer calls /agents to render the catalog and /run to execute.
Adding a new agent = add one entry here.
"""
from __future__ import annotations

from typing import Any, Callable

from .agents import aeo, competitor, seo
from .schemas import (
    AEORequest,
    AgentInfo,
    AgentResult,
    CompetitorRequest,
    SEORequest,
)

_REGISTRY: dict[str, dict[str, Any]] = {
    "aeo": {
        "name": "AEO — Answer Engine Optimization",
        "description": "Probe AI answer engines with buyer questions, measure brand visibility + citations, recommend fixes.",
        "request_model": AEORequest,
        "runner": lambda i: aeo.run(AEORequest(**i)),
    },
    "seo": {
        "name": "SEO / Content",
        "description": "Scrape the live SERP for a keyword, analyze ranking pages, output content gaps + optimized brief.",
        "request_model": SEORequest,
        "runner": lambda i: seo.run(SEORequest(**i)),
    },
    "competitor": {
        "name": "Competitor Intelligence",
        "description": "Scrape a competitor site, extract pricing/positioning/messaging, diff vs. you, recommend moves.",
        "request_model": CompetitorRequest,
        "runner": lambda i: competitor.run(CompetitorRequest(**i)),
    },
}


def list_agents() -> list[AgentInfo]:
    return [
        AgentInfo(
            id=aid,  # type: ignore[arg-type]
            name=meta["name"],
            description=meta["description"],
            input_schema=meta["request_model"].model_json_schema(),
        )
        for aid, meta in _REGISTRY.items()
    ]


def run_agent(agent_id: str, agent_input: dict[str, Any]) -> AgentResult:
    if agent_id not in _REGISTRY:
        raise KeyError(agent_id)
    runner: Callable[[dict], AgentResult] = _REGISTRY[agent_id]["runner"]
    return runner(agent_input)
