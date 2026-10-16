"""Naukri.com scraper with honeypot / anti-bot hardening.

Personal-use design:
- Only public search pages, polite delays, capped pages/jobs.
- Human-like: random pauses, scrolling, mouse moves, persistent profile.
- Honeypot-safe extraction: ignores hidden/trap links, dedupes by job id.
- Never auto-solves CAPTCHAs — pauses for manual solve.
- Retries (tenacity) cover TRANSIENT network/timeouts only (max 3, backoff).
  They never hammer through 403/429/CAPTCHA — a bot-wall pauses instead.

Pipeline: Playwright -> in-page JS extract -> normalize -> Job (Pydantic).
"""
from __future__ import annotations

import csv
import json
import logging
import random
import re
import urllib.parse
from collections import Counter
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from playwright.sync_api import BrowserContext, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import SETTINGS
from .models import Job
from .stealth_browser import human_pause

# Progress/cancel hook types (web orchestrator passes bound methods here).
StopHook = Callable[[], bool]
ProgressHook = Callable[[dict], None]

log = logging.getLogger(__name__)

BASE_SEARCH = "https://www.naukri.com/jobs"

#: Naukri homepage + search-bar selector CANDIDATES (ordered: proven class
#: selectors first, semantic placeholder/aria fallbacks for markup variants
#: served to automated visits — verified live: the bar exists but classes
#: may differ while placeholders/aria-labels stay stable).
NAUKRI_HOME = "https://www.naukri.com/"
SEARCH_CANDIDATES = {
    "keywords": [".nI-gNb-sb__keywords input.suggestor-input",
                 'input[aria-label*="keyword, designation"]',
                 'input[placeholder*="designation"]'],
    "location": [".nI-gNb-sb__locations input.suggestor-input",
                 'input[placeholder="Enter location"]',
                 'input[aria-label="Enter location"]'],
    "location_option": [".nI-gNb-sb__locations li.tuple-wrap",
                        "li.tuple-wrap"],
    "experience": ["#experienceDD",
                   'input[aria-label="Select experience"]',
                   'input[placeholder="Select experience"]'],
    "experience_option": ["li"],
}

def _first_match(page: Page, candidates: list[str]) -> str | None:
    """Return the first selector matching ≥1 node, else None (fast probe).

    Evaluate errors propagate — the caller treats them as a failed submit
    and falls back to URL navigation, so no swallowing here.
    """
    for sel in candidates:
        count = page.evaluate(
            f"document.querySelectorAll('{sel}').length") or 0
        if count:
            return sel
    return None

BOT_WALL_PATTERNS = re.compile(
    r"verify you are (a )?human|captcha|access denied|pardon the interruption|"
    r"unusual traffic|are you a robot|cloudflare|perimeterx|datadome",
    re.I,
)

# Anchors on Naukri job pages always look like /job-listings-<slug>-<digits>
JOB_URL_RE = re.compile(r"/job-listings-[\w\-]+-(\d+)")

def build_search_url(keywords: str, location: str, experience: int,
                     date_filter: int, page: int = 1) -> str:
    """Build a Naukri ``/jobs`` search URL (stable query-param form).

    Args:
        keywords: e.g. ``"asp.net core c# .net"`` (URL-encoded as ``k``).
        location: e.g. ``"pune"`` (``l``). Experience: years (``experience``).
        date_filter: posted within last N days (``jobPostDate``).
        page: 1-based result page (``page``).
    """
    q = {
        "k": keywords,
        "l": location,
        "experience": str(experience),
        "jobPostDate": str(date_filter),
        "page": str(page),
    }
    return f"{BASE_SEARCH}?{urllib.parse.urlencode(q)}"

