"""Pure-Python analysis used when no LLM provider is available.

Not as nuanced as an LLM, but fully keyless and deterministic: term-frequency
content-gap detection, price extraction, intent classification, and templated
recommendations driven by the actual scraped data.
"""
from __future__ import annotations

import re
from collections import Counter

_STOP = set(
    """a an the and or but if then else for of to in on at by with from as is are was were be been
    being this that these those it its you your we our they their he she his her i me my mine ours
    yours theirs who whom which what when where why how all any both each few more most other some
    such no nor not only own same so than too very can will just should now about into over after
    before above below up down out off again further once here there com www http https new get use
    using used also may one two three best top vs via per etc eg ie""".split()
)

_WORD = re.compile(r"[a-zA-Z][a-zA-Z0-9'-]{2,}")
_PRICE = re.compile(r"(?:\$|usd|€|£)\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:/|per)\s?(?:mo|month|yr|year|user|seat))?", re.I)


def tokens(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text) if w.lower() not in _STOP]


def top_terms(text: str, n: int = 20) -> list[tuple[str, int]]:
    return Counter(tokens(text)).most_common(n)


def content_gaps(target_terms: set[str], corpus: str, n: int = 15) -> list[str]:
    """Terms common across ranking pages that the target hasn't emphasized."""
    ranked = [t for t, _ in top_terms(corpus, 60)]
    return [t for t in ranked if t not in target_terms][:n]


def extract_prices(text: str, limit: int = 10) -> list[str]:
    seen: list[str] = []
    for m in _PRICE.findall(text):
        v = m.strip()
        if v not in seen:
            seen.append(v)
        if len(seen) >= limit:
            break
    return seen


def classify_intent(keyword: str) -> str:
    k = keyword.lower()
    if any(w in k for w in ("buy", "price", "pricing", "cost", "cheap", "deal", "coupon")):
        return "transactional — users are comparing to purchase"
    if any(w in k for w in ("best", "top", "vs", "review", "compare", "alternative")):
        return "commercial investigation — users are evaluating options"
    if any(w in k for w in ("how", "what", "why", "guide", "tutorial", "learn")):
        return "informational — users want to understand the topic"
    return "informational/navigational — broad intent"


def detect_features(text: str, candidates: list[str]) -> list[str]:
    t = text.lower()
    return [c for c in candidates if c.lower() in t]
