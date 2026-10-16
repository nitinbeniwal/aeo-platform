"""Competitor intelligence agent.

Pipeline:
  1. Scrape the competitor URL (rendered if needed) + a few key internal pages
     (pricing / product / about discovered from links).
  2. Optionally scrape your comparable page.
  3. Ask Claude to extract structured intel (pricing, positioning, messaging,
     features) and, when your page is supplied, a head-to-head diff + gaps.
"""
from __future__ import annotations

import json
import re

from .. import heuristics
from ..llm import analyze_json
from ..scrapers import web
from ..schemas import AgentResult, CompetitorRequest

_KEY_PATHS = re.compile(r"(pricing|plans|product|features|about|solutions)", re.I)


def run(req: CompetitorRequest) -> AgentResult:
    main = web.extract(req.competitor_url)

    extra_pages: list[dict] = []
    for link in main.links:
        if _KEY_PATHS.search(link) and link != req.competitor_url:
            p = web.extract(link)
            if p.ok and p.text:
                extra_pages.append({"url": link, "text_excerpt": p.text[:2500]})
            if len(extra_pages) >= 3:
                break

    your_page = None
    if req.your_url:
        yp = web.extract(req.your_url)
        your_page = {"url": req.your_url, "text_excerpt": yp.text[:3000], "ok": yp.ok}

    intel = _analyze(req, main, extra_pages, your_page)

    return AgentResult(
        agent="competitor",
        summary=intel.get("summary", f"Scraped {req.competitor_url} + {len(extra_pages)} internal pages."),
        findings=intel.get("findings", []),
        recommendations=intel.get("recommendations", []),
        raw={
            "competitor_url": req.competitor_url,
            "pages_scraped": 1 + len(extra_pages),
            "intel": intel,
        },
    )


def _analyze(req: CompetitorRequest, main, extra_pages: list[dict], your_page) -> dict:
    context = json.dumps(
        {
            "focus": req.focus,
            "competitor": {
                "url": req.competitor_url,
                "title": main.title,
                "text_excerpt": main.text[:3500],
                "internal_pages": extra_pages,
            },
            "you": your_page,
        },
        ensure_ascii=False,
    )
    diff_clause = (
        'Also include "head_to_head": array of {dimension, competitor, you, advantage} objects.'
        if your_page
        else ""
    )
    prompt = (
        "You are a competitive-intelligence analyst. Given the scraped competitor content below, "
        f"extract structured intel focused on: {', '.join(req.focus)}.\n{context}\n\n"
        "Return a JSON object with keys:\n"
        '  "summary": 2-sentence executive summary,\n'
        '  "findings": array of {dimension, detail} covering pricing, positioning, messaging, features,\n'
        '  "recommendations": array of 5 actions for us to compete/differentiate.\n'
        f"  {diff_clause}\n"
        "Return ONLY the JSON object."
    )
    data = analyze_json(
        prompt,
        fallback=lambda: _heuristic_intel(req, main, extra_pages, your_page),
        model="claude-opus-4-8",
        max_tokens=1800,
    )
    return data if isinstance(data, dict) else _heuristic_intel(req, main, extra_pages, your_page)


_FEATURE_SIGNALS = [
    "free trial", "free plan", "enterprise", "api", "integrations", "sso", "self-hosted",
    "open source", "on-premise", "money-back", "no credit card", "24/7 support", "sla",
    "gdpr", "soc 2", "analytics", "automation", "ai", "mobile app",
]


def _heuristic_intel(req: CompetitorRequest, main, extra_pages: list[dict], your_page) -> dict:
    """Keyless competitor intel from scraped text: prices, features, top messaging terms."""
    all_text = main.text + " " + " ".join(p.get("text_excerpt", "") for p in extra_pages)
    prices = heuristics.extract_prices(all_text)
    features = heuristics.detect_features(all_text, _FEATURE_SIGNALS)
    top = [t for t, _ in heuristics.top_terms(all_text, 12)]

    findings = [
        {"dimension": "pricing", "detail": ", ".join(prices) if prices else "no explicit prices found on scraped pages"},
        {"dimension": "features", "detail": ", ".join(features) if features else "no standout feature signals detected"},
        {"dimension": "messaging", "detail": f"dominant terms: {', '.join(top[:8])}"},
        {"dimension": "positioning", "detail": f"page title: {main.title!r}"},
    ]

    recs = [
        "Counter their pricing visibility — publish a transparent pricing/comparison page."
        if prices
        else "They hide pricing; a clear public pricing page is a differentiator you can own.",
        f"They emphasize: {', '.join(features[:5]) or 'few explicit features'} — match table-stakes, highlight what they lack.",
        f"Their messaging centers on {', '.join(top[:4])}; differentiate with a distinct angle.",
        "Target the buyer questions their page answers and answer them better for SEO/AEO.",
        "Create a direct 'you vs them' comparison page to capture their branded searches.",
    ]

    head_to_head = []
    if your_page and your_page.get("ok"):
        your_prices = heuristics.extract_prices(your_page.get("text_excerpt", ""))
        your_features = heuristics.detect_features(your_page.get("text_excerpt", ""), _FEATURE_SIGNALS)
        head_to_head = [
            {"dimension": "pricing shown", "competitor": bool(prices), "you": bool(your_prices),
             "advantage": "you" if your_prices and not prices else "competitor" if prices and not your_prices else "tie"},
            {"dimension": "feature signals", "competitor": len(features), "you": len(your_features),
             "advantage": "you" if len(your_features) > len(features) else "competitor" if len(features) > len(your_features) else "tie"},
        ]

    return {
        "summary": f"Scraped {req.competitor_url} + {len(extra_pages)} internal pages. "
        f"Found {len(prices)} price points and {len(features)} feature signals.",
        "findings": findings,
        "recommendations": recs,
        "head_to_head": head_to_head,
        "_mode": "heuristic (no LLM) — set ANTHROPIC_API_KEY or run Ollama for deeper analysis",
    }