LISTING_EXTRACT_JS = """
() => {
  const isVisible = (el) => {
    if (!el) return false;
    if (el.getAttribute('aria-hidden') === 'true') return false;
    const style = window.getComputedStyle(el);
    if (!style) return false;
    if (style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse') return false;
    if (parseFloat(style.opacity || '1') < 0.15) return false;
    const r = el.getBoundingClientRect();
    if (r.width <= 1 || r.height <= 1) return false;
    // off-screen far away = likely honeypot
    if (r.x < -2000 || r.y < -2000) return false;
    return true;
  };
  const visibleText = (el) => (el && isVisible(el) ? (el.innerText || '').trim() : '');

  const out = [];
  const anchors = Array.from(document.querySelectorAll('a[href*="/job-listings-"]'));
  for (const a of anchors) {
    try {
      const href = a.getAttribute('href') || '';
      if (!href || href === '#' || href.startsWith('javascript:')) continue;
      // HONEYPOT GUARD: link itself AND its card must be visible
      if (!isVisible(a)) continue;
      const m = href.match(/\\/job-listings-[\\w\\-]+-(\\d+)/);
      if (!m) continue;
      const jobId = m[1];
      // NOTE: window.location explicitly — a same-scope const ALSO named
      // location would shadow it into the temporal dead zone (this exact bug
      // once zeroed every result: ReferenceError per card, swallowed below).
      const absUrl = new URL(href, window.location.origin).toString().split('?')[0];

      // Walk up to card container (article / div with jobTuple-ish class)
      let card = a.closest('article, div[class*="jobTuple"], div[class*="srp-job"], div[class*="cust-job"], li[class*="job"]');
      if (!card) card = a.parentElement?.parentElement || a.parentElement;

      // Title: prefer the anchor text itself if long enough, else card h2/a.title
      let title = visibleText(a);
      const t2 = card ? visibleText(card.querySelector('a.title, h2 a, a[class*="title"]')) : '';
      if (t2 && t2.length > title.length) title = t2;

      const pick = (sels) => {
        if (!card) return '';
        for (const s of sels) {
          const el = card.querySelector(s);
          const t = visibleText(el);
          if (t) return t;
        }
        return '';
      };
      const company = pick(['a[class*="comp"], a[class*="Comp"], div[class*="comp"] a, span[class*="comp"]']);
      const loc = pick(['span[class*="loc"], div[class*="loc"] span, li[class*="location"]']);
      const exp = pick(['span[class*="exp"], li[class*="experience"], span[class*="experience"]']);
      const salary = pick(['span[class*="sal"], li[class*="salary"], span[class*="salary"]']);
      const posted = pick(['span[class*="date"], span[class*="posted"], div[class*="posted"], li[class*="date"]']);
      const snippet = pick(['div[class*="desc"], span[class*="desc"], div[class*="snippet"]']).slice(0, 600);

      // Skip obvious trap cards (0x0 or hidden container)
      if (card && !isVisible(card)) continue;
      if (!title || title.length < 4) continue;

      out.push({ jobId, title, company, location: loc, experience: exp, salary, posted, snippet, url: absUrl });
    } catch (e) { /* skip one bad card */ }
  }
  // Dedupe by jobId, keep first
  const seen = new Set(); const deduped = [];
  for (const j of out) { if (!seen.has(j.jobId)) { seen.add(j.jobId); deduped.push(j); } }
  return deduped;
}
"""

DETAIL_EXTRACT_JS = """
() => {
  const txt = (sel) => {
    const el = document.querySelector(sel);
    return el ? (el.innerText || '').trim().slice(0, 400) : '';
  };
  const all = (sel) => Array.from(document.querySelectorAll(sel))
    .map(e => (e.innerText || '').trim()).filter(Boolean).slice(0, 5);
  const descEl = document.querySelector('section[class*="job-desc"], div[class*="job-desc"], div.dtl-section, section.dtl-section');
  const description = descEl ? (descEl.innerText || '').trim().slice(0, 6000) : document.body.innerText.slice(0, 6000);
  // Apply link: prefer visible external apply / company-site button, else canonical URL
  let applyUrl = location.href.split('?')[0];
  const candidates = Array.from(document.querySelectorAll('a[href], button'));
  for (const el of candidates) {
    const t = ((el.innerText || '') + ' ' + (el.getAttribute('aria-label') || '')).toLowerCase();
    if (!/apply|company site|career site|apply on/.test(t)) continue;
    const r = el.getBoundingClientRect();
    const st = window.getComputedStyle(el);
    if (st.display === 'none' || st.visibility === 'hidden' || r.width <= 1) continue; // honeypot guard
    const href = el.getAttribute('href');
    if (href && href.startsWith('http') && !href.includes('naukri.com')) { applyUrl = href; break; }
  }
  return {
    pageTitle: txt('h1'),
    company: txt('a[class*="comp"], div[class*="comp"]'),
    location: all('span[class*="loc"]')[0] || '',
    experience: txt('span[class*="exp"]'),
    salary: txt('span[class*="sal"]'),
    posted: txt('span[class*="date"], div[class*="posted"]'),
    skills: Array.from(document.querySelectorAll('a[class*="skill"], span[class*="skill"], div[class*="key-skill"] a'))
      .map(e => (e.innerText || '').trim()).filter(Boolean).slice(0, 30),
    description,
    applyUrl,
  };
}
"""

