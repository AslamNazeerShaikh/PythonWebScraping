# Secure Naukri.com Jobs Collector
### Playwright + Chrome + uBlock Origin Lite | Pydantic + SQLite | Typer + Rich | personal use

Built for you: **.NET 6+ yrs, ASP.NET Core / C# / Fullstack, Pune + Hyderabad** — collects job **apply links** into a local DB so a busy schedule only needs minutes.

## 1. Setup (one time)

```bash
cd /Users/aslamshaikh/Projects/PythonWebScraping
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # Chrome-only stack (Firefox engines don't start here)
cp .env.example .env
bash vendor/download-ubol.sh  # fetch uBlock Origin Lite (unpacked, gitignored)
```

### uBlock Origin Lite (real MV3 blocking, verified live)
`vendor/download-ubol.sh` downloads the official build from Mozilla AMO and
patches its manifest for Chromium (`service_worker`). Set
`UBLOCK_UNPACKED_DIR=vendor/ubol-chrome` (default). Verified: 13/13
tracker/ad requests `ERR_BLOCKED_BY_CLIENT` on forbes.com — incl. DataDome's
fingerprinting tag. Loaded headed-only (headless-shell can't load
extensions); headless runs fall back to the built-in tracker-blocker.

## 2. Usage

```bash
source .venv/bin/activate

# Full pipeline: browser -> Pydantic -> SQLite + timestamped JSON/CSV
python -m src.main scrape
python -m src.main scrape --keywords "asp.net core c# .net" --locations "pune,hyderabad" --days 7 --pages 3
python -m src.main scrape --no-enrich --pages 2        # fast link sweep (<2 min)
python -m src.main scrape --browser chromium --headless # background (after 1 headful run)

# DB overview / exports (Pandas)
python -m src.main stats
python -m src.main export --format csv --location pune
python -m src.main export --format excel

# Offline re-parse of a saved page (no browser needed)
python -m src.main parse output/debug_last_search.html

# Daily runs at 08:05 + 20:05 (blocking; or use cron/launchd)
python -m src.main schedule --hours 8,20

# Tests: 93 tests, 100% coverage gate (no browser/network needed)
pytest

# Live practice suite: TESTING.md Tests 1-7 on real sandboxes (Chrome + uBOL)
.venv/bin/python scripts/practice_tests.py
```

## 2b. Docs & testing phase

- `docs/PROJECT.md` — detailed project document (pipeline, modules, config, data model)
- `docs/TESTING.md` — practice progression (Books → Quotes → … → Naukri), failure taxonomy, suite guide
- `docs/BOT_DETECTION.md` — Test A/B/C signal matrix (measure exposure, never spoof)

> **Heads-up (verified on this Mac):** Naukri blocks **headless** browsers — always do the
> **first run headful** (default) so you can solve the CAPTCHA / log in once. The persistent
> profile keeps cookies; later runs succeed. Chrome-only by decision: no Firefox
> engine starts in this environment (stable 155 and Nightly both die on profile spawn).

## 3. Architecture (your proposed stack, as built)
```
Scheduler (APScheduler) ── schedule --hours 8,20
        │
        ▼
Browser (Playwright → Chrome + uBO Lite)        src/stealth_browser.py
        │  persistent profile, stealth init JS, uBlock + fallback blocker,
        │  human pauses/scrolls, manual-solve bot-wall handling
        ▼
Extraction ── live: in-page JS (computed-style honeypot guards)
             offline: BeautifulSoup + lxml twin                   src/parser.py
        │  skips display:none / aria-hidden / href traps, dedupes by job id
        ▼
Validation (Pydantic Job)                    src/models.py
        │  one contract; bad cards dropped with a named-field warning
        ▼
Persistence (SQLAlchemy → SQLite)            src/db.py, jobs.db (gitignored)
        │  upsert by job_id, first_seen/last_seen, scrape_runs log
        ├──► Pandas → CSV / Excel            src/export.py
        └──► JSON/CSV snapshots              output/ (gitignored)
CLI (Typer) + output (Rich) + retries (tenacity, transient-only) + logging (std)
```

SQLite is the source of truth — set `DATABASE_URL` to Postgres later with no code change.

## 4. Files

```
src/config.py            env-driven settings (your defaults pre-filled)
src/stealth_browser.py   Chrome-only launcher + uBO Lite wiring
src/naukri_scraper.py    search URLs, JS extractors, tenacity goto, Pydantic coercion
src/parser.py            BS4+lxml offline parser (debug without re-hitting Naukri)
src/models.py            Pydantic Job + SQLAlchemy JobRow / ScrapeRun
src/db.py                engine, init, upsert (dedupe), fetch, run log
src/export.py            Pandas CSV/Excel exports
src/scheduler.py         APScheduler daily runs
src/main.py              Typer commands: scrape | export | stats | parse | schedule
src/log.py               logging setup (LOG_LEVEL)
jobs.db                  local DB (gitignored)        output/  snapshots (gitignored)
.pw-profile*/            browser profiles (gitignored) .env    your secrets (gitignored)
```

Deliberately **not** included: Selenium/Scrapy, undetected-chromedriver, fingerprint-spoofing
packages, proxy rotation, CAPTCHA solvers — Playwright covers the browser side; the latter group
is redundant or aimed at circumventing anti-abuse controls.

## 5. Fair-use note
Public listings only, rate-limited, for your personal job search. Respect Naukri's ToS and
`robots.txt`; don't share/sell scraped data or run at high concurrency. If a block page appears,
back off and retry later.
