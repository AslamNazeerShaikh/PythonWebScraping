# Implementation Plan: LinkedIn Recruiter Email Collector

Implements `docs/SPEC-linkedin-email-collector.md` (approved 2026-10-23).
User-confirmed decisions: `capgemini.com` (typo fix), **post-body only**
extraction, keep **all** emails tagged by target domain, `past-month` facet
for the ~30-day window. Scroll default `--max-scrolls 6`; keyword is the
literal `"@<domain>"`; company-page sweep deferred (spec open Q2/Q3 resolved
as: single `@domain` pass, no second pass).

## Overview

New CLI path `python -m src.main collect-emails` that loops 11 target
domains, opens LinkedIn **content search** (`/search/results/content/?…`
with `datePosted=["past-month"]`, `sortBy="date_posted"`) in the existing
persistent stealth profile, scrolls the infinite feed, extracts post cards
in-page, regexes every email out of the post body, and upserts into a new
`contact_emails` SQLite table; `export-emails --fmt excel` renders the
working Excel (`output/linkedin_emails_<ts>.xlsx`). No new dependencies; the
job pipeline is untouched.

## Architecture Decisions

- **URL grammar borrowed (as patterns) from linkedin-mcp-server**
  (Apache-2.0): validate the date facet *before* navigating — LinkedIn
  silently ignores unknown facets. Sort newest-first.
- **Extraction split into two testable halves**: in-page JS
  (`CONTENT_EXTRACT_JS`, mirrors joeyism's `feed-shared-update-v2`
  selectors) returns plain card dicts; pure Python
  `_contacts_from_cards()` applies JobSpy's email regex → `EmailContact`.
  Tests drive the Python half with fake card dicts (repo's FakePage
  convention) — no live LinkedIn in pytest.
- **Post URL is best-effort** (`a[href*="/feed/update/"]` / `/posts/`),
  empty string acceptable — per the MCP server's finding that content
  search renders no per-post permalink anchors.
- **email = primary key** — one row per address; re-sighting bumps
  `last_seen` and backfills empty evidence fields (author/post_url/snippet).
  Cross-domain evidence overwrites the tag (newest search wins) per spec
  "keep all, tagged".
- **Same safety rails as Naukri**: tenacity retries transient-only
  (never 403/429/security walls), `BOT_WALL_PATTERNS`-style guard stops the
  run with guidance, `human_pause()` between domains and scroll batches,
  never solve CAPTCHAs.
- **No web/MCP surface** — CLI + Excel only for this phase (scheduler/API
  out of scope; keeps blast radius small).

## Task List

### Phase 1: Foundation (data contract)
- [ ] Task 1: `EmailContact` (Pydantic) + `EmailRow` (SQLAlchemy, table
  `contact_emails`) + converters in `src/models.py`
- [ ] Task 2: Settings (`EMAIL_DOMAINS`, `EMAIL_MAX_SCROLLS`,
  `EMAIL_DATE_FACET`) in `src/config.py` + `.env.example`; DB helpers
  `upsert_emails()` / `count_emails()` in `src/db.py`

### Checkpoint: Foundation
- [ ] `python3 -m pytest` green at 100 % (new model/db tests included)

### Phase 2: Core collector
- [ ] Task 3: `src/linkedin_email_scraper.py` — `build_content_search_url`,
  `EMAIL_RE` + `extract_emails()`, `CONTENT_EXTRACT_JS`,
  `_contacts_from_cards()`, bot-wall guard, `_safe_goto`
- [ ] Task 4: `run_collect(context, domains, …)` loop — scrolls, pauses,
  per-domain dedupe, progress logging; wires `launch_context` from CLI
- [ ] Task 5: Export — `load_email_frame()` + `export_emails()` in
  `src/export.py` (columns/order per spec)

### Checkpoint: Core
- [ ] `python3 -m pytest` green; fake end-to-end (FakeContext → DB → Excel)

### Phase 3: CLI + polish
- [ ] Task 6: `collect-emails` + `export-emails` Typer commands in
  `src/main.py` (+ tests via typer runner)
- [ ] Task 7: Docs — spec status → APPROVED/IMPLEMENTED, `LINKEDIN_RESEARCH.md`
  §11 decision record, README mention, `.env.example`, `docs/TESTING.md`
  practice-run note
- [ ] Task 8: Full gate — `python3 -m pytest` 100 %, `graphify update .`,
  live practice run of `collect-emails` on the logged-in profile

### Checkpoint: Complete
- [ ] All spec success criteria met; commit + push

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LinkedIn card markup differs in search vs feed | Med | Candidate selector list (joeyism's proven set) + empty-result guidance; fixture test keeps parser honest |
| Bot-wall on automated scroll | Med | Headful first run, politeness delays, stop-with-guidance (never CAPTCHA-solve) — existing policy |
| No permalinks in content search | Low | Best-effort URL; email+snippet+author is the evidence (spec) |
| Coverage gate (100 % branch) | Med | Fake card dicts + FakeContext follow repo conventions; JS string kept dumb |
| 11 domains → long runtime | Low | 6-scroll cap/domain, random delays, resumable (DB dedupe) |

## Open Questions

- None blocking (spec Q1–Q3 resolved at approval: 6 scrolls, single
  `@domain` pass, company sweep deferred).