def check_bot_wall(page: Page) -> bool:
    """True only on *visible* block pages (not raw HTML, avoids false positives)."""
    try:
        visible = (page.evaluate("document.body ? document.body.innerText.slice(0,4000) : ''") or "")
        title = (page.title() or "")
        blob = f"{title}\n{visible}"
        if not BOT_WALL_PATTERNS.search(blob):
            return False
        # Confirm it's really a wall: no job anchors AND block text visible
        anchors = page.evaluate(
            "document.querySelectorAll('a[href*=\"/job-listings-\"]').length") or 0
        return anchors == 0
    except Exception:
        return False

def handle_possible_block(page: Page) -> None:
    """Pause for MANUAL bot-wall solving when one is detected (never bypass).

    No-op on normal pages. On a visible CAPTCHA / “verify human” / Access
    Denied wall: prints guidance, waits for ENTER (headful solve), then a
    short pause. ``EOFError`` (non-interactive runs) just continues.
    """
    if check_bot_wall(page):
        log.warning("Possible bot-check / CAPTCHA detected — solve MANUALLY in the "
                    "opened browser window, then press ENTER.")
        try:
            input("  Press ENTER after solving (or to continue anyway)... ")
        except EOFError:
            pass
        human_pause(2, 4)

def human_scroll(page: Page, rounds: int = 3) -> None:
    """Mimic human reading: mouse-wheel scrolls + small pauses + mouse wiggle.

    Triggers lazy-loaded job cards on listing pages (content below the fold
    only renders after scrolling). Falls back to JS scrolling if the mouse
    API is unavailable.
    """
    for _ in range(rounds):
        try:
            page.mouse.wheel(0, random.randint(400, 900))
        except Exception:
            page.evaluate("window.scrollBy(0, 600)")
        time_small = random.uniform(0.6, 1.4)
        page.wait_for_timeout(int(time_small * 1000))
    # occasional mouse wiggle
    try:
        page.mouse.move(random.randint(100, 900), random.randint(100, 600))
    except Exception:
        pass

def is_relevant(title: str, desc: str = "") -> bool:
    """Light relevance filter for .NET fullstack roles; keeps recall high."""
    t = f"{title} {desc}".lower()
    must = ("net", ".net", "dotnet", "asp.net", "c#", "c #", "fullstack", "full stack")
    if not any(k in t for k in must):
        return False
    return True

#: Java-stack signal for the pure-Java exclusion gate (see
#: :func:`should_exclude_java_job`). Word-boundary guarded so ``JavaScript``
#: (and the spaced variant ``Java Script``) never counts as Java — port of
#: the title keyword/blocklist idea from ankitbaghel01's auto-apply runner,
#: adapted from Node to a single stdlib regex here.
JAVA_STACK_RE = re.compile(
    r"(?<![a-zA-Z#.\w])"
    r"(?:java(?!\s*script)|spring(?:\s*boot)?|hibernate|selenium|gradle|maven"
    r"|kotlin|groovy|scala|jsp|servlet|struts|j2ee|j2se|junit|testng"
    r"|micronaut|quarkus)"
    r"(?![a-zA-Z])",
    re.I,
)

#: .NET anchor that rescues a Java-signal job (mixed stacks stay: the user
#: wants AI/.NET-relevant postings, only *pure*-Java ones go). ``React`` /
#: ``Angular`` / ``Microservices`` are deliberately NOT anchors — they appear
#: in pure-Java postings too, so they cannot prove .NET relevance.
DOTNET_ANCHOR_RE = re.compile(
    r"(?<![a-zA-Z#.\w])c\s*#"
    r"|\.net\b"
    r"|(?<![a-zA-Z])dotnet(?![a-zA-Z])"
    r"|asp\.?net"
    r"|(?<![a-zA-Z])blazor(?![a-zA-Z])"
    r"|entity\s*framework"
    r"|vb\.?net",
    re.I,
)


