# Secure Naukri.com Jobs Collector
### Playwright + Firefox + uBlock | Pydantic + SQLite | Typer + Rich | personal use

Built for you: **.NET 6+ yrs, ASP.NET Core / C# / Fullstack, Pune + Hyderabad** — collects job **apply links** into a local DB so a busy schedule only needs minutes.

## 1. Setup (one time)

```bash
cd /Users/aslamshaikh/Projects/PythonWebScraping
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install firefox chromium   # firefox preferred; chromium = fallback
cp .env.example .env
```

### uBlock Origin (recommended, one time)
- **Firefox**: download the `.xpi` from https://addons.mozilla.org/en-US/firefox/addon/ublock-origin/, set `UBLOCK_XPI_PATH=/abs/path/to.xpi` in `.env`. Pre-seeded into the profile on 2nd+ run (or install once via `about:addons`, it persists).
- **Chromium fallback**: unpacked dir via `UBLOCK_UNPACKED_DIR=` (optional).
- Without either, the built-in fallback tracker-blocker still runs.

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

# Tests: 98 tests, 100% coverage gate (no browser/network needed)
pytest
```

## 2b. Docs & testing phase

- `docs/PROJECT.md` — detailed project document (pipeline, modules, config, data model)
- `docs/TESTING.md` — practice progression (Books → Quotes → … → Naukri), failure taxonomy, suite guide
- `docs/BOT_DETECTION.md` — Test A/B/C signal matrix (measure exposure, never spoof)

> **Heads-up (verified on this Mac):** Naukri blocks **headless** browsers — always do the
> **first run headful** (default) so you can solve the CAPTCHA / log in once. The persistent
> profile keeps cookies; later runs succeed. If Playwright's Firefox Nightly is broken on your
> macOS it auto-falls-back to Chromium (same stealth + adblock).

## 3. Architecture (your proposed stack, as built)
```
Scheduler (APScheduler) ── schedule --hours 8,20
        │
        ▼
Browser (Playwright → Firefox → Naukri)      src/stealth_browser.py
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
src/stealth_browser.py   Firefox-first launcher, Chromium auto-fallback
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
