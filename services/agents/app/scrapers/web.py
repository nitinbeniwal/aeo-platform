"""Web content scraper.

Two tiers:
  fetch_static()   httpx + trafilatura  -> fast, for static/SSR pages
  fetch_rendered() Playwright chromium   -> for JS-heavy SPAs

`extract(url)` tries static first and transparently falls back to rendered
when the static pull yields too little text.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import httpx
import trafilatura
from bs4 import BeautifulSoup

from ..config import get_settings

_MIN_TEXT = 400  # chars below which we consider the static pull a failure


@dataclass
class Page:
    url: str
    title: str = ""
    text: str = ""
    links: list[str] = field(default_factory=list)
    rendered: bool = False
    ok: bool = True
    error: str | None = None


def _headers() -> dict[str, str]:
    return {"User-Agent": get_settings().scraper_user_agent}


def fetch_static(url: str) -> Page:
    s = get_settings()
    try:
        with httpx.Client(timeout=s.scraper_timeout, follow_redirects=True, headers=_headers()) as c:
            r = c.get(url)
            r.raise_for_status()
            html = r.text
    except Exception as e:  # noqa: BLE001
        return Page(url=url, ok=False, error=str(e))

    text = trafilatura.extract(html, include_links=False, favor_recall=True) or ""
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string or "").strip() if soup.title else ""
    links = _absolute_links(url, soup)
    return Page(url=url, title=title, text=text, links=links)


def fetch_rendered(url: str) -> Page:
    s = get_settings()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return Page(url=url, ok=False, error="playwright not installed")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=s.scraper_user_agent)
            page.goto(url, timeout=s.scraper_timeout * 1000, wait_until="networkidle")
            html = page.content()
            title = page.title()
            browser.close()
    except Exception as e:  # noqa: BLE001
        return Page(url=url, ok=False, error=str(e))

    text = trafilatura.extract(html, include_links=False, favor_recall=True) or ""
    soup = BeautifulSoup(html, "html.parser")
    links = _absolute_links(url, soup)
    return Page(url=url, title=title, text=text, links=links, rendered=True)


def extract(url: str) -> Page:
    page = fetch_static(url)
    if page.ok and len(page.text) >= _MIN_TEXT:
        return page
    rendered = fetch_rendered(url)
    return rendered if rendered.ok else page


def _absolute_links(base: str, soup: BeautifulSoup) -> list[str]:
    from urllib.parse import urljoin, urlparse

    out: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base, a["href"])
        if urlparse(href).scheme in ("http", "https") and href not in seen:
            seen.add(href)
            out.append(href)
    return out[:200]
