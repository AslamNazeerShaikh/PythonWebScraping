# Project Document — Secure Naukri.com Jobs Collector

> **Purpose.** Personal job-search assistant for a .NET developer (6+ yrs,
> ASP.NET Core / C# / Fullstack, Pune + Hyderabad) with little spare time:
> collect job apply links into a local database on a schedule, review a short
> list, apply fast.
>
> **Stack.** Python + Playwright + Chrome (+ uBlock Origin Lite) for collection;
> BeautifulSoup + lxml for offline parsing; Pydantic for validation;
> SQLAlchemy + SQLite for storage; Pandas + openpyxl for export; APScheduler
> for scheduling; tenacity for transient retries; Typer + Rich for the CLI;
> std `logging`; python-dotenv for config.
>
> **Non-goals.** No Selenium/Scrapy, no stealth-spoofing packages, no proxy
> rotation, no CAPTCHA solving. The collector is a polite, low-volume browser,
> not an evasion tool (see `BOT_DETECTION.md` for the philosophy).

---

## 1. How it works (pipeline)

```
Scheduler (APScheduler, `schedule --hours 8,20`)
        │  one polite pass per trigger, max_instances=1
        ▼
Browser (Playwright → Chrome + uBO Lite)            stealth_browser.py
        │  persistent profile · stealth init JS · uBlock + fallback blocker
        │  human pauses/scrolls · manual-solve bot-wall handling
        ▼
Extraction — LIVE: in-page JS (computed-style honeypot guards)
             OFFLINE twin: BeautifulSoup + lxml  parser.py / naukri_scraper.py
        │  skips display:none · aria-hidden · href traps · 0-size · off-screen
        │  dedupes by /job-listings-<slug>-(<id>)
        ▼
Validation (Pydantic Job)                        models.py
        │  single contract; bad cards dropped with a named-field warning
        ▼
Persistence (SQLAlchemy → SQLite, jobs.db)       db.py
        │  upsert by job_id · first_seen/last_seen · scrape_runs audit log
        ├──► Pandas → CSV / Excel snapshots      export.py
        └──► timestamped JSON/CSV snapshots      output/  (naukri_scraper.save_results)
CLI (Typer) · output (Rich) · retries (tenacity, transient-only) · logging
```

**Key invariants**

1. SQLite is the source of truth; every file export is a disposable snapshot.
2. `job_id` (Naukri numeric id) is the dedupe key end-to-end.
3. Retries cover transient network/timeouts only (max 3, exponential backoff).
   HTTP 403/429/CAPTCHA walls are never retried — the run pauses for a manual
   solve instead of hammering.
4. First run is headful (solve CAPTCHA / log in once); cookies persist in the
   profile, later runs succeed.

## 2. Module reference

| Module | Responsibility | Key functions |
|---|---|---|
| `config.py` | `.env`-driven `SETTINGS` singleton | `_get*` readers, `Settings`, `SETTINGS` |
| `stealth_browser.py` | Chrome-only launcher + uBO Lite wiring | `launch_context`, `_launch_chromium`, `_extension_args`, `human_pause` |
| `naukri_scraper.py` | Search URLs, extractors, pipeline | `build_search_url`, `scrape_search_page`, `enrich_job`, `run_scrape`, `save_results`, `coerce_job`, `normalize_raw` |
| `parser.py` | Offline BS4+lxml twin of the JS extractors | `parse_search_html`, `parse_detail_html` |
| `models.py` | Pydantic `Job` + ORM `JobRow`/`ScrapeRun` | `Job.skill_text`, `JobRow.from_job/to_job` |
| `db.py` | Engine, sessions, upsert, audit | `init_db`, `upsert_jobs`, `record_run`, `fetch_all_jobs`, `count_jobs` |
| `export.py` | Pandas CSV/Excel snapshots | `load_frame`, `export_jobs` |
| `scheduler.py` | Daily cron triggers | `run_scheduled` |
| `main.py` | Typer commands + Rich tables | `do_scrape`, `scrape/export/stats/parse/schedule` |
| `log.py` | Std-logging setup | `setup_logging` |

## 3. Configuration (`.env`, see `.env.example`)

| Var | Default | Meaning |
|---|---|---|
| `KEYWORDS` | `asp.net core c# .net fullstack` | Search keywords (`k`) |
| `LOCATIONS` | `pune,hyderabad` | One search per location (`l`) |
| `EXPERIENCE` / `DATE_FILTER` | `6` / `7` | Years exp · posted last N days |
| `MAX_PAGES_PER_SEARCH` / `MAX_JOBS_TOTAL` | `3` / `60` | Politeness caps |
| `ENRICH_DETAILS` | `true` | Visit each job page (`--no-enrich` skips) |
| `BROWSER` / `HEADLESS` | `chromium` / `false` | Engine (chromium-only) · background |
| `USER_DATA_DIR` | `.pw-profile` | Persistent profile (cookies, uBO) |
| `TIMEZONE` / `LOCALE` | `Asia/Kolkata` / `en-IN` | Fingerprint consistency |
| `UBLOCK_UNPACKED_DIR` | `vendor/ubol-chrome` | uBO Lite dir (fetch via `vendor/download-ubol.sh`; headed-only) |
| `ADBLOCK_FALLBACK` | `true` | Built-in tracker-blocker |
| `MIN_DELAY_S` / `MAX_DELAY_S` / `NAV_TIMEOUT_MS` | `2.0` / `5.0` / `45000` | Polite timing |
| `OUTPUT_DIR` / `DATABASE_URL` / `LOG_LEVEL` | `output` / `sqlite:///jobs.db` / `INFO` | Outputs |

## 4. Commands

```bash
source .venv/bin/activate
python -m src.main scrape --keywords "asp.net core c# .net" --locations "pune,hyderabad" --days 7 --pages 3
python -m src.main scrape --no-enrich --pages 2          # fast link sweep
python -m src.main stats                                  # DB overview
python -m src.main export --format excel --location pune # filtered snapshot
python -m src.main parse output/debug_last_search.html   # offline re-parse
python -m src.main schedule --hours 8,20                 # daily 08:05 + 20:05
pytest                                                    # 93 tests, 100% coverage gate
```

## 5. Data model

`jobs(job_id PK, title, company, location, search_location, experience, salary,
posted, url, apply_url, snippet, description, skills, first_seen, last_seen)` ·
`scrape_runs(id, started_at, keywords, locations, pages, found, new_jobs)`.

## 6. Known environment notes (verified)

- Chrome-only by decision: no Firefox engine (stable 155, Nightly 1543)
  starts in this environment — both die spawning the profile/content
  process (`Operation not permitted` on helper exec). Chromium works.
- uBO Lite loads headed-only (headless-shell can't load extensions);
  headless runs use the fallback blocker. Verified functionally live.
- Retries catch BOTH `TimeoutError` classes: Playwright raises its own, not
  the builtin — catching only the builtin silently disables retries
  (found by the live practice suite, regression-tested).
- Naukri blocks headless browsers: first run must be headful.

## 7. Fair use

Public listings only, rate-limited, personal job search. Respect Naukri's ToS
and `robots.txt`; never share/sell scraped data or run concurrent workers. On
a block page: back off, retry later.

## 8. Knowledge graph (Graphify)

This repo ships a queryable map of itself ([details](GRAPHIFY.md),
[upstream](https://github.com/Graphify-Labs/graphify)): `graphify-out/`
(`graph.html`, `GRAPH_REPORT.md`, `graph.json`; 364 nodes, 12 communities).
Query before grepping: `graphify query "<question>"`. Rebuild after code
changes: `graphify update .` (free). Excludes: `vendor/`, `docs/evidence/`
(see `.graphifyignore`).
