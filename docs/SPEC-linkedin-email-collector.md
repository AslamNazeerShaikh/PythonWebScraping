# Spec: LinkedIn Recruiter Email Collector

Status: APPROVED 2026-10-23 (all 4 clarification decisions baked in) —
         IMPLEMENTED same day; see tasks/plan.md + tasks/todo.md

## Objective

Search LinkedIn **content/posts** for `@<domain>` mentions made by recruiters
("hiring" posts where they publish their work email), extract every email
address from the post body, and land them in SQLite + an Excel snapshot the
user can work through manually when sending job applications.

Target domains (default run): `cognizant.com`, `capgemini.com`, `ltm.com`,
`hexaware.com`, `infosys.com`, `tcs.com`, `wipro.com`, `epam.com`,
`kforce.com`, `persistent.com`, `xoriant.com` (11 total).

User stories:

1. As the job seeker, I run one command and get `output/linkedin_emails_*.xlsx`
   with every email found in the last ~30 days of posts per domain.
2. As the job seeker, I can re-run later; already-seen emails are not
   duplicated but their evidence (post URL, first/last seen) is refreshed.
3. As the repo owner, nothing about the existing job pipeline changes.

### Decisions already made (clarification round, 2026-10-23)

| Question | Decision |
|---|---|
| `capgemin.com` in request | Typo → use **`capgemini.com`**; `ltm.com` stays |
| Extraction scope | **Post body only** (search-result cards; no per-post comment crawl) |
| Cross-domain emails | **Keep all emails found**, tag each row with the target domain it was discovered under |
| Date window | LinkedIn native **`past-month`** facet (≈ last 30 days), sorted `date_posted` newest-first |

## Research basis (what we reuse and from where)

- **URL grammar + date facet** — stickerdaniel/linkedin-mcp-server
  (`linkedin_mcp_server/linkedin/search_urls.py`): content search URL is
  `https://www.linkedin.com/search/results/content/?keywords=<kw>&origin=FACETED_SEARCH&datePosted=%5B%22past-month%22%5D&sortBy=%22date_posted%22`.
  Only `past-24h|past-week|past-month` are valid; unknown values are silently
  ignored by LinkedIn — so we validate before navigating (their lesson,
  verified live).
- **Post card selectors** — joeyism/linkedin_scraper
  (`company_posts.py`): `div.feed-shared-update-v2` →
  `.feed-shared-update-v2__description` / `.update-components-text` /
  `.feed-shared-text`; activity-urn data attributes; timestamp via
  `[class*="actor__sub-description"]`.
- **Email regex** — speedyapply/JobSpy (`jobspy/util.py`):
  `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` + domain validation.
- **Permalink caveat** — the MCP server found LinkedIn renders **no per-post
  permalink anchor** in the content-search tab and intercepts them from
  network JSON instead. Our stance: best-effort DOM anchors
  (`a[href*="/feed/update/"]`, `a[href*="/posts/"]`); empty post URL is
  acceptable evidence — the email + post snippet still identifies the source.
- Explicitly **not** used: CrossLinked (GPL-3.0, people enumeration via search
  engines), JobSpy's LinkedIn job search (wrong surface), comment-scrapers
  (scope decision above).

## Tech Stack

Same as the repo (no new dependencies): Python 3.11+, Playwright (sync),
Pydantic v2, SQLAlchemy + SQLite, pandas + openpyxl, tenacity, typer + rich.
License note: regex/URL/selector *patterns* are reimplemented, not copied
code — JobSpy is MIT, linkedin-mcp-server + linkedin_scraper are Apache-2.0,
so direct quoting would also be fine; we credit in `docs/LINKEDIN_RESEARCH.md`.

## Commands

```bash
# Full collector run (all 11 domains, past-month facet)
python -m src.main collect-emails

# Subset / explicit options
python -m src.main collect-emails --domains cognizant.com,ltm.com --headless
python -m src.main collect-emails --days 30 --max-scrolls 6

# Export only (DB → Excel/CSV), re-runnable
python -m src.main export-emails --fmt excel

# Gates (must stay green)
pytest                          # --cov-fail-under=100, branch coverage
graphify update .               # after code changes (AGENTS.md)
```

## Project Structure

