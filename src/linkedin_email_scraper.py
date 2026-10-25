"""LinkedIn content-search email collector (spec: docs/SPEC-linkedin-email-collector.md).

Flow per domain (ONE browser, ONE search, no per-domain URL navigation):

1. Type ``"@<domain>"`` into LinkedIn's global search box and press Enter.
2. Click the native **Posts** tab → content search (URL 2).
3. Apply **Latest** sort + **Past month** via the real radio controls and
   **Show results**.
4. Expand every post's "… more" button, then scroll the newest-first feed
   only until the domain's unique-email target is met (or the feed ends).
5. Move to the next CSV domain by clearing/retyping the SAME search box.

Why this shape: repeated direct URL hits (and per-domain browser relaunches)
triggered LinkedIn's "unusual search traffic" wall. In-page typing, clicking,
and mouse-wheel scrolling behave like a human session; the sorted content
feed is the single source of truth so URL 1 is never scraped.

Only emails whose own domain equals the searched domain survive extraction.
The extractor targets LinkedIn's current SDUI DOM (verified live 2026-10-25):
each post is a ``[role="listitem"]`` inside ``[data-testid="lazy-column"]``,
with exactly one ``[data-testid="expandable-text-box"]`` holding the body.
Older selectors (``div.feed-shared-update-v2``) no longer exist there.
"""
from __future__ import annotations

import json
import logging
import re
import urllib.parse
from collections.abc import Callable

from playwright.sync_api import BrowserContext, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import SETTINGS
from .models import EMAIL_RE, EmailContact
from .naukri_scraper import BOT_WALL_PATTERNS
from .stealth_browser import human_pause

log = logging.getLogger(__name__)

#: Content (posts) search — NOT the jobs surface; keyword is ``"@<domain>"``.
CONTENT_SEARCH = "https://www.linkedin.com/search/results/content/"
ALL_SEARCH = "https://www.linkedin.com/search/results/all/"
FEED_URL = "https://www.linkedin.com/feed/"

#: The only date facets LinkedIn's content search honours (anything else
#: is silently ignored — so we validate before using it).
DATE_FACETS = ("past-24h", "past-week", "past-month")

#: Facet token → label rendered in the "Date posted" dropdown.
DATE_LABELS = {
    "past-24h": "Past 24 hours",
    "past-week": "Past week",
    "past-month": "Past month",
}

#: File extensions that produce "logo@2x.png"-style false-positive emails.
JUNK_TLDS = frozenset({
    "png", "jpg", "jpeg", "gif", "svg", "webp", "bmp", "ico",
    "css", "js", "html", "json", "md", "txt", "log",
})

#: Context characters captured around an email inside the snippet.
SNIPPET_RADIUS = 120

#: SDUI settle time after landing on a page (ms).
SETTLE_MS = 1500

#: Global search input and the native Posts filter tab.
SEARCH_INPUT_SELECTOR = 'input[placeholder="Search"]'
POSTS_FILTER_SELECTOR = 'input[aria-label="Filter by Posts"]'
POSTS_FILTER_JS = r"""
() => {
  /*open-posts*/
  const inp = document.querySelector('input[aria-label="Filter by Posts"]');
  if (!inp) return false;
  const lab = inp.id ? document.querySelector('label[for="' + inp.id + '"]') : null;
  (lab || inp).click();
  return true;
}
"""

#: Typing cadence for the search box — human-typed, not a paste.
SEARCH_TYPE_DELAY_MS = 70
#: How long to wait for the new result page to visibly carry the keyword.
SEARCH_READY_TIMEOUT_MS = 15000
SEARCH_READY_POLL_MS = 500
#: Filter dropdown open/apply settle times.
FILTER_OPEN_MS = 900
FILTER_RADIO_MS = 300
FILTER_APPLY_MS = 4000
#: Feed scrolling: wheel burst, then wait for the lazy spinner / next batch.
WHEEL_STEPS = 3
WHEEL_DY = 1200
SCROLL_WAIT_MS = 2500
STALL_WAIT_MS = 5000
MAX_STALLS = 3
#: Extract + persist a checkpoint every N scroll rounds (partial-save safety).
CHECKPOINT_EVERY = 2
#: Settle time after clicking "more" so the expanded body is readable (ms).
EXPAND_WAIT_MS = 1200