def should_exclude_java_job(title: str = "", skills: list[str] | tuple[str, ...] = (),
                            snippet: str = "", description: str = "") -> bool:
    """True when a posting is pure-Java and must stay out of the Excel.

    Exclude iff a Java-stack signal (``JAVA_STACK_RE``) appears anywhere in
    the title, key skills, snippet, or description AND no .NET anchor
    (``DOTNET_ANCHOR_RE``) is present in the same text. Truth table:

    * pure AI / AI+C# / pure .NET / Java+C# / pure Python / AI+Python → keep
    * pure Java / AI+Java (no .NET) / Selenium-only → exclude

    Pure function — unit-tested against every row of that table.
    """
    parts = [title or ""]
    parts.extend(s for s in (skills or []) if s)
    parts.append(snippet or "")
    parts.append(description or "")
    blob = "\n".join(parts)
    if not JAVA_STACK_RE.search(blob):
        return False
    return DOTNET_ANCHOR_RE.search(blob) is None


def job_should_exclude(job: Job) -> bool:
    """Thin :class:`Job` wrapper over :func:`should_exclude_java_job`."""
    return should_exclude_java_job(job.title, job.skills, job.snippet,
                                   job.description)

def normalize_raw(raw: dict, search_location: str = "") -> dict:
    """Map extractor output (in-page JS camelCase) to Job snake_case fields.

    Also canonicalises URLs (drops ``?…`` tracking params), caps free text,
    and defaults ``apply_url`` to the job URL (enrichment may upgrade it to
    an external company-site link). Pure function — trivially unit-testable.
    """
    """Map in-page JS camelCase keys -> Job snake_case fields."""
    url = (raw.get("url") or "").split("?")[0]
    return {
        "job_id": str(raw.get("jobId") or raw.get("job_id") or ""),
        "title": raw.get("title") or "",
        "company": raw.get("company") or "",
        "location": raw.get("location") or "",
        "search_location": search_location,
        "experience": raw.get("experience") or "",
        "salary": raw.get("salary") or "",
        "posted": raw.get("posted") or "",
        "snippet": (raw.get("snippet") or "")[:600],
        "url": url,
        "apply_url": (raw.get("applyUrl") or raw.get("apply_url") or url).split("?")[0],
        "description": (raw.get("description") or "")[:6000],
        "skills": raw.get("skills") or [],
    }

def coerce_job(raw: dict, search_location: str = "") -> Job | None:
    """Validate one raw dict -> Job. Returns None (with warning) on bad data."""
    try:
        return Job(**normalize_raw(raw, search_location))
    except ValidationError as e:
        log.warning("Dropping invalid job %r: %s",
                    str(raw.get("jobId") or raw.get("url"))[:80], e.errors()[0])
        return None

# --- Tenacity: transient navigation failures only ---------------------------
# Playwright raises its OWN TimeoutError (not the builtin) on slow loads.
# Both are safe to retry with backoff. HTTP 403/429/CAPTCHA walls are NOT
# retried here — the bot-wall handler pauses for manual solve instead.
_TRANSIENT = (TimeoutError, PlaywrightTimeoutError)
_safe_goto = retry(
    retry=retry_if_exception_type(_TRANSIENT),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=15),
    reraise=True,
)(lambda page, url: page.goto(url, wait_until="domcontentloaded"))

def scrape_search_page(page: Page, url: str) -> list[dict]:
    """Load ONE search page and return raw (pre-Pydantic) job-card dicts.

    Flow: tenacity-guarded goto → settle → bot-wall check → human scroll →
    wait for job anchors → in-page JS extract. On zero cards the page HTML is
    saved to ``output/debug_last_search.html`` for offline ``parse`` runs.
    """
    _safe_goto(page, url)
    return extract_listing_cards(page)

