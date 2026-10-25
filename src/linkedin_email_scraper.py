"""LinkedIn content-search email collector (spec: docs/SPEC-linkedin-email-collector.md).

Pipeline: content-search URL (``past-month`` facet, newest first) →
persistent stealth profile → scroll the infinite feed → in-page JS card
extract → regex every email out of the post body → :class:`EmailContact`
(Pydantic) → caller upserts into ``contact_emails`` → Excel.

Patterns borrowed (credited in docs/LINKEDIN_RESEARCH.md §11, MIT/Apache-2.0):

- URL grammar + facet validation — stickerdaniel/linkedin-mcp-server
  (LinkedIn SILENTLY IGNORES unknown date facets, hence the ValueError).
- Card selectors — joeyism/linkedin_scraper ``company_posts.py``.
- Email regex — speedyapply/JobSpy ``extract_emails_from_text``.

Safety rails mirror ``src/naukri_scraper.py``: transient-only tenacity
retries (never 403/429/security walls), bot-wall stop-with-guidance
(never CAPTCHA-solve), politeness pauses between domains and scrolls.
LinkedIn renders NO permalink anchor per post in content search (MCP
server's live finding) — ``post_url`` is best-effort, empty is acceptable.
"""
from __future__ import annotations

import logging
import re
import urllib.parse

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
from .naukri_scraper import BOT_WALL_PATTERNS, human_scroll
from .stealth_browser import human_pause

log = logging.getLogger(__name__)

#: Content (posts) search — NOT the jobs surface; keyword is ``"@<domain>"``.
CONTENT_SEARCH = "https://www.linkedin.com/search/results/content/"

#: The only date facets LinkedIn's content search honours (anything else
#: is silently ignored — so we validate before navigating).
DATE_FACETS = ("past-24h", "past-week", "past-month")

#: File extensions that produce "logo@2x.png"-style false-positive emails.
JUNK_TLDS = frozenset({
    "png", "jpg", "jpeg", "gif", "svg", "webp", "bmp", "ico",
    "css", "js", "html", "json", "md", "txt", "log",
})

#: Context characters captured around an email inside the snippet.
SNIPPET_RADIUS = 120

#: SDUI settle time after landing on search results (ms).
SETTLE_MS = 1500

