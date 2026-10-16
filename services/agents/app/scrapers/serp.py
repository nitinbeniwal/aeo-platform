"""Lightweight SERP scraper (DuckDuckGo HTML endpoint).

No API key required. Returns organic results (title, url, snippet). DuckDuckGo's
HTML endpoint is used because it is scrape-friendly and doesn't hard-block bots
the way google.com/search does. Swap in a paid SERP API here if you need Google
parity at scale.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup

from ..config import get_settings

_ENDPOINT = "https://html.duckduckgo.com/html/"
# DDG's HTML endpoint returns an empty page for non-browser UAs, so SERP probing
# uses a browser UA (distinct from the polite bot UA used for direct site scraping).
_SERP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


@dataclass
class SerpResult:
    rank: int
    title: str
    url: str
    snippet: str


def search(query: str, *, limit: int = 10) -> list[SerpResult]:
    s = get_settings()
    try:
        with httpx.Client(timeout=s.scraper_timeout, headers={"User-Agent": _SERP_UA}) as c:
            r = c.post(_ENDPOINT, data={"q": query})
            r.raise_for_status()
            html = r.text
    except Exception:  # noqa: BLE001
        return []

    soup = BeautifulSoup(html, "html.parser")
    results: list[SerpResult] = []
    for i, el in enumerate(soup.select(".result__body"), start=1):
        if i > limit:
            break
        a = el.select_one("a.result__a")
        if not a:
            continue
        snippet_el = el.select_one(".result__snippet")
        results.append(
            SerpResult(
                rank=i,
                title=a.get_text(strip=True),
                url=_clean_ddg_url(a.get("href", "")),
                snippet=snippet_el.get_text(strip=True) if snippet_el else "",
            )
        )
    return results


def _clean_ddg_url(href: str) -> str:
    """DDG wraps targets in a redirect: /l/?uddg=<encoded>. Unwrap it."""
    if "uddg=" in href:
        qs = parse_qs(urlparse(href).query)
        if "uddg" in qs:
            return qs["uddg"][0]
    return href