#: In-page extractor: one dict per POST (not per DOM chunk/comment).
#: Marker ``/*content-email-cards*/`` lets tests dispatch on it (FakePage).
#: Raw string: ``\d`` / ``\n`` / ``\u2022`` must reach JS untouched.
CONTENT_EXTRACT_JS = r"""
() => {
  /*content-email-cards*/
  const cards = [];
  const seen = new Set();
  const lc = document.querySelector('[data-testid="lazy-column"]');
  if (!lc) return cards;
  const items = Array.from(lc.querySelectorAll('[role="listitem"]'))
    .filter((it) => it.querySelector('[data-testid="expandable-text-box"]'));
  for (const it of items) {
    const box = it.querySelector('[data-testid="expandable-text-box"]');
    const text = (box.innerText || '').trim();
    if (!text) continue;
    let author = '';
    for (const a of it.querySelectorAll('a[href*="/in/"]')) {
      const t = (a.innerText || '').trim();
      if (t && t.indexOf('\u2022') !== -1) {
        author = t.split('\u2022')[0].trim();
        break;
      }
    }
    if (!author) {
      const a = it.querySelector('a[href*="/in/"]');
      if (a) author = (a.innerText || '').trim().split('\n')[0].trim();
    }
    let posted = '';
    for (const el of it.querySelectorAll('p, span')) {
      const t = (el.innerText || '').trim();
      if (/^(\d+[smhdw]|\d+mo|\d+yr|just now|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{1,2})$/i.test(t)) {
        posted = t;
        break;
      }
    }
    let postId = it.getAttribute('componentkey') || '';
    const m = postId.match(/update-card-focus(.+?)FeedType_/);
    if (m) postId = m[1];
    if (!postId) postId = (author || '') + '|' + (posted || '') + '|' + text.slice(0, 80);
    if (seen.has(postId)) continue;
    seen.add(postId);
    let url = '';
    const link = it.querySelector('a[href*="/feed/update/"], a[href*="/posts/"]');
    if (link) url = link.href || '';
    cards.push({ text, post_id: postId, author, posted, url });
  }
  return cards;
}
"""

#: Count the real post units currently rendered (drives scroll progress).
COUNT_POSTS_JS = r"""
() => {
  /*count-posts*/
  const lc = document.querySelector('[data-testid="lazy-column"]');
  if (!lc) return 0;
  return Array.from(lc.querySelectorAll('[role="listitem"]'))
    .filter((it) => it.querySelector('[data-testid="expandable-text-box"]')).length;
}
"""

#: Feed column rectangle — used to park the mouse over the posts before
#: wheeling, so the wheel scrolls the results feed, not the page chrome.
FEED_RECT_JS = r"""
() => {
  /*feed-rect*/
  const lc = document.querySelector('[data-testid="lazy-column"]');
  if (!lc) return null;
  const r = lc.getBoundingClientRect();
  return { x: r.x, y: r.y, width: r.width, height: r.height };
}
"""

#: Scroll the true scroll container (verified live: ``<main>``) to its end,
#: which triggers LinkedIn's lazy-load sentinel.
SCROLL_TO_BOTTOM_JS = r"""
() => {
  /*scroll-bottom*/
  const lc = document.querySelector('[data-testid="lazy-column"]');
  if (!lc) return false;
  let el = lc;
  while (el && el !== document.documentElement) {
    const cs = getComputedStyle(el);
    if (/(auto|scroll)/.test(cs.overflowY) && el.scrollHeight > el.clientHeight + 20) break;
    el = el.parentElement;
  }
  if (!el || el === document.documentElement) {
    el = document.scrollingElement || document.documentElement;
  }
  el.scrollTop = el.scrollHeight;
  el.dispatchEvent(new Event('scroll', { bubbles: true }));
  return true;
}
"""

#: Filter bar / posts rendered? The search SPA updates its URL before the
#: new SDUI body exists, so URL alone is not enough to start scraping.
RESULTS_READY_JS = r"""
() => {
  /*results-ready*/
  if (document.querySelector('input[aria-label="Filter by Posts"]')) return true;
  if (document.querySelector('[data-testid="lazy-column"] [role="listitem"]')) return true;
  const t = document.body ? (document.body.innerText || '').toLowerCase() : '';
  return t.includes('no results') || t.includes('no matching');
}
"""

