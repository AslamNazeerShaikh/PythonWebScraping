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

log = logging.getLogger(__name__)

BASE_SEARCH = "https://www.naukri.com/jobs"

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


def run_scrape(context: BrowserContext) -> list[Job]:
    """Run the full collection pass: all locations × pages → enriched Jobs.

    Stages: (1) per search+page: goto, extract, coerce to Job, relevance
    filter, dedupe by job_id (stops early at MAX_JOBS_TOTAL); (2) optional
    per-job detail enrichment with polite pauses. Pure collection — the
    caller (CLI/scheduler) handles persistence. Returns validated Jobs.
    """
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
            url = build_search_url(keywords, location, SETTINGS.experience,
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
                all_jobs[job.job_id] = job
                if len(all_jobs) >= SETTINGS.max_jobs_total:
                    break
            human_pause()  # politeness between pages

    jobs_list = list(all_jobs.values())
    log.info("Collected %d unique relevant jobs (enrich=%s)",
             len(jobs_list), SETTINGS.enrich_details)

    if SETTINGS.enrich_details:
        for i, job in enumerate(jobs_list, 1):
            log.info("Detail %d/%d: %s", i, len(jobs_list), job.title[:70])
            jobs_list[i - 1] = enrich_job(page, job)
            human_pause(1.5, 3.5)  # extra polite on detail pages

    try:
        page.close()
    except Exception:
        pass
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
