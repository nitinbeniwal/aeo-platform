"""Probe answer engines (and answer-engine-adjacent sources) with a query.

Engines, auto-included based on what's available:
  - serp       : KEYLESS. Scrapes the live SERP; the combined organic titles+
                 snippets are the "answer", result URLs are the "citations".
                 Always included — gives real AEO signal with zero keys.
  - ollama     : free local model, if Ollama is running (no key)
  - claude     : if ANTHROPIC_API_KEY set
  - perplexity : if PERPLEXITY_API_KEY set (returns real citations)
  - openai     : if OPENAI_API_KEY set

With no keys and no Ollama you still get the `serp` probe, so the AEO agent
always produces a result.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import httpx

from ..config import get_settings
from ..llm import complete, provider
from . import serp


@dataclass
class AnswerProbe:
    engine: str
    query: str
    answer: str = ""
    citations: list[str] = field(default_factory=list)
    ok: bool = True
    error: str | None = None


def probe_all(query: str) -> list[AnswerProbe]:
    s = get_settings()
    probes: list[AnswerProbe] = [probe_serp(query)]  # always, keyless
    if provider() == "ollama":
        probes.append(probe_ollama(query))
    if s.anthropic_api_key:
        probes.append(probe_claude(query))
    if s.perplexity_api_key:
        probes.append(probe_perplexity(query))
    if s.openai_api_key:
        probes.append(probe_openai(query))
    return probes


def probe_serp(query: str) -> AnswerProbe:
    results = serp.search(query, limit=10)
    if not results:
        return AnswerProbe(engine="serp", query=query, ok=False, error="no SERP results")
    answer = "\n".join(f"{r.title} — {r.snippet}" for r in results)
    return AnswerProbe(
        engine="serp",
        query=query,
        answer=answer,
        citations=[r.url for r in results],
    )


def probe_ollama(query: str) -> AnswerProbe:
    try:
        answer = complete(
            query,
            system="You are a helpful answer engine. Answer factually and name any brands/products you recommend.",
            max_tokens=800,
        )
        return AnswerProbe(engine="ollama", query=query, answer=answer)
    except Exception as e:  # noqa: BLE001
        return AnswerProbe(engine="ollama", query=query, ok=False, error=str(e))


def probe_claude(query: str) -> AnswerProbe:
    try:
        answer = complete(
            query,
            system="You are a helpful answer engine. Answer factually and name any brands/products you recommend.",
            max_tokens=1000,
        )
        return AnswerProbe(engine="claude", query=query, answer=answer)
    except Exception as e:  # noqa: BLE001
        return AnswerProbe(engine="claude", query=query, ok=False, error=str(e))


def probe_perplexity(query: str) -> AnswerProbe:
    s = get_settings()
    try:
        with httpx.Client(timeout=s.scraper_timeout) as c:
            r = c.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {s.perplexity_api_key}"},
                json={"model": "sonar", "messages": [{"role": "user", "content": query}]},
            )
            r.raise_for_status()
            data = r.json()
        return AnswerProbe(
            engine="perplexity",
            query=query,
            answer=data["choices"][0]["message"]["content"],
            citations=data.get("citations", []),
        )
    except Exception as e:  # noqa: BLE001
        return AnswerProbe(engine="perplexity", query=query, ok=False, error=str(e))


def probe_openai(query: str) -> AnswerProbe:
    """Probe any OpenAI-compatible endpoint (OpenAI / OpenRouter / Groq / …)."""
    s = get_settings()
    try:
        with httpx.Client(timeout=s.scraper_timeout) as c:
            r = c.post(
                f"{s.openai_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {s.openai_api_key}"},
                json={"model": s.openai_model, "messages": [{"role": "user", "content": query}]},
            )
            r.raise_for_status()
            data = r.json()
        return AnswerProbe(
            engine="openai", query=query, answer=data["choices"][0]["message"]["content"]
        )
    except Exception as e:  # noqa: BLE001
        return AnswerProbe(engine="openai", query=query, ok=False, error=str(e))