SHOW_RESULTS_JS = r"""
() => {
  /*show-results*/
  const els = Array.from(document.querySelectorAll('a, button, [role="button"]'));
  const el = els.find((e) => {
    const t = (e.innerText || '').trim();
    const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && t === 'Show results';
  });
  if (!el) return false;
  el.click();
  return true;
}
"""

#: LinkedIn's "search paused" wall ("unusual search traffic… activity paused").
SEARCH_PAUSED_RE = re.compile(
    r"unusual search traffic|search activity[^.]{0,120}paused", re.I | re.S)

_TRANSIENT = (TimeoutError, PlaywrightTimeoutError)
#: Transient navigation failures only — a 403/CAPTCHA wall is NOT retried.
_safe_goto = retry(
    retry=retry_if_exception_type(_TRANSIENT),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=15),
    reraise=True,
)(lambda page, url: page.goto(url, wait_until="domcontentloaded"))


def build_content_search_url(keyword: str,
                             date_facet: str | None = "past-month",
                             sort: str = "date_posted") -> str:
    """Return a LinkedIn content-search URL for ``keyword``.

    Kept for the ``export``/diagnostic tooling and offline fixtures; the live
    collector now reaches this page by CLICKING the native Posts tab instead
    of navigating to a hard-coded URL.

    Args:
        keyword: Search string, e.g. ``"@cognizant.com"``.
        date_facet: One of :data:`DATE_FACETS` — anything else would be
            silently ignored by LinkedIn, hence validated here.
        sort: ``"date_posted"`` (newest first, default) or ``"relevance"``.

    Returns:
        Fully-encoded ``https://www.linkedin.com/search/results/content/…`` URL.

    Raises:
        ValueError: If ``date_facet`` is not a supported token.
    """
    if date_facet:
        if date_facet not in DATE_FACETS:
            raise ValueError(
                f"unsupported date facet {date_facet!r}; one of {DATE_FACETS}")
    params = {
        "keywords": keyword,
        "origin": "FACETED_SEARCH",
        "sortBy": f'"{sort}"',
    }
    if date_facet:
        params["datePosted"] = f'["{date_facet}"]'
    query = urllib.parse.urlencode(params)
    return f"{CONTENT_SEARCH}?{query}"


def build_all_search_url(keyword: str) -> str:
    """Return LinkedIn's global (all-results) search URL for ``keyword``.

    No date/location/type filters — matches the user's requested query shape:
    ``/search/results/all/?keywords=<kw>&origin=TYPEAHEAD_HISTORY&position=0``.
    """
    query = urllib.parse.urlencode({
        "keywords": keyword,
        "origin": "TYPEAHEAD_HISTORY",
        "position": "0",
    })
    return f"{ALL_SEARCH}?{query}"


def extract_emails(text: str) -> list[str]:
    """Return unique, lowercased emails found in ``text`` (order kept).

    Filters filename false positives (``logo@2x.png`` → TLD ``png``).
    """
    found: list[str] = []
    for raw in EMAIL_RE.findall(text or ""):
        email = raw.lower()
        if email.rsplit(".", 1)[-1] in JUNK_TLDS:
            continue
        if email not in found:
            found.append(email)
    return found


def _snippet_around(text: str, email: str) -> str:
    """Return up to ±:data:`SNIPPET_RADIUS` chars of context around ``email``."""
    idx = text.lower().find(email)
    start = max(0, idx - SNIPPET_RADIUS)
    end = idx + len(email) + SNIPPET_RADIUS
    return text[start:end]


