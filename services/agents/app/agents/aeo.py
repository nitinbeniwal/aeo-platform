"""AEO agent — Answer Engine Optimization.

Pipeline:
  1. Probe each answer engine with every buyer prompt.
  2. Detect whether the brand (and domain) appear in each answer + as a citation.
  3. Compute a visibility score (mention rate weighted by engine + citation bonus).
  4. Recommend fixes (LLM if available, else keyless heuristic from the gaps).

Keyless: the `serp` probe scrapes the live SERP so visibility is measured with
zero API keys; recommendations fall back to data-driven templates.
"""
from __future__ import annotations

import json

from ..llm import analyze_json
from ..scrapers.answer_engines import probe_all
from ..schemas import AEORequest, AgentResult


def run(req: AEORequest) -> AgentResult:
    brand_l = req.brand.lower()
    domain_l = (req.domain or "").lower().replace("https://", "").replace("http://", "").strip("/")

    findings: list[dict] = []
    mention_hits = 0
    citation_hits = 0
    total = 0

    for prompt in req.prompts:
        for probe in probe_all(prompt):
            if not probe.ok:
                findings.append(
                    {
                        "engine": probe.engine,
                        "prompt": prompt,
                        "mentioned": False,
                        "cited": False,
                        "ok": False,
                        "answer_excerpt": "",
                        "citations": [],
                        "error": probe.error,
                    }
                )
                continue  # don't count failed probes toward visibility
            total += 1
            answer_l = probe.answer.lower()
            mentioned = probe.ok and brand_l in answer_l
            cited = bool(domain_l) and (
                any(domain_l in c.lower() for c in probe.citations) or domain_l in answer_l
            )
            mention_hits += int(mentioned)
            citation_hits += int(cited)
            findings.append(
                {
                    "engine": probe.engine,
                    "prompt": prompt,
                    "mentioned": mentioned,
                    "cited": cited,
                    "ok": probe.ok,
                    "answer_excerpt": probe.answer[:400],
                    "citations": probe.citations[:5],
                    "error": probe.error,
                }
            )

    score = 0.0
    if total:
        score = round(100 * (0.7 * mention_hits + 0.3 * citation_hits) / total, 1)

    recommendations = _recommend(req, findings, score)

    return AgentResult(
        agent="aeo",
        summary=(
            f"'{req.brand}' appeared in {mention_hits}/{total} answer-engine responses "
            f"({citation_hits} with a citation to {domain_l or 'your domain'}). "
            f"Visibility score {score}/100."
        ),
        score=score,
        findings=findings,
        recommendations=recommendations,
        raw={"mention_hits": mention_hits, "citation_hits": citation_hits, "total": total},
    )


def _recommend(req: AEORequest, findings: list[dict], score: float) -> list[str]:
    context = json.dumps(
        [{k: f[k] for k in ("engine", "prompt", "mentioned", "cited", "answer_excerpt")} for f in findings],
        ensure_ascii=False,
    )
    prompt = (
        f"Brand: {req.brand}. Domain: {req.domain}.\n"
        f"Answer-engine visibility score: {score}/100.\n"
        f"Below are answer-engine responses to buyer questions and whether the brand was mentioned/cited:\n"
        f"{context}\n\n"
        "Give 5 specific, prioritized Answer Engine Optimization recommendations to increase how often "
        "this brand is mentioned and cited by AI answer engines. Base each on the actual gaps you see above. "
        'Return a JSON array of strings only.'
    )
    recs = analyze_json(prompt, fallback=lambda: _heuristic_recs(req, findings), max_tokens=800)
    if isinstance(recs, list):
        return [str(r) for r in recs][:5]
    return _heuristic_recs(req, findings)


def _heuristic_recs(req: AEORequest, findings: list[dict]) -> list[str]:
    """Keyless recommendations derived from where the brand is missing."""
    missing_engines = sorted({f["engine"] for f in findings if not f["mentioned"] and f["ok"]})
    uncited = [f for f in findings if f["mentioned"] and not f["cited"]]
    missing_prompts = sorted({f["prompt"] for f in findings if not f["mentioned"] and f["ok"]})
    recs: list[str] = []
    if missing_engines:
        recs.append(
            f"Not surfacing on {', '.join(missing_engines)}. Publish authoritative, directly-answering "
            f"content for these buyer questions: {'; '.join(missing_prompts[:3]) or 'your target prompts'}."
        )
    recs.append(
        "Add FAQ/Q&A schema (JSON-LD) and clear H2 questions matching buyer prompts so answer engines can extract you verbatim."
    )
    if req.domain and uncited:
        recs.append(
            f"You're mentioned but {req.domain} isn't cited — earn mentions on third-party review/listicle sites "
            "(G2, Capterra, industry roundups) that answer engines cite."
        )
    recs.append(
        "Get listed in comparison/'best X' articles that rank on the SERP — those pages are the sources answer engines pull from."
    )
    recs.append(
        "Keep a concise, fact-dense summary (stats, pricing, differentiators) on your key pages; answer engines favor extractable facts."
    )
    return recs[:5]
