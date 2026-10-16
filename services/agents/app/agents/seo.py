"""SEO / Content agent.

Pipeline:
  1. Scrape the SERP for the target keyword.
  2. Extract the content of the top organic results.
  3. Find your current rank (if domain provided).
  4. Ask Claude to produce: search intent, content gaps vs. ranking pages,
     and an optimized content brief (H2s, entities, questions to answer).
"""
from __future__ import annotations

import json

from .. import heuristics
from ..llm import analyze_json
from ..scrapers import serp, web
from ..schemas import AgentResult, SEORequest

_TOP_N_TO_SCRAPE = 5


def run(req: SEORequest) -> AgentResult:
    results = serp.search(req.keyword, limit=req.serp_limit)

    your_rank: int | None = None
    domain_l = (req.domain or "").lower()
    if domain_l:
        for r in results:
            if domain_l in r.url.lower():
                your_rank = r.rank
                break

    pages: list[dict] = []
    for r in results[:_TOP_N_TO_SCRAPE]:
        page = web.extract(r.url)
        pages.append(
            {
                "rank": r.rank,
                "url": r.url,
                "title": page.title or r.title,
                "text_excerpt": page.text[:3000],
                "ok": page.ok,
            }
        )

    brief = _brief(req, results, pages)

    findings = [
        {"rank": r.rank, "title": r.title, "url": r.url, "snippet": r.snippet} for r in results
    ]
    summary = (
        f"Analyzed top {len(results)} results for '{req.keyword}'. "
        + (f"Your domain ranks #{your_rank}." if your_rank else "Your domain not found in results.")
    )

    return AgentResult(
        agent="seo",
        summary=summary,
        score=float(max(0, 100 - (your_rank - 1) * 10)) if your_rank else None,
        findings=findings,
        recommendations=brief.get("recommendations", []),
        raw={"your_rank": your_rank, "brief": brief, "scraped_pages": len(pages)},
    )


def _brief(req: SEORequest, results, pages: list[dict]) -> dict:
    context = json.dumps(
        {
            "keyword": req.keyword,
            "serp": [{"rank": r.rank, "title": r.title, "snippet": r.snippet} for r in results],
            "top_pages": pages,
        },
        ensure_ascii=False,
    )
    prompt = (
        f"You are an SEO content strategist. Keyword: '{req.keyword}'.\n"
        f"Here is the live SERP and the extracted content of the top-ranking pages:\n{context}\n\n"
        "Produce a JSON object with keys:\n"
        '  "intent": one sentence on the dominant search intent,\n'
        '  "content_gaps": array of topics/entities the ranking pages cover that a new page must include,\n'
        '  "outline": array of H2/H3 headings for a page designed to outrank them,\n'
        '  "questions_to_answer": array of PAA-style questions,\n'
        '  "recommendations": array of 5 concrete optimization actions.\n'
        "Return ONLY the JSON object."
    )
    data = analyze_json(
        prompt,
        fallback=lambda: _heuristic_brief(req, pages),
        model="claude-opus-4-8",
        max_tokens=1800,
    )
    return data if isinstance(data, dict) else _heuristic_brief(req, pages)


def _heuristic_brief(req: SEORequest, pages: list[dict]) -> dict:
    """Keyless content brief: term-frequency gap analysis over the ranking pages."""
    corpus = " ".join(p.get("text_excerpt", "") for p in pages)
    titles = " ".join(p.get("title", "") for p in pages)
    gaps = heuristics.content_gaps(set(heuristics.tokens(req.keyword)), corpus, n=15)
    top = [t for t, _ in heuristics.top_terms(corpus, 12)]
    outline = [f"What is {req.keyword}?", f"Best {req.keyword} options compared"] + [
        f"{g.title()}" for g in gaps[:6]
    ]
    return {
        "intent": heuristics.classify_intent(req.keyword),
        "content_gaps": gaps,
        "outline": outline,
        "questions_to_answer": [
            f"What is the best {req.keyword}?",
            f"How much does {req.keyword} cost?",
            f"{req.keyword} vs alternatives?",
        ],
        "recommendations": [
            f"Cover these high-frequency topics the ranking pages share: {', '.join(gaps[:8]) or 'n/a'}.",
            f"Target the dominant intent: {heuristics.classify_intent(req.keyword)}.",
            f"Work your primary terms into titles/H2s (observed leaders emphasize: {', '.join(top[:6])}).",
            "Match or exceed the depth of the top result; add a comparison table and FAQ schema.",
            "Earn links/mentions from the cited domains in the SERP to compete on authority.",
        ],
        "_mode": "heuristic (no LLM) — set ANTHROPIC_API_KEY or run Ollama for richer briefs",
        "titles_analyzed": titles[:300],
    }