def _contacts_from_cards(cards: list[dict], domain: str,
                         keyword: str) -> list[EmailContact]:
    """Turn raw card dicts (untrusted) into validated contacts.

    Only emails on the **searched domain** are kept. A post may contain
    ``@cognizant.com`` alongside Gmail addresses; the outsiders must never
    reach the workbook. Multiple matching addresses in one post become
    separate contacts (one row each downstream).

    Args:
        cards: Raw ``{text, post_id, author, posted, url}`` cards.
        domain: Target company domain, e.g. ``"cognizant.com"``.
        keyword: Search keyword, e.g. ``"@cognizant.com"`` (evidence only).
    """
    out: list[EmailContact] = []
    target = domain.strip().lower().lstrip("@")
    for card in cards:
        text = str(card.get("text") or "")
        emails = [e for e in extract_emails(text)
                  if e.rsplit("@", 1)[-1] == target]
        if not emails:
            continue
        # "Show more" expansion may have appended text; re-extract defensively.
        post_id = str(card.get("post_id") or card.get("urn") or "")
        if not post_id:
            post_id = str(card.get("url") or "")
        if not post_id:
            author = str(card.get("author") or "")
            posted = str(card.get("posted") or "")
            post_id = f"{author}|{posted}|{text[:40]}"
        author = str(card.get("author") or "")
        posted = str(card.get("posted") or "")
        url = str(card.get("url") or "")
        for email in emails:
            out.append(EmailContact(
                email=email,
                post_id=post_id,
                domain=target,
                keyword=keyword,
                author=author,
                posted=posted,
                post_url=url,
                snippet=_snippet_around(text, email),
            ))
    return out


def _body_text(page: Page) -> str:
    """Visible body text (first 4 000 chars) — wall/readiness sensing only."""
    try:
        return str(page.evaluate(
            "document.body ? document.body.innerText.slice(0,4000) : ''") or "")
    except Exception:
        return ""


def _check_bot_wall(page: Page) -> bool:
    """True when the visible page is a block/CAPTCHA/search-paused wall."""
    visible = _body_text(page)
    if not visible:
        return False
    return bool(BOT_WALL_PATTERNS.search(visible)
                or SEARCH_PAUSED_RE.search(visible))


#: LinkedIn auth-wall redirect targets (probe-verified 2026-10-23: an
#: unauthenticated search lands on ``/uas/login?session_redirect=…``).
LOGIN_WALL_RE = re.compile(r"/uas/login|authwall|checkpoint", re.I)

#: Passive poll cadence (s) while waiting for the human to finish signing in.
LOGIN_POLL_S = 2.0

#: Max passive wait (s) for sign-in before giving up with guidance. Generous
#: on purpose: it covers typing credentials + 2FA/OTP. It is a passive URL
#: poll — it never navigates or reloads the page, so it cannot interrupt the
#: human the way a re-``goto`` did (that reload was the "page refreshes at
#: login" bug).
LOGIN_GRACE_S = 300.0


#: JS that clicks every post's "… more" button so the full body (and any
#: emails past the truncation point) is readable. Each button is clicked at
#: most once per DOM node — LinkedIn toggles to "see less", and re-clicking
#: would collapse the text we just revealed.
_EXPAND_SHOW_MORE_JS = r"""
() => {
  /*expand-more*/
  let clicked = 0;
  const buttons = document.querySelectorAll(
    '[data-testid="expandable-text-button"], [role="listitem"] button');
  buttons.forEach((el) => {
    if (el.getAttribute('data-scraper-expanded') === '1') return;
    const t = (el.innerText || el.textContent || '').trim().toLowerCase();
    if (!t || t.includes('less')) return;
    const byTestId = el.getAttribute('data-testid') === 'expandable-text-button';
    const byLabel = t === 'more' || t.endsWith(' more') ||
                    t.includes('see more') || t.includes('show more');
    if (!byTestId && !byLabel) return;
    try {
      el.click();
      el.setAttribute('data-scraper-expanded', '1');
      clicked += 1;
    } catch (e) { /* ignore */ }
  });
  return clicked;
}
"""


def _expand_show_more(page: Page) -> int:
    """Click every visible post "more" button; return how many were clicked.

    Best-effort and never raises. A short settle follows the clicks so the
    extractor reads the fully expanded body, not the truncated preview.
    """
    try:
        clicked = int(page.evaluate(_EXPAND_SHOW_MORE_JS) or 0)
    except Exception:
        return 0
    if clicked:
        page.wait_for_timeout(EXPAND_WAIT_MS)
    return clicked