#: In-page extractor: one dict {text, author, posted, url} per post card.
#: Marker ``/*content-email-cards*/`` lets tests dispatch on it (FakePage).
CONTENT_EXTRACT_JS = """
() => {
  /*content-email-cards*/
  const cards = [];
  const seen = new Set();
  document.querySelectorAll('div.feed-shared-update-v2').forEach((el) => {
    const urn = el.getAttribute('data-urn') || '';
    if (urn && seen.has(urn)) return;      // virtualised feed re-renders cards
    if (urn) seen.add(urn);
    const textEl = el.querySelector(
      '.feed-shared-update-v2__description, .update-components-text, .feed-shared-text');
    const text = textEl ? (textEl.innerText || '').trim() : '';
    if (!text) return;
    const authorEl = el.querySelector('[class*="actor__name"]');
    const postedEl = el.querySelector('[class*="actor__sub-description"]');
    const link = el.querySelector('a[href*="/feed/update/"], a[href*="/posts/"]');
    let url = '';
    if (link) {
      const href = link.getAttribute('href') || '';
      url = href.startsWith('http') ? href : ('https://www.linkedin.com' + href);
    }
    // Best-effort "Show more" expansion has already been attempted by the
    // caller; re-read the (possibly expanded) text node defensively.
    cards.push({
      text,
      post_id: urn || url || '',
      author: authorEl ? (authorEl.innerText || '').trim() : '',
      posted: postedEl ? (postedEl.innerText || '').trim() : '',
      url,
    });
  });
  return cards;
}
"""

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

    One contact per email; cards without emails yield nothing. The snippet
    keeps the evidence window, :class:`EmailContact` squeezes/caps it.
    """
    out: list[EmailContact] = []
    for card in cards:
        text = str(card.get("text") or "")
        emails = extract_emails(text)
        if not emails:
            continue
        # Relevance gate: drop posts LinkedIn surfaced that do not actually
        # carry the searched keyword nor an email on the target domain (the
        # "weird unrelated posts" the content search sometimes returns).
        if keyword and keyword.lower() not in text.lower() and \
                not any(e.rsplit("@", 1)[-1] == domain.lower() for e in emails):
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
                domain=domain,
                keyword=keyword,
                author=author,
                posted=posted,
                post_url=url,
                snippet=_snippet_around(text, email),
            ))
    return out


def _check_bot_wall(page: Page) -> bool:
    """True when the visible page is a block/CAPTCHA wall (never bypassed)."""
    try:
        visible = page.evaluate(
            "document.body ? document.body.innerText.slice(0,4000) : ''") or ""
    except Exception:
        return False
    return bool(BOT_WALL_PATTERNS.search(visible))


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


#: JS that clicks any "...see more / Show more" affordance so truncated post
#: bodies (and the emails hiding inside them) are expanded before extraction.
_EXPAND_SHOW_MORE_JS = """
() => {
  const needles = ['see more', 'show more', 'more'];
  document.querySelectorAll('button, a, span').forEach((el) => {
    const t = (el.innerText || el.textContent || '').trim().toLowerCase();
    if (!t) return;
    if (needles.some((n) => t === n || t.endsWith(n) || t.includes('see more'))
      && t.length <= 40) {
      try { el.click(); } catch (e) { /* ignore */ }
    }
  });
  return null;
}
"""


def _expand_show_more(page: Page) -> None:
    '''Best-effort expansion of truncated LinkedIn post bodies (never raises).'''
    try:
        page.evaluate(_EXPAND_SHOW_MORE_JS)
    except Exception:
        pass


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


def run_collect(context: BrowserContext,
                domains: list[str] | None = None,
                max_scrolls: int | None = None,
                date_facet: str | None = None) -> list[EmailContact]:
    """Search LinkedIn posts per domain and return deduped contacts.

    Flow per domain: ``"@<domain>"`` keyword URL → guarded goto → settle →
    bot-wall check (stop-with-guidance, never bypass) → up to
    ``max_scrolls`` extract/scroll passes (human-scroll + pause between) →
    politeness pause before the next domain. First sighting of an email
    wins within a run; cross-run dedupe is the DB's job (``upsert_emails``).

    Args:
        context: Open browser context (caller owns close()).
        domains: Target domains; defaults to ``SETTINGS.email_domains``.
        max_scrolls: Feed scrolls per domain; defaults to ``SETTINGS``.
        date_facet: LinkedIn date facet; defaults to ``SETTINGS``.

    Returns:
        Contacts in discovery order, one per unique email.
    """
    if domains is None:
        domains = SETTINGS.email_domains
    if max_scrolls is None:
        max_scrolls = SETTINGS.email_max_scrolls
    if date_facet is None:
        date_facet = SETTINGS.email_date_facet

    page = context.new_page()
    contacts: dict[tuple[str, str], EmailContact] = {}   # (email, post) → first sighting

    def _ensure_signed_in(url: str) -> bool:
        '''Navigate (with login-wall handling) and return True if usable.'''
        _safe_goto(page, url)
        page.wait_for_timeout(SETTLE_MS)      # SDUI hydration settle
        if _on_login_wall(page):
            # Signed out: hand the window to the human and WAIT. Do NOT
            # re-navigate here — a reload would interrupt sign-in and discard
            # whatever they have typed (the "page refreshes at login" bug).
            if not _prompt_manual_login():
                log.warning("Signed out and no TTY — stopping. Run headful "
                            "once, log in, and rerun (session persists).")
                return False
            if not _wait_for_login(page):
                log.warning("Still on the sign-in page %.0fs after the prompt "
                            "— NOT reloading it (that would interrupt your "
                            "login). Finish signing in in the open window, "
                            "then rerun; the session persists.", LOGIN_GRACE_S)
                return False
            # Signed in → one clean navigation to the target search page.
            _safe_goto(page, url)
            page.wait_for_timeout(SETTLE_MS)
            if _on_login_wall(page):       # bounced back to the wall anyway
                log.warning("Navigation landed back on the sign-in page — "
                            "stopping the run.")
                return False
        if _check_bot_wall(page):
            log.warning("Bot-wall on %r — stopping the run. Solve any check "
                        "MANUALLY in the opened window, then rerun.", domain)
            return False
        return True

    def _scroll_pass(keyword: str, domain: str, facet, scrolls: int) -> None:
        '''One extract/scroll pass over the feed for a single domain.'''
        for scroll in range(scrolls):
            _expand_show_more(page)
            cards = page.evaluate(CONTENT_EXTRACT_JS) or []
            for contact in _contacts_from_cards(cards, domain, keyword):
                contacts.setdefault((contact.email, contact.post_id), contact)
            if scroll < scrolls - 1:      # scroll between passes only
                human_scroll(page, rounds=1)
                human_pause()
                _expand_show_more(page)

    for domain in domains:
        keyword = "@" + domain
        target = SETTINGS.email_target_min
        before = len(contacts)
        log.info("Searching LinkedIn posts for %r", keyword)
        url = build_content_search_url(keyword, date_facet)
        if not _ensure_signed_in(url):
            break
        _scroll_pass(keyword, domain, date_facet, max_scrolls)
        added = len(contacts) - before
        # Fallback for sparse results: widen to all-time posts and scroll deeper
        # so we still surface ~20-30 emails even when the last 60 days are thin.
        if added < target:
            log.info("Only %d emails for %r in the primary window — falling "
                     "back to all-time posts (target %d).", added, domain, target)
            url2 = build_content_search_url(keyword, None)
            if _ensure_signed_in(url2):
                _scroll_pass(keyword, domain, None, SETTINGS.email_fallback_scrolls)
        human_pause()                          # politeness between domains
    log.info("Collect pass done: %d unique (email, post) contacts",
             len(contacts))
    return list(contacts.values())
