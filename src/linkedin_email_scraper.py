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
    cards.push({
      text,
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
                             date_facet: str = "past-month",
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
    if date_facet not in DATE_FACETS:
        raise ValueError(
            f"unsupported date facet {date_facet!r}; one of {DATE_FACETS}")
    query = urllib.parse.urlencode({
        "keywords": keyword,
        "origin": "FACETED_SEARCH",
        "datePosted": f'["{date_facet}"]',
        "sortBy": f'"{sort}"',
    })
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
        for email in extract_emails(text):
            out.append(EmailContact(
                email=email,
                domain=domain,
                keyword=keyword,
                author=str(card.get("author") or ""),
                posted=str(card.get("posted") or ""),
                post_url=str(card.get("url") or ""),
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
    contacts: dict[str, EmailContact] = {}   # email → first sighting wins
    for domain in domains:
        keyword = "@" + domain
        url = build_content_search_url(keyword, date_facet)
        log.info("Searching LinkedIn posts for %r", keyword)
        _safe_goto(page, url)
        page.wait_for_timeout(SETTLE_MS)      # SDUI hydration settle
        if _check_bot_wall(page):
            log.warning("Bot-wall on %r — stopping the run. Solve any check "
                        "MANUALLY in the opened window, then rerun.", domain)
            break
        for scroll in range(max_scrolls):
            cards = page.evaluate(CONTENT_EXTRACT_JS) or []
            for contact in _contacts_from_cards(cards, domain, keyword):
                contacts.setdefault(contact.email, contact)
            if scroll < max_scrolls - 1:      # scroll between passes only
                human_scroll(page, rounds=1)
                human_pause()
        human_pause()                          # politeness between domains
    log.info("Collect pass done: %d unique emails", len(contacts))
    return list(contacts.values())