def _on_login_wall(page: Page) -> bool:
    """True when the page landed on LinkedIn's sign-in redirect.

    Content search is auth-walled; without a session the extractor would
    silently find zero cards — exactly the first live run's failure mode.
    """
    return bool(LOGIN_WALL_RE.search(page.url or ""))


def _prompt_manual_login() -> bool:
    """Ask the human to sign in once (session persists in the profile).

    Returns:
        False when non-interactive (no TTY / background run) — caller stops.

    Never solves any challenge — signing in is the human's action only.
    """
    log.warning("LinkedIn session is signed out — log in MANUALLY in the "
                "opened window, then press ENTER (session persists).")
    try:
        input("  Press ENTER after logging in (or Ctrl+C to abort)... ")
    except EOFError:
        return False
    human_pause(2, 4)
    return True


def _wait_for_login(page: Page,
                    grace_s: float | None = None,
                    poll_s: float | None = None) -> bool:
    """Passively wait until the human has finished signing in.

    Polls ``page.url`` until the sign-in wall clears. It NEVER navigates or
    reloads — the human may need a while to type credentials and clear 2FA,
    and a re-``goto`` would reload the login page and discard what they typed
    (the reported "page refreshes at login" bug).

    Args:
        page: The page showing the sign-in wall.
        grace_s: Max wait in seconds; defaults to :data:`LOGIN_GRACE_S`.
        poll_s: Poll cadence in seconds; defaults to :data:`LOGIN_POLL_S`.

    Returns:
        True once the URL is off the login wall (signed in); False if still
        on the wall after ``grace_s`` — the caller then stops with guidance
        rather than reloading the page.
    """
    if grace_s is None:
        grace_s = LOGIN_GRACE_S
    if poll_s is None:
        poll_s = LOGIN_POLL_S
    waited = 0.0
    while _on_login_wall(page):
        if waited >= grace_s:
            return False
        # Passive wait — Playwright sleeps the Node worker; the browser window
        # stays live for the human. It does NOT reload or re-navigate.
        page.wait_for_timeout(int(poll_s * 1000))
        waited += poll_s
    return True


def _open_feed(page: Page) -> bool:
    """Open the feed once and clear any sign-in wall.

    This is the ONLY navigation of a run. Every later domain reuses this
    page and is driven through the global search box.
    """
    try:
        _safe_goto(page, FEED_URL)
    except Exception:
        log.warning("Could not open the LinkedIn feed; continuing on the "
                    "current page.")
    page.wait_for_timeout(SETTLE_MS)
    if _on_login_wall(page):
        if not _prompt_manual_login():
            log.warning("Signed out and no TTY — stopping. Run headful once, "
                        "log in, and rerun (session persists).")
            return False
        if not _wait_for_login(page):
            log.warning("Still on the sign-in page %.0fs after the prompt — "
                        "NOT reloading it (that would interrupt your login). "
                        "Finish signing in in the open window, then rerun; "
                        "the session persists.", LOGIN_GRACE_S)
            return False
        try:
            _safe_goto(page, FEED_URL)
        except Exception:
            log.warning("Could not reopen the feed after login; continuing.")
        page.wait_for_timeout(SETTLE_MS)
        if _on_login_wall(page):
            log.warning("Navigation landed back on the sign-in page — "
                        "stopping the run.")
            return False
    return True


def _results_ui_ready(page: Page) -> bool:
    """True once the search result surface has actually rendered."""
    try:
        return bool(page.evaluate(RESULTS_READY_JS))
    except Exception:
        return False


def _wait_for_results(page: Page, keyword: str) -> bool:
    """Wait until the rendered results visibly reflect ``keyword``.

    Prevents scraping the previous domain's feed while the SPA swaps pages.
    The URL changes before the new SDUI body exists, so this requires ALL of:
    a search-results URL, the keyword visible in the body (or an explicit
    "no results" message), and a rendered filter bar / post list.
    Times out (and continues) rather than failing a run on a slow render.
    """
    needle = keyword.lower()
    waited = 0
    while waited <= SEARCH_READY_TIMEOUT_MS:
        try:
            url = (page.url or "").lower()
        except Exception:
            url = ""
        low = _body_text(page).lower()
        if "/search/results/" in url and _results_ui_ready(page) and (
                needle in low or "no results" in low or "no matching" in low):
            return True
        page.wait_for_timeout(SEARCH_READY_POLL_MS)
        waited += SEARCH_READY_POLL_MS
    log.warning("Search results for %r were not confirmed after %.0fs — "
                "continuing anyway", keyword, SEARCH_READY_TIMEOUT_MS / 1000)
    return False