```
src/
  linkedin_email_scraper.py   # NEW — URL builder + in-page extractor + run loop
  models.py                   # EXTEND — EmailContact (Pydantic) + EmailRow (SQLAlchemy)
  db.py                       # EXTEND — upsert_emails(), count_emails()
  export.py                   # EXTEND — load_email_frame() + export_emails()
  main.py                     # EXTEND — `collect-emails`, `export-emails` commands
  stealth_browser.py          # UNCHANGED — reused via launch_context()
  config.py                   # EXTEND — EMAIL_DOMAINS, EMAIL_MAX_SCROLLS, …
tests/
  test_email_collector.py     # NEW — offline fixtures, no network
  fixtures/linkedin_content_search.html  # NEW — saved search-results DOM
docs/
  SPEC-linkedin-email-collector.md  # this file
  LINKEDIN_RESEARCH.md              # append §11: email-collector decision record
output/
  linkedin_emails_<ts>.xlsx         # gitignored (output/ already ignored)
```

## Design

### Data contract

```python
# Layer 3 — Pydantic validation gate
class EmailContact(BaseModel):
    email: str            # lowercased, format+domain validated
    post_id: str = ""     # activity URN / permalink / fallback key (dedupe unit)
    domain: str           # target domain this post was searched under (e.g. "cognizant.com")
    post_url: str = ""    # best-effort permalink; "" when LinkedIn exposes none
    author: str = ""      # post author name from the card
    posted: str = ""      # relative/absolute date text from the card
    snippet: str = ""     # ~200-char window around the email (evidence)
    keyword: str = ""     # search keyword used, e.g. "@cognizant.com"
    first_seen: datetime  # set by DB on insert
    last_seen: datetime   # bumped on every re-sighting
```

```python
# Layer 4 — SQLAlchemy: table `contact_emails`
# PK: surrogate id; UNIQUE (email, post_id) — one row per (email, post)
# sighting. The same address re-posted across several posts is kept (hiring
# still ongoing); only a re-sighting of the *same* post bumps last_seen.
```

### Pipeline (mirrors README §3: Browser → Extract → Pydantic → SQLite → Excel)

1. **URL builder** `build_content_search_url(keyword, date_facet="past-month",
   sort="date_posted") -> str` — pure function; raises `ValueError` on
   unknown facet (LinkedIn would silently ignore it).
2. **Browser** — `launch_context()` (existing persistent `.pw-profile-
   chromium`, first run headful for manual login; **never solve CAPTCHAs** —
   on bot-wall/security pages, stop with guidance, same policy as Naukri).
3. **Per domain loop**: goto URL (tenacity: retry *transient* only —
   timeouts/5xx; never retry security/verification pages), wait for `main`,
   then scroll `_EMAIL_SCROLLS_PER_PAGE` × N times (infinite scroll, no
   `&start=` pagination), extracting cards each pass.
4. **In-page JS extractor** (function injected per scroll): collect
   `div.feed-shared-update-v2` cards → text, author, timestamp, permalink →
   return plain dicts (untrusted — validated next layer).
5. **Pydantic gate** — `EmailContact` per email found; regex over card text;
   dedupe within a card.
6. **SQLite upsert** — `upsert_emails(contacts) -> (new, total)`.
7. **Excel** — `export_emails(fmt="excel")` → `output/linkedin_emails_<ts>.xlsx`
   with one sheet, columns: `email, domain, author, posted, post_url,
   snippet, keyword, first_seen, last_seen`, sorted domain → email.
8. **Politeness** — `MIN_DELAY_S..MAX_DELAY_S` random pause between domains
   and between scroll batches (reuse existing settings).

## Code Style

Match the repo (from `src/naukri_scraper.py` / `src/db.py`): module docstring
stating layers & decisions, `from __future__ import annotations`, type hints,
Google-style docstrings with Args/Returns/Raises, module logger
`log = logging.getLogger(__name__)`, no bare `except`, constants in
`UPPER_SNAKE`.

