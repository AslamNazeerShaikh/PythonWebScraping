"""Layer 2 (extraction, offline twin): BeautifulSoup + lxml over saved HTML.

Pipeline position::

    Playwright (browser + JS) → HTML → THIS MODULE → dicts → Job (Pydantic)

The LIVE path uses the in-page JS extractor in :mod:`src.naukri_scraper`
(it sees computed styles, so its honeypot filtering is strongest). This BS4
layer is the offline twin: it re-parses ``output/debug_last_search.html`` or
any saved page, so you can develop/debug selectors WITHOUT re-hitting Naukri.
Same guard philosophy, best-effort from static markup: inline-style /
``aria-hidden`` / ``href``-trap checks plus job-id dedupe.

Entry points: :func:`parse_search_html` (listing pages), :func:`parse_detail_html`.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag

#: Canonical Naukri job URL shape — the trailing digits are the stable job id.
JOB_URL_RE = re.compile(r"/job-listings-[\w\-]+-(\d+)")

#: Inline styles that mark an element (or its card) as a honeypot trap.
HONEYPOT_STYLE_RE = re.compile(
    r"display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0(\.0+)?",
    re.I,
)

#: Origin used to absolutise relative job hrefs.
BASE = "https://www.naukri.com"


def _is_trap(a: Tag) -> bool:
    """Decide whether an anchor is a honeypot/placeholder trap (skip it).

    A link is a trap when ANY of these hold:
        - empty / ``"#"`` / ``javascript:`` href (navigates nowhere);
        - ``aria-hidden="true"`` on itself (assistive-tech invisible);
        - honeypot inline style on itself (``display:none`` …);
        - same style/``aria-hidden`` on any of 3 ancestor levels
          (hidden card container = every link inside is bait).
    """
    href = (a.get("href") or "").strip()
    if not href or href == "#" or href.lower().startswith("javascript:"):
        return True
    if a.get("aria-hidden") == "true":
        return True
    style = a.get("style") or ""
    if HONEYPOT_STYLE_RE.search(style):
        return True
    # Walk up: a hidden card container poisons every link inside it.
    # NOTE: BeautifulSoup (the document root) subclasses Tag, so the loop
    # must stop on it explicitly — there is nothing above it to inspect.
    parent = a.parent
    for _ in range(3):
        if parent is None or isinstance(parent, BeautifulSoup):
            break
        if HONEYPOT_STYLE_RE.search(parent.get("style") or ""):
            return True
        if parent.get("aria-hidden") == "true":
            return True
        parent = parent.parent
    return False


def _card_text(card: Tag | None, selectors: list[str]) -> str:
    """Return the first non-empty text found in ``card`` via ``selectors``.

    Args:
        card: Job-card container (``article``/``div``/``li``), or ``None``
            when the anchor sits outside any card (returns ``""``).
        selectors: CSS selectors tried in order, e.g. ``["span[class*='loc']"]``.
    """
    if card is None:
        return ""
    for sel in selectors:
        el = card.select_one(sel)
        if el and (t := el.get_text(" ", strip=True)):
            return t
    return ""


def parse_search_html(html: str) -> list[dict]:
    """Parse a saved Naukri SEARCH page into raw job dicts (pre-Pydantic).

    Args:
        html: Full page HTML (e.g. ``output/debug_last_search.html``).

    Returns:
        One dict per unique visible job (``job_id``/``title``/``company``/…).
        Trap links, title-less anchors and duplicate ids are dropped.
        Callers validate each dict via
        :func:`src.naukri_scraper.coerce_job` before use.
    """
    soup = BeautifulSoup(html, "lxml")
    out: list[dict] = []
    seen: set[str] = set()
    for a in soup.select('a[href*="/job-listings-"]'):
        m = JOB_URL_RE.search(a.get("href") or "")
        if not m or _is_trap(a):
            continue
        job_id = m.group(1)
        if job_id in seen:
            continue
        # Card context gives company/location/salary; anchor text is the title.
        card = a.find_parent(["article", "div", "li"])
        title = a.get_text(" ", strip=True) or _card_text(
            card, ["a.title", "h2 a", "a[class*='title']"])
        if not title or len(title) < 4:
            continue
        url = urljoin(BASE, (a.get("href") or "").split("?")[0])
        seen.add(job_id)
        out.append({
            "job_id": job_id,
            "title": title,
            "company": _card_text(card, ["a[class*='comp']", "div[class*='comp'] a"]),
            "location": _card_text(card, ["span[class*='loc']", "div[class*='loc'] span"]),
            "experience": _card_text(card, ["span[class*='exp']", "li[class*='experience']"]),
            "salary": _card_text(card, ["span[class*='sal']", "li[class*='salary']"]),
            "posted": _card_text(card, ["span[class*='date']", "span[class*='posted']", "div[class*='posted']"]),
            "snippet": _card_text(card, ["div[class*='desc']", "span[class*='desc']"])[:600],
            "url": url,
            "apply_url": url,  # default; detail parse may upgrade to external link
        })
    return out


def parse_detail_html(html: str, url: str) -> dict:
    """Parse a saved Naukri JOB page into a detail fragment.

    Args:
        html: Full job-page HTML.
        url: Canonical job URL (fallback ``apply_url`` when no external
            “apply on company site” link is found).

    Returns:
        ``{"description": …, "skills": […], "apply_url": …}`` — merged by the
        caller into the listing record (same keys as ``DETAIL_EXTRACT_JS``).
    """
    soup = BeautifulSoup(html, "lxml")
    desc = soup.select_one(
        'section[class*="job-desc"], div[class*="job-desc"], div.dtl-section')
    skills = [e.get_text(strip=True) for e in
              soup.select('a[class*="skill"], span[class*="skill"]')]
    # Apply link: first VISIBLE external “apply/company site” anchor wins;
    # trap-styled ones are skipped by _is_trap.
    apply_url = url.split("?")[0]
    for el in soup.select("a[href]"):
        label = f"{el.get_text(' ', strip=True)} {el.get('aria-label') or ''}".lower()
        if "apply" not in label and "company site" not in label:
            continue
        if _is_trap(el):
            continue
        href = el.get("href") or ""
        if href.startswith("http") and "naukri.com" not in href:
            apply_url = href
            break
    return {
        "description": desc.get_text("\n", strip=True)[:6000] if desc else "",
        "skills": [s for s in skills if s][:30],
        "apply_url": apply_url,
    }