def extract_listing_cards(page: Page) -> list[dict]:
    """Extract job cards from the CURRENT page (no navigation).

    Used after search-bar submission lands on results. Same settle →
    bot-wall → scroll → extract flow as :func:`scrape_search_page`, whose
    goto step is skipped here.
    """
    page.wait_for_timeout(2500)
    handle_possible_block(page)
    human_scroll(page)
    try:
        page.wait_for_selector('a[href*="/job-listings-"]', timeout=12000)
    except Exception:
        log.warning("No job cards found (selector timeout) — saving debug HTML.")
    jobs = page.evaluate(LISTING_EXTRACT_JS) or []
    if not jobs:
        try:
            out = SETTINGS.output_dir
            out.mkdir(parents=True, exist_ok=True)
            dbg = out / "debug_last_search.html"
            dbg.write_text(page.content() or "", encoding="utf-8")
            log.info("Saved debug page HTML -> %s (re-parse offline with "
                     "`parse` command)", dbg)
        except Exception:
            pass
    return jobs

def slugify_keywords(text: str) -> str:
    """Slugify a keyword string the way Naukri's own search box does.

    Derived from a live manual search (``c-sharp-asp-dot-net-core-...``):
    lowercase, ``#`` → ``sharp``, ``.`` → ``dot``, commas dropped,
    whitespace → dashes. Unit-tested against that exact manual slug.
    """
    s = (text or "").lower()
    s = s.replace("#", " sharp ").replace(".", " dot ").replace(",", "")
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    return re.sub(r"-+", "-", s).strip("-")

def build_slug_search_url(keywords: str, location: str, experience: int,
                          days: int, page: int = 1) -> str:
    """Skills-scan search URL mirroring a manual Naukri search exactly.

    ``/<slug>-jobs-in-<loc>[-<n>]?k=&l=&experience=&jobAge=``: the
    lordzohar-bot ``/{keyword}-jobs`` pattern plus the user-verified
    ``jobAge`` freshness param. Pagination is PATH-based (``...-pune-2``):
    verified live that ``?page=2`` on a slug URL reloads page 1 (same
    first job id, deduped to nothing new), while the ``-2`` suffix
    returns 20 fresh postings. The collector's legacy ``/jobs?k=&l=``
    builder is untouched.
    """
    base = f"{slugify_keywords(keywords)}-jobs-in-{location.lower()}"
    if page > 1:
        base = f"{base}-{page}"
    q = {"k": keywords, "l": location, "experience": str(experience),
         "jobAge": str(days)}
    return f"https://www.naukri.com/{base}?{urllib.parse.urlencode(q)}"


def _pick_option(page: Page, candidates: list[str], text: str) -> bool:
    """Click the dropdown option matching ``text``; False when none matches.

    Exact (case-insensitive) hit first, then substring — e.g. ``6 years``
    picks its own row, never ``16 years``. Text matching (ankitbaghel01's
    discipline) survives the class renames automated visits get.
    """
    sel = _first_match(page, candidates)
    if sel is None:
        return False
    texts = page.evaluate(
        f"/*OPTION_TEXTS*/Array.from(document.querySelectorAll('{sel}')).map(e=>((e.innerText||e.textContent)||'').trim())") or []
    want = (text or "").strip().casefold()
    for i, current in enumerate(texts):
        if want and current.casefold() == want:
            page.evaluate(f"document.querySelectorAll('{sel}')[{i}].click()")
            return True
    for i, current in enumerate(texts):
        if want and want in current.casefold():
            page.evaluate(f"document.querySelectorAll('{sel}')[{i}].click()")
            return True
    return False