```python
def build_content_search_url(keyword: str, date_facet: str = "past-month",
                             sort: str = "date_posted") -> str:
    """Return a LinkedIn content-search URL for ``keyword``.

    Args:
        keyword: Search string, e.g. ``"@cognizant.com"``.
        date_facet: One of ``past-24h``/``past-week``/``past-month`` —
            anything else is silently ignored by LinkedIn, hence validated.

    Returns:
        Fully-encoded ``https://www.linkedin.com/search/results/content/…`` URL.

    Raises:
        ValueError: If ``date_facet`` is not a supported token.
    """
```

## Testing Strategy

- **Framework/gate:** pytest, `tests/test_email_collector.py`, must keep
  `--cov-fail-under=100` + branch coverage green (`pytest`).
- **Offline only:** saved DOM fixture (`fixtures/linkedin_content_search.html`)
  drives the extractor via a fake page object; no live LinkedIn in CI.
- Test levels: URL builder (facet validation/encoding), extractor (fixture →
  dicts → `EmailContact`, incl. no-email cards, missing permalink/author),
  dedupe logic, DB upsert semantics (new vs re-sighting, evidence refresh),
  export frame (columns, sorting, empty DB), CLI wiring (typer runner,
  like `tests/test_main.py`), config overrides.
- Live verification is a **manual practice run**, documented in
  `docs/TESTING.md` style, never part of pytest.

## Boundaries

- **Always:** keep `pytest` at 100% coverage; SQLite remains source of truth;
  no CAPTCHA solving; no secrets in commits; politeness delays on every
  network hop; `graphify update .` after code changes.
- **Ask first:** new DB table (this spec requests it); new dependencies
  (none planned); scheduler/CI changes; changing existing job-pipeline
  behaviour.
- **Never:** commit `.env`, `output/`, `jobs.db` contents; scrape while not
  logged in / against security walls; modify `vendor/`.

## Fair use (extends LINKEDIN_RESEARCH §10)

Public posts only, personal job-search use, one account, rate-limited
(11 domains × ~6 scrolls/minutes per run ≈ minutes, not hours). Emails are
used only for the user's own manual job applications; the Excel stays in
gitignored `output/`. No bulk messaging automation — sending stays manual.

## Success Criteria

1. `python -m src.main collect-emails` runs end-to-end on a logged-in
   profile and writes `output/linkedin_emails_*.xlsx` containing the known
   example (`neha.pandey@ltm.com`, found under `ltm.com`) when that post is
   within the past-month window.
2. All 11 default domains are searched with the `past-month` facet, newest
   first.
3. Re-running does not duplicate rows; `last_seen` bumps and evidence fields
   fill in.
4. `pytest` green at 100% branch coverage; `graphify update .` clean.
5. `docs/LINKEDIN_RESEARCH.md` gains a §11 decision record citing the three
   reference sources.
6. Existing commands (`scrape`, `export`, `stats`, `parse`, `schedule`) and
   their tests are untouched/unchanged in behaviour.

## Implementation note (2026-10-23)

Shipped and gated (pytest 242 passed, 100 % branch coverage) except
Success Criterion #1's live Excel: the first live run surfaced the
authwall (profile had no LinkedIn session) → 0 emails. Fixed at the root
(`_on_login_wall` + one manual-ENTER login prompt, never automated) with
regression tests; live verification is deferred until the user performs
the one-time sign-in (`scripts/probe_content_search.py --login`, then
`collect-emails`). Card selectors (joeyism-derived) are offline-tested but
not yet live-confirmed — the probe reports a selector census if the first
signed-in run still finds nothing.

**Login-wait fix (2026-10-24):** the sequence "prompt ENTER → immediately
re-`goto` the search" was reloading the sign-in page out from under the user
(the reported "page refreshes too early at login"). Replaced with
`_wait_for_login()` — a **passive `page.url` poll that never navigates**, giving
the human unlimited time to type credentials + clear 2FA (`LOGIN_GRACE_S`,
default 300 s), followed by **one** clean navigation to the target search once
the wall has cleared. If the wall never clears it stops with guidance rather
than reloading the page (regression test pins `goto` at 1 — no reload).
`pytest`: 246 passed, 100 % branch coverage. The persistent profile means the
one-time login then persists across domains and reruns.

## Implementation update (2026-10-25)

1. **Dedupe unit is now `(email, post)`**, not `email` alone: recruiters
   re-posting the same address across several posts are kept (each post is a
   distinct row), while a re-sighting of the *same* post bumps `last_seen`.
   `post_id` comes from the post's SDUI `componentkey`
   (`update-card-focus<hash>FeedType_…`), falling back to the permalink and
   then an `author|posted|text[:40]` key.