def _submit_search(page: Page, keyword: str) -> bool:
    """Type ``keyword`` into the SAME global search box and press Enter."""
    try:
        box = page.locator(SEARCH_INPUT_SELECTOR).first
        box.click()
        box.fill("")
        box.type(keyword, delay=SEARCH_TYPE_DELAY_MS)
        box.press("Enter")
    except Exception as exc:
        log.warning("Could not drive the LinkedIn search box for %r: %s",
                    keyword, exc)
        return False
    page.wait_for_timeout(1500)
    _wait_for_results(page, keyword)
    return True


def _open_posts_view(page: Page) -> bool:
    """Click the native Posts tab (URL 1 → URL 2) without a URL goto.

    The filter bar can finish rendering a few seconds after the search
    results URL changes, so this retries briefly instead of skipping a
    domain's entire content view on the first miss.
    """
    clicked = False
    for _ in range(20):
        try:
            clicked = bool(page.evaluate(POSTS_FILTER_JS))
        except Exception:
            clicked = False
        if clicked:
            break
        page.wait_for_timeout(500)
    if not clicked:
        log.warning("Posts filter tab not found on the all-results page")
        return False
    try:
        page.wait_for_selector("text=Sort by", timeout=10000)
    except Exception:
        page.wait_for_timeout(5000)
    page.wait_for_timeout(SETTLE_MS)
    return True


def _click_filter_button(page: Page, label: str) -> bool:
    """Open a native search filter dropdown (e.g. ``"Sort by"``)."""
    js = f"""
    () => {{
      /*click-filter*/
      const wanted = {json.dumps(label)};
      const els = Array.from(document.querySelectorAll('[role="button"], button'));
      const el = els.find((e) => {{
        const t = (e.innerText || '').trim();
        const r = e.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && (t === wanted || t.startsWith(wanted));
      }});
      if (!el) return false;
      el.click();
      return true;
    }}
    """
    try:
        return bool(page.evaluate(js))
    except Exception:
        return False


def _select_filter_radio(page: Page, label: str) -> bool:
    """Select a native filter radio by its aria-label (click its label)."""
    js = f"""
    () => {{
      /*select-radio*/
      const wanted = {json.dumps(label)};
      const inputs = Array.from(document.querySelectorAll('input[type="radio"]'));
      const input = inputs.find(
        (i) => (i.getAttribute('aria-label') || '') === wanted);
      if (!input) return false;
      const lab = input.id
        ? document.querySelector('label[for="' + input.id + '"]') : null;
      (lab || input).click();
      return true;
    }}
    """
    try:
        return bool(page.evaluate(js))
    except Exception:
        return False


def _show_filter_results(page: Page) -> bool:
    """Apply the open filter panel via its native "Show results" control."""
    try:
        return bool(page.evaluate(SHOW_RESULTS_JS))
    except Exception:
        return False


def _apply_content_filters(page: Page, date_facet: str | None) -> bool:
    """Apply **Latest** + the requested date facet through LinkedIn's UI.

    The dropdowns are custom SDUI panels whose radios do nothing until the
    "Show results" link is clicked — navigating to a crafted URL instead is
    exactly the behaviour that tripped the traffic wall, so this stays 100%
    in-page clicks.
    """
    ok = True
    if _click_filter_button(page, "Sort by"):
        page.wait_for_timeout(FILTER_OPEN_MS)
        if _select_filter_radio(page, "Latest"):
            page.wait_for_timeout(FILTER_RADIO_MS)
            if not _show_filter_results(page):
                ok = False
        else:
            ok = False
        page.wait_for_timeout(FILTER_APPLY_MS)
    else:
        log.debug("Sort-by control not found; keeping LinkedIn's default order")
        ok = False

    label = DATE_LABELS.get(date_facet or "")
    if label:
        if _click_filter_button(page, "Date posted"):
            page.wait_for_timeout(FILTER_OPEN_MS)
            if _select_filter_radio(page, label):
                page.wait_for_timeout(FILTER_RADIO_MS)
                if not _show_filter_results(page):
                    ok = False
            else:
                ok = False
            page.wait_for_timeout(FILTER_APPLY_MS)
        else:
            log.debug("Date-posted control not found; keeping all dates")
            ok = False
    return ok