def submit_searchbar(page: Page, keywords: str, location: str,
                     experience: int) -> str:
    """Drive Naukri's search bar like a human; return the landed results URL.

    Fills the keyword/location suggestors (variant-tolerant resolution),
    picks the location suggestion and the ``<N> years`` experience option by
    visible text, then submits with Enter (proven live — the search button
    node is absent in the served variant). Raises on failure so the caller
    falls back to slug-URL navigation (which never breaks the run).
    """
    log.info("Skills search via search bar: %r in %s (%sy)", keywords,
             location, experience)
    _safe_goto(page, NAUKRI_HOME)
    page.wait_for_timeout(2000)
    handle_possible_block(page)
    kw_sel = _first_match(page, SEARCH_CANDIDATES["keywords"])
    loc_sel = _first_match(page, SEARCH_CANDIDATES["location"])
    exp_sel = _first_match(page, SEARCH_CANDIDATES["experience"])
    if not all([kw_sel, loc_sel, exp_sel]):
        raise RuntimeError("search bar variant without known inputs")
    assert kw_sel and loc_sel and exp_sel  # narrowed for typing
    page.fill(kw_sel, keywords)
    page.wait_for_timeout(800)
    page.fill(loc_sel, location)
    page.wait_for_timeout(1500)  # let suggestions render
    if not _pick_option(page, SEARCH_CANDIDATES["location_option"], location):
        log.info("Location suggestion skipped — typed text kept")
    try:
        page.click(exp_sel)
        if not _pick_option(page, SEARCH_CANDIDATES["experience_option"],
                            f"{experience} years"):
            log.info("Experience option missing — typed search continues")
    except Exception:
        log.info("Experience dropdown skipped — search continues without it")
    page.click(kw_sel)
    page.keyboard.press("Enter")
    page.wait_for_selector('a[href*="/job-listings-"]', timeout=15000)
    log.info("Search bar landed: %s", page.url)
    return page.url
    """Return ``url`` with its ``page`` query param set (for post-bar paging)."""
    parts = urllib.parse.urlsplit(url)
    q = dict(urllib.parse.parse_qsl(parts.query))
    q["page"] = str(pnum)
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(q)))

def enrich_job(page: Page, job: Job) -> Job:
    """Visit ONE job page and merge detail fields (description/skills/apply).

    Returns a NEW validated Job (input untouched). Any failure (timeout,
    validation, unexpected) logs a warning and returns the original job, so
    one bad detail page never kills the whole run.
    """
    try:
        _safe_goto(page, job.url)
        page.wait_for_timeout(2200)
        handle_possible_block(page)
        human_scroll(page, rounds=2)
        detail = page.evaluate(DETAIL_EXTRACT_JS) or {}
        merged = job.model_dump()
        mapping = {"applyUrl": "apply_url", "pageTitle": None}
        for k, v in detail.items():
            if not v:
                continue
            target = mapping.get(k, k)
            if target is None:
                continue
            if target in merged:
                merged[target] = v
        if not merged.get("apply_url"):
            merged["apply_url"] = job.url
        return Job(**merged)
    except (ValidationError, TimeoutError, PlaywrightTimeoutError) as e:
        log.warning("Detail fetch failed for %s: %s", job.url, e)
        return job
    except Exception as e:
        log.warning("Detail fetch failed for %s: %s", job.url, e)
        return job