2. **"Show more" expansion**: `_expand_show_more` clicks `…see more` /
   `Show more` affordances before extraction so emails hidden behind
   truncated bodies are revealed (best-effort, never raises).
3. **Domain-only filtering**: only addresses whose own domain equals the
   searched domain are stored. A post containing `jobs@cognizant.com` plus
   `personal@gmail.com` contributes the Cognizant address only. Multiple
   matching addresses in one post become separate rows.
4. **URL-2-only, one search per domain**: each domain is typed once into the
   global search box, switched to the native **Posts** tab
   (`origin=SWITCH_SEARCH_VERTICAL`), then **Latest** + **Past month** are
   applied via the real radio controls and **Show results**. The blended
   all-results cluster (URL 1) is no longer scraped — the sorted content
   feed is the single source of truth and saves search requests.
5. **Verified SDUI selectors (live 2026-10-25)**: posts are
   `[role="listitem"]` units inside `[data-testid="lazy-column"]`, each with
   one `[data-testid="expandable-text-box"]` body. The previous direct-child
   logic treated a *chunk* of posts as one post and lost most emails.
6. **Expand before reading**: every post's `expandable-text-button`
   ("… more") is clicked once, then a short settle precedes extraction. The
   button is marked so a later checkpoint cannot toggle it back closed.
7. **Targeted, human-like scrolling**: mouse-wheel bursts over the feed,
   with the true scroll container (`<main>`) nudged to the lazy sentinel when
   a batch stalls. Scrolling stops as soon as the domain's unique-email
   target is met; `EMAIL_MAX_SCROLLS` (default 40 rounds) is only a safety
   cap. Three no-growth rounds end a sparse feed.
8. **Crash-safe checkpoints**: `run_collect(..., on_batch=…)` hands each new
   batch to the CLI, which upserts into SQLite and rewrites
   `output/linkedin_emails_partial.xlsx`. A broken session still leaves the
   harvested emails on disk; a final timestamped snapshot is written at the
   end.
9. **Config**: `EMAIL_DEFAULT_TARGET` (default 10) is used when a CSV
   domain has no `:N`; `EMAIL_MAX_SCROLLS` is the per-domain round cap.

## Input CSV + export rules (2026-10-26)

`collect-emails --input-csv targets.csv` accepts any of:

```csv
@cognizant.com:5
@capgemini.com:2
```

```csv
domain,target
@cognizant.com,5
@capgemini.com,2
```

```csv
"@cognizant.com:5,@capgemini.com:2"
```

Domains may omit `@`; targets are positive integers, defaulting to
`EMAIL_DEFAULT_TARGET`. Rows are processed in first-seen CSV order.

The workbook is derived from SQLite with these guarantees:

* **No foreign domains** — a row whose email domain differs from the row's
  searched domain is discarded at export time (legacy contamination included).
* **One row per email** — duplicate sightings collapse to the newest post
  (parsed from `posted`, falling back to `last_seen`), preserving that post's
  `post_id`, author, date, URL, and snippet.
* **Grouped and alphabetical** — output is ordered by `domain`, then `email`.

## Related path (2026-10-27)

`collect-role-emails` is a separate, analysis-only command for
`"<phrase> @<domain>"` searches. It never writes `contact_emails` and does not
change this collector. See
[`SPEC-linkedin-role-email-collector.md`](SPEC-linkedin-role-email-collector.md).

## Open Questions

1. **Scroll depth default** — proposal: `--max-scrolls 6` per domain
   (~60 cards). Want more/less? (Trade-off: runtime + bot-wall exposure.)
2. **`@domain` keyword vs `domain` keyword** — proposal: search the literal
   `"@cognizant.com"` (matches your manual search exactly). Some recruiters
   write the email as `name@ cognizant.com` or plain `cognizant.com`; should
   we run a second keyword pass without the `@`? (Doubles runtime.)
3. **Company page scan as a future phase?** — out of scope here, but note
   joeyism's `CompanyPostsScraper` could later sweep
   `/<company>/posts/` for missed posts. Defer?