def _count_posts(page: Page) -> int:
    """Number of real post units currently rendered in the lazy column."""
    try:
        return int(page.evaluate(COUNT_POSTS_JS) or 0)
    except Exception:
        return 0


def _wheel_feed(page: Page) -> None:
    """Mouse-wheel over the posts column (human scroll gesture)."""
    try:
        rect = page.evaluate(FEED_RECT_JS)
    except Exception:
        rect = None
    if isinstance(rect, dict) and rect.get("width"):
        try:
            x = float(rect.get("x", 0)) + float(rect.get("width", 0)) / 2
            y = float(rect.get("y", 0)) + 200
            page.mouse.move(int(x), int(max(160.0, min(y, 620.0))))
            for _ in range(WHEEL_STEPS):
                page.mouse.wheel(0, WHEEL_DY)
            return
        except Exception:
            pass
    try:
        page.mouse.wheel(0, WHEEL_DY * WHEEL_STEPS)
    except Exception:
        pass


def _scroll_to_bottom(page: Page) -> bool:
    """Jump the true scroll container to its end (lazy-load sentinel)."""
    try:
        return bool(page.evaluate(SCROLL_TO_BOTTOM_JS))
    except Exception:
        return False


def _extract_fresh(page: Page, domain: str, keyword: str,
                   seen: set[tuple[str, str]],
                   emails_seen: set[str],
                   on_batch: Callable[[list[EmailContact]], None] | None
                   ) -> list[EmailContact]:
    """Expand every post, extract, and return contacts not seen in this run."""
    _expand_show_more(page)
    try:
        cards = page.evaluate(CONTENT_EXTRACT_JS) or []
    except Exception:
        cards = []
    batch: list[EmailContact] = []
    for contact in _contacts_from_cards(cards, domain, keyword):
        emails_seen.add(contact.email)
        key = (contact.email, contact.post_id)
        if key in seen:
            continue
        seen.add(key)
        batch.append(contact)
    if batch and on_batch is not None:
        on_batch(batch)
    return batch


def _collect_view(page: Page, keyword: str, domain: str, rounds: int,
                  target_emails: int, seen: set[tuple[str, str]],
                  emails_seen: set[str],
                  on_batch: Callable[[list[EmailContact]], None] | None
                  ) -> list[EmailContact]:
    """Scroll the Latest/Past-month feed until the unique-email target is met.

    The feed is already newest-first, so stopping as soon as ``target_emails``
    distinct matching addresses have been seen yields the latest posts, not
    the whole archive. ``rounds`` is a safety cap; three no-growth rounds end
    the feed early when a domain simply doesn't have that many addresses.
    """
    target_emails = max(1, int(target_emails))
    found: list[EmailContact] = []
    stalled = 0
    hit_target = False

    for round_no in range(max(0, rounds)):
        # Read the initial batch before spending a scroll — most small
        # targets (5-10 emails) are satisfied by the first few posts.
        if round_no == 0:
            found.extend(_extract_fresh(page, domain, keyword, seen,
                                        emails_seen, on_batch))
            if len(emails_seen) >= target_emails:
                hit_target = True
                break

        before = _count_posts(page)
        if before == 0:
            break
        _wheel_feed(page)
        page.wait_for_timeout(SCROLL_WAIT_MS)
        after = _count_posts(page)
        if after <= before:
            _scroll_to_bottom(page)
            page.wait_for_timeout(STALL_WAIT_MS)
            after = max(after, _count_posts(page))
            stalled = stalled + 1 if after <= before else 0
        else:
            stalled = 0

        if round_no % CHECKPOINT_EVERY == 0 or stalled:
            found.extend(_extract_fresh(page, domain, keyword, seen,
                                        emails_seen, on_batch))
            if len(emails_seen) >= target_emails:
                hit_target = True
                break
        if stalled >= MAX_STALLS:
            log.info("%s: no more posts after %d posts", domain, after)
            break

    if not hit_target:
        found.extend(_extract_fresh(page, domain, keyword, seen,
                                    emails_seen, on_batch))
    if len(emails_seen) >= target_emails:
        log.info("%s: reached target (%d/%d unique emails)", domain,
                 len(emails_seen), target_emails)
    else:
        log.warning("%s: only %d/%d unique emails after scrolling",
                    domain, len(emails_seen), target_emails)
    return found