def run_scrape(context: BrowserContext,
               should_stop: Callable[[], bool] | None = None,
               on_progress: Callable[[dict], None] | None = None) -> list[Job]:
    """Run the full collection pass: all locations × pages → enriched Jobs.

    Stages: (1) per search+page: goto, extract, coerce to Job, relevance
    filter, dedupe by job_id (stops early at MAX_JOBS_TOTAL); (2) optional
    per-job detail enrichment with polite pauses. Pure collection — the
    caller (CLI/scheduler) handles persistence. Returns validated Jobs.

    Args:
        context: Playwright browser context (the hands).
        should_stop: Optional poll hook — when it returns True the pass ends
            early and whatever was collected so far is returned (the web
            orchestrator wires this to its cancel event; CLI passes None).
        on_progress: Optional sink for ``{"stage": ...}`` dicts (``"search"``
            per page, ``"done"`` at the end) for live UI progress bars.
    """
    stopped = should_stop or (lambda: False)

    def _report(stage: str, **extra: object) -> None:
        if on_progress is not None:
            on_progress({"stage": stage, **extra})

    page = context.new_page()
    all_jobs: dict[str, Job] = {}

    searches = [(kw, loc) for loc in SETTINGS.locations
                for kw in [SETTINGS.keywords]]
    log.info("Plan: %d searches x %d pages | exp=%dy | last %dd",
             len(searches), SETTINGS.max_pages_per_search,
             SETTINGS.experience, SETTINGS.date_filter)

    for keywords, location in searches:
        for pnum in range(1, SETTINGS.max_pages_per_search + 1):
            if len(all_jobs) >= SETTINGS.max_jobs_total:
                break
            if stopped():
                log.info("Scrape cancel requested — stopping after %d jobs", len(all_jobs))
                break
            url = build_slug_search_url(keywords, location, SETTINGS.experience,
                                          SETTINGS.date_filter, pnum)
            log.info("Search %s p%d: %s", location, pnum, url)
            try:
                raw_jobs = scrape_search_page(page, url)
            except Exception as e:
                log.error("Search page failed: %s", e)
                human_pause()
                continue
            log.info("Found %d cards (pre-filter)", len(raw_jobs))
            for raw in raw_jobs:
                job = coerce_job(raw, search_location=location)
                if job is None or job.job_id in all_jobs:
                    continue
                if not is_relevant(job.title, job.snippet):
                    continue
                if job_should_exclude(job):
                    log.info("Skipping pure-Java posting: %s", job.title[:70])
                    continue
                all_jobs[job.job_id] = job
                if len(all_jobs) >= SETTINGS.max_jobs_total:
                    break
            _report("search", location=location, page=pnum,
                    pages=SETTINGS.max_pages_per_search, found=len(all_jobs))
            human_pause()  # politeness between pages

    jobs_list = list(all_jobs.values())
    log.info("Collected %d unique relevant jobs (enrich=%s)",
             len(jobs_list), SETTINGS.enrich_details)

    if SETTINGS.enrich_details:
        for i, job in enumerate(jobs_list, 1):
            if stopped():
                log.info("Scrape cancel requested — skipping remaining details")
                break
            log.info("Detail %d/%d: %s", i, len(jobs_list), job.title[:70])
            jobs_list[i - 1] = enrich_job(page, job)
            _report("detail", index=i, total=len(jobs_list))
            human_pause(1.5, 3.5)  # extra polite on detail pages
        # Detail pages reveal skills/descriptions: re-check the Java gate so
        # postings that only show their Java stack in the full text still drop.
        kept = [j for j in jobs_list if not job_should_exclude(j)]
        if len(kept) != len(jobs_list):
            log.info("Excluded %d pure-Java postings after enrichment",
                     len(jobs_list) - len(kept))
        jobs_list = kept

    try:
        page.close()
    except Exception:
        pass
    _report("done", found=len(jobs_list))
    return jobs_list

