# Implementation Plan: Lane Job-Quality Gates (irrelevant · pure-frontend · external-apply · dedupe)

Implements `docs/SPEC-lane-job-quality-gates.md` (approved 2026-10-21).
User-confirmed decisions: dedupe key `(title, company)`; `react`/`angular` are
search keywords but not relevance anchors; lane scans use `max_jobs: 150`.
Scope of this run: Pune + Hyderabad + Bengaluru, experience 6, days 3.

## Overview

Four durable, API-only gates (no Playwright) so lane collects + exports stop
carrying Naukri's fuzzy-search junk: unrelated postings, pure-frontend roles,
duplicate reposts, and postings whose Apply leaves Naukri for the company's
own portal. One opt-out flag (`exclude_unwanted`, default `true`) on collect
and export; runbook + WEB_API updated; pytest stays at 100 % coverage.

## Architecture Decisions

- **Gates live beside the existing Java gate** (`src/naukri_scraper.py`): pure
  regex functions over `title + skills + snippet`, so collect time and export
  time judge the same text and stay deterministic.
- **External-apply is detected from the search row** (`companyApplyJob` /
  `clientCareersUrl` / `applyRedirectUrl` — JobSpy semantics, live-verified):
  zero extra requests. A non-`naukri.com` `apply_url` host at export time is
  the safety net for browser-enriched rows.
- **Skills scans stay raw**: `api_scan_skills` pins `exclude_unwanted: False`
  so exploratory keyword scans keep today's behaviour.
- **Browser fallback path gets the same G1+G2 unconditionally** (like the Java
  gate already is) and drops the stale `.NET`-only `is_relevant`, which would
  have silently discarded Lane 1 AI jobs.
- **No schema change** — no migration; SQLite stays source of truth.

## Task List

### Phase 1 — Foundation (gate functions)

- [ ] Task 1: Gate functions + regexes in `src/naukri_scraper.py`
  (`should_exclude_irrelevant_job`, `should_exclude_frontend_job`, remove
  `is_relevant` + its test) — tests first.
  Files: `src/naukri_scraper.py`, `tests/test_scraper.py`. Size: S.

### Phase 2 — Wiring (consumers)

- [ ] Task 2: Export gates + dedupe + `exclude_unwanted` in `src/export.py`.
  Files: `src/export.py`, `tests/test_export.py`. Size: S. Depends: 1.
- [ ] Task 3: API-collect gates (`is_external_apply`, `exclude_unwanted`) in
  `src/web/nkapi.py`; skills scan pins `False`.
  Files: `src/web/nkapi.py`, `tests/test_web.py`. Size: S. Depends: 1.
- [ ] Task 4: Contract plumbing — `exclude_unwanted` on `CollectRequest` /
  `ExportRequest`, orchestrator runners, CLI `--exclude-unwanted`.
  Files: `src/web/schemas.py`, `src/web/orchestrator.py`, `src/main.py`,
  `tests/test_web.py`, `tests/test_main.py`. Size: M. Depends: 2, 3.
- [ ] Task 5: Browser path — apply G1+G2 (pre- and post-enrichment).
  Files: `src/naukri_scraper.py`, `tests/test_scraper.py`. Size: S. Depends: 1.

### Checkpoint: Gates
- [x] `python3 -m pytest` green at `--cov-fail-under=100`; spot-check a live
  search page against the gates (junk drops, lanes survive).

### Phase 3 — Docs + delivery

- [x] Task 6: Docs — `docs/LANES_RUNBOOK.md` §1c + params, `docs/WEB_API.md`
  contract lines.
  Files: `docs/LANES_RUNBOOK.md`, `docs/WEB_API.md`. Size: S.
- [x] Task 7: Run it — start server, collect Lane 1 then Lane 2
  (`pune,hyderabad,bengaluru`, exp 6, `days: 3`, `max_jobs: 150`,
  `exclude_unwanted: true`), export `{"format":"excel","days":1}` → download,
  sanity-check, hand over the Excel. Size: M (ops).

### Checkpoint: Complete
- [x] All spec success criteria met; Excel delivered; graph updated.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| 406 rate-limit on back-to-back pages | Med | keep 3–7 s pacing; sequential lanes; retry after a pause |
| Gates keep fewer rows than `max_jobs` | Med | `max_jobs: 150` + `max_pages = max_jobs//20+2` pages per lane |
| False drops (relevant job killed by a gate) | High | truth-table tests; title+skills anchors; snippet needs a *strong* term |
| Coverage gate trips on a new branch | Med | tests written with (before) each function; full pytest after every task |

## Verification

`python3 -m pytest` (coverage gate baked into `pyproject.toml`), then live:
collect summaries report `source: "api"` + drop counters, export downloads,
every `apply_url` in the sheet is `naukri.com`, no `(title, company)` repeats.