def run_collect(context: BrowserContext,
                domains: list[str] | None = None,
                max_scrolls: int | None = None,
                date_facet: str | None = None,
                on_batch: Callable[[list[EmailContact]], None] | None = None,
                targets: dict[str, int] | None = None
                ) -> list[EmailContact]:
    """Search the Latest/Past-month content feed until each target is met.

    One page, one search per domain. The flow is deliberately URL-2-only:
    type ``"@domain"`` in the search box → click the native **Posts** tab →
    apply **Latest** + the date facet → scroll the content feed until the
    domain has ``targets[domain]`` distinct matching email addresses.

    Args:
        context: Open browser context (caller owns close()).
        domains: Target domains; used when ``targets`` is omitted. Defaults
            to ``SETTINGS.email_domains``.
        max_scrolls: Max scroll rounds per domain (safety cap); defaults to
            ``SETTINGS.email_max_scrolls``.
        date_facet: LinkedIn date facet; defaults to ``SETTINGS``.
        on_batch: Optional persistence hook called with each new batch of
            contacts, so a broken session still leaves partial Excel.
        targets: Ordered ``{domain: unique_email_target}`` map. When given,
            ``domains`` is ignored and the CSV order is preserved.

    Returns:
        Contacts in discovery order, one per unique (email, post).
    """
    if targets is None:
        if domains is None:
            domains = SETTINGS.email_domains
        targets = {d: SETTINGS.email_default_target for d in domains}
    else:
        domains = list(targets)
    if max_scrolls is None:
        max_scrolls = SETTINGS.email_max_scrolls
    if date_facet is None:
        date_facet = SETTINGS.email_date_facet
    if date_facet and date_facet not in DATE_FACETS:
        raise ValueError(
            f"unsupported date facet {date_facet!r}; one of {DATE_FACETS}")

    page = context.new_page()
    contacts: dict[tuple[str, str], EmailContact] = {}
    seen: set[tuple[str, str]] = set()

    if not _open_feed(page):
        return []

    for domain in domains:
        target = max(1, int(targets.get(domain,
                                         SETTINGS.email_default_target)))
        keyword = "@" + domain
        log.info("Searching LinkedIn posts for %r (target %d unique emails)",
                 keyword, target)
        if not _submit_search(page, keyword):
            break
        if _check_bot_wall(page):
            log.warning("LinkedIn paused search activity / served a block "
                        "wall — stopping. Wait 30-60 minutes before searching "
                        "again. SQLite and output/linkedin_emails_partial.xlsx "
                        "already hold every email harvested so far; rerun the "
                        "remaining domains with --input-csv.")
            break

        if not _open_posts_view(page):
            log.warning("%s: Posts tab unavailable — skipping this domain",
                        domain)
        elif not _apply_content_filters(page, date_facet):
            log.warning("%s: could not apply Latest + %s — skipping this "
                        "domain so unsorted results never reach the sheet",
                        domain, date_facet or "date filter")
        else:
            if _check_bot_wall(page):
                log.warning("LinkedIn paused search activity after the "
                            "filters — stopping. Partial Excel is preserved.")
                break
            log.info("%s: content search (newest, %s)", domain,
                     date_facet or "all time")
            emails_seen: set[str] = set()
            for contact in _collect_view(page, keyword, domain, max_scrolls,
                                         target, seen, emails_seen, on_batch):
                contacts.setdefault((contact.email, contact.post_id), contact)

        page.wait_for_timeout(SETTINGS.email_domain_pause_s * 1000)
        human_pause()                          # politeness between domains

    log.info("Collect pass done: %d unique (email, post) contacts",
             len(contacts))
    return list(contacts.values())