def save_results(jobs: list[Job], output_dir: Path | None = None) -> tuple[Path, Path]:
    """Timestamped JSON + CSV file export (SQLite remains the source of truth)."""
    out = output_dir or SETTINGS.output_dir
    out.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = out / f"naukri_jobs_{ts}.json"
    csv_path = out / f"naukri_jobs_{ts}.csv"

    payload = [j.model_dump() for j in jobs]
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                         encoding="utf-8")

    fields = ["job_id", "title", "company", "location", "search_location",
              "experience", "salary", "posted", "url", "apply_url", "snippet"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for j in payload:
            w.writerow(j)
    log.info("Saved %d jobs -> %s, %s", len(jobs), json_path, csv_path)
    return json_path, csv_path

# ---------------------------------------------------------------------------
# Key-skills scan (analysis-only: aggregates "Key Skills" across postings)
# ---------------------------------------------------------------------------
def build_skills_report(jobs: list[Job], by_company: bool = True) -> dict:
    """Aggregate key-skill frequencies across enriched jobs.

    ``by_company=True`` (default): each skill counts DISTINCT companies
    (``C#`` in 20 Capgemini + 10 TCS postings scores 2, over
    ``companies_total``). ``False`` keeps the legacy one-vote-per-posting
    count. Per-company posting breakdowns ship in both modes.


    Each posting votes once per skill (case-insensitive, dupes collapsed);
    display casing follows the most common raw form. Every skill also carries
    its company breakdown (which companies asked for it, how many postings
    each) so company-heavy skills are visible instead of silently repeated.
    Returns a JSON-safe report with the top 30 skills by posting count.
    Pure function.
    """
    if not jobs:
        return {"jobs_scanned": 0, "with_skills": 0, "without_skills": 0,
                "unique_skills": 0, "companies_total": 0,
                "count_mode": "companies" if by_company else "postings",
                "top": []}
    forms: dict[str, Counter] = {}
    company_votes: dict[str, Counter] = {}
    for job in jobs:
        seen: set[str] = set()
        for raw in job.skills:
            name = (raw or "").strip()
            key = name.casefold()
            if not key or key in seen:
                continue
            seen.add(key)
            counts = forms.get(key)
            if counts is None:
                counts = forms[key] = Counter()
            counts[name] += 1
            company = (job.company or "").strip() or "Unknown"
            cc = company_votes.get(key)
            if cc is None:
                cc = company_votes[key] = Counter()
            cc[company] += 1
    posting_counts = {k: sum(c.values()) for k, c in forms.items()}
    if by_company:
        scores = {k: len(company_votes[k]) for k in forms}  # distinct companies
    else:
        scores = posting_counts  # legacy: one vote per posting
    ranked = Counter(scores).most_common(30)
    total = len(jobs)
    companies_total = len({(j.company or "").strip() or "Unknown" for j in jobs})
    denom = companies_total if by_company else total
    top = []
    for key, count in ranked:
        cos = sorted(company_votes[key].items(), key=lambda kv: (-kv[1], kv[0]))
        top.append({"skill": forms[key].most_common(1)[0][0], "count": count,
                    "pct": round(100 * count / denom, 1),
                    "companies": [{"name": n, "count": c} for n, c in cos]})
    with_skills = sum(1 for j in jobs if j.skills)
    return {"jobs_scanned": total, "with_skills": with_skills,
            "without_skills": total - with_skills,
            "unique_skills": len(forms), "companies_total": companies_total,
            "count_mode": "companies" if by_company else "postings",
            "top": top}


def run_skills_scan(context: BrowserContext, keywords: str, location: str,
                    experience: int, days: int, pages: int,
                    max_jobs: int, by_company: bool = True,
                    should_stop: StopHook | None = None,
                    on_progress: ProgressHook | None = None) -> dict:
    """Scan detail pages for key skills: one search → enriched → report.

    The full comma-separated keyword string goes into a SINGLE search
    (``?k=<all titles>``), exactly like Naukri's own search box — Naukri
    matches across the titles itself. Same polite machinery as
    :func:`run_scrape` (pauses, bot-wall handling, honeypot-safe
    extraction) but WITHOUT the relevance filter. Analysis-only: nothing
    is written to the DB; the report (plus a .txt written by the caller)
    is the artifact.
    """
    stopped = should_stop or (lambda: False)

    def _report(stage: str, **extra: object) -> None:
        if on_progress is not None:
            on_progress({"stage": stage, **extra})

    page = context.new_page()
    found: dict[str, Job] = {}
    for pnum in range(1, pages + 1):
        if len(found) >= max_jobs or stopped():
            break
        try:
            if pnum == 1:
                # Human path first: drive the search bar (keywords + location
                # + experience, like manual typing). Any failure falls back to
                # the proven direct-URL navigation — the run never breaks here.
                try:
                    submit_searchbar(page, keywords, location, experience)
                    raw_jobs = extract_listing_cards(page)
                except Exception as e:
                    log.warning("Search-bar submit failed (%s) — slug fallback", e)
                    raw_jobs = scrape_search_page(
                        page, build_slug_search_url(keywords, location,
                                                    experience, days, pnum))
            else:
                # Path-based paging (slug-2, slug-3, ...): ?page= is ignored
                # on slug URLs (reloads page 1 — deduped to nothing new).
                raw_jobs = scrape_search_page(
                    page, build_slug_search_url(keywords, location,
                                                experience, days, pnum))
        except Exception as e:
            log.error("Search page failed: %s", e)
            human_pause()
            continue
        for raw in raw_jobs:
            job = coerce_job(raw, search_location=location)
            if job is None or job.job_id in found:
                continue
            found[job.job_id] = job
            if len(found) >= max_jobs:
                break
        _report("search", location=location, page=pnum, found=len(found))
        human_pause()  # politeness between pages

    jobs_list = list(found.values())
    log.info("Skills scan collected %d postings — enriching key skills", len(jobs_list))
    for i, job in enumerate(jobs_list, 1):
        if stopped():
            log.info("Skills scan cancel requested — skipping remaining details")
            break
        jobs_list[i - 1] = enrich_job(page, job)
        _report("detail", index=i, total=len(jobs_list))
        human_pause(1.5, 3.5)  # extra polite on detail pages

    try:
        page.close()
    except Exception:
        pass
    report = build_skills_report(jobs_list, by_company=by_company)
    _report("done", found=len(jobs_list))
    return report
