"""Pluggable LLM layer.

Providers, in auto-select order:
  anthropic  — Claude (needs ANTHROPIC_API_KEY)
  openai     — any OpenAI-COMPATIBLE API (OpenAI/OpenRouter/Groq/Mistral/LM Studio/vLLM…)
  ollama     — free local model (needs Ollama running; no API key)
  heuristic  — no model at all; agents fall back to pure-Python analysis

Agents should call `analyze_json(prompt, fallback=...)`. If a real LLM is
available it is used; otherwise (or on error) the agent's `fallback()` runs,
so every agent produces output with zero keys and zero models installed.
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import get_settings

_anthropic_client = None


# ---------------------------------------------------------------- provider select
def provider() -> str:
    """Resolve the active provider name."""
    s = get_settings()
    choice = (s.llm_provider or "auto").lower()
    if choice != "auto":
        return choice
    if s.anthropic_api_key:
        return "anthropic"
    if s.openai_api_key:
        return "openai"
    if _ollama_up():
        return "ollama"
    return "heuristic"


def has_llm() -> bool:
    return provider() in ("anthropic", "openai", "ollama")


def status() -> dict:
    """Active provider + which backends are configured (for the UI / transparency)."""
    s = get_settings()
    p = provider()
    model = {
        "anthropic": s.anthropic_model,
        "openai": s.openai_model,
        "ollama": s.ollama_model,
        "heuristic": None,
    }.get(p)
    return {
        "provider": p,
        "model": model,
        "has_llm": has_llm(),
        "available": {
            "anthropic": bool(s.anthropic_api_key),
            "openai": bool(s.openai_api_key),
            "ollama": _ollama_up(),
            "heuristic": True,
        },
    }


def _ollama_up() -> bool:
    s = get_settings()
    try:
        httpx.get(f"{s.ollama_base_url}/api/tags", timeout=1.5).raise_for_status()
        return True
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------- text completion
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def complete(
    prompt: str,
    *,
    system: str | None = None,
    model: str | None = None,
    max_tokens: int = 2000,
    temperature: float = 0.2,
) -> str:
    system = system or "You are an expert analyst. Be precise and concise."
    p = provider()
    if p == "anthropic":
        return _anthropic(prompt, system, model, max_tokens, temperature)
    if p == "openai":
        return _openai(prompt, system, model, max_tokens, temperature)
    if p == "ollama":
        return _ollama(prompt, system, model, temperature)
    raise RuntimeError("No LLM provider available (heuristic mode).")


def complete_json(prompt: str, **kwargs: Any) -> Any:
    kwargs.setdefault(
        "system",
        "You are an expert analyst. Respond ONLY with valid JSON, no prose, no markdown fences.",
    )
    return _extract_json(complete(prompt, **kwargs))


def analyze_json(prompt: str, *, fallback: Callable[[], Any], **kwargs: Any) -> Any:
    """Use the LLM if available; otherwise (or on any failure) run the heuristic fallback."""
    if not has_llm():
        return fallback()
    try:
        return complete_json(prompt, **kwargs)
    except Exception:  # noqa: BLE001
        return fallback()


# ---------------------------------------------------------------- backends
def _anthropic(prompt, system, model, max_tokens, temperature) -> str:
    global _anthropic_client
    from anthropic import Anthropic

    s = get_settings()
    if _anthropic_client is None:
        _anthropic_client = Anthropic(api_key=s.anthropic_api_key)
    msg = _anthropic_client.messages.create(
        model=model or s.anthropic_model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in msg.content if b.type == "text")


def _openai(prompt, system, model, max_tokens, temperature) -> str:
    s = get_settings()
    # Agents may request a claude-* model for "deep" steps; map those to the configured model.
    use_model = s.openai_model if (not model or model.startswith("claude")) else model
    with httpx.Client(timeout=s.scraper_timeout * 3) as c:
        r = c.post(
            f"{s.openai_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {s.openai_api_key}"},
            json={
                "model": use_model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


def _ollama(prompt, system, model, temperature) -> str:
    s = get_settings()
    with httpx.Client(timeout=s.scraper_timeout * 3) as c:
        r = c.post(
            f"{s.ollama_base_url}/api/chat",
            json={
                "model": model_for_ollama(model),
                "stream": False,
                "options": {"temperature": temperature},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
        )
        r.raise_for_status()
        return r.json()["message"]["content"]


def model_for_ollama(model: str | None) -> str:
    # Claude model ids don't exist in Ollama; map anything claude-* to the configured local model.
    s = get_settings()
    if not model or model.startswith("claude"):
        return s.ollama_model
    return model


# ---------------------------------------------------------------- json extraction
def _extract_json(text: str) -> Any:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if m:
            return json.loads(m.group(1))
        raise
