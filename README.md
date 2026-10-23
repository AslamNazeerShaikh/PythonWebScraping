# Jobs Collector

A polite, extensible job-listings collector with a FastAPI control plane. It gathers public job postings into a local SQLite database, analyzes skill demand across them, and exports hyperlinked Excel/CSV snapshots — driven from a dashboard, REST API, CLI, scheduler, or any MCP-compatible AI client.

The default board adapter targets Naukri.com (direct search-API fast path with a Playwright browser fallback), but the pipeline — collect → validate → store → analyze → export — is board-agnostic and open to new adapters.

## What it can do

- **Collect listings** into SQLite (deduplicated by posting id, with first/last-seen tracking) via a direct search-API fast path, falling back to a polite Playwright/Chromium pass with human-like pacing.
- **Filter at every stage** — relevance gating plus a configurable stack filter (e.g. drop pure-Java postings while keeping mixed-stack ones) applied at collect time and again at export time.
- **Analyze skill demand** across fresh postings: top skills ranked by distinct-company or per-posting counts, each with a per-company breakdown, rendered in the dashboard and as a downloadable report.
- **Export snapshots** — CSV or Excel where each job title is a true clickable hyperlink to the apply page.
- **Serve a control plane** (one process, one port): dashboard UI, REST endpoints with cancel twins for every long run, live progress with stage timelines, run logs, and a DB explorer.
- **Talk to AI agents** over Streamable HTTP MCP (curated tools: stats, search, start scrape/skill-scan/collect, run status, cancel) with an interactive Scalar API reference alongside Swagger/OpenAPI.
- **Run on a schedule** (APScheduler cron) or headlessly from the CLI with Rich tables.

## Tech stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI (bigger-applications layout: routers, dependencies, internal ops) |
| AI / agent interface | FastMCP (Streamable HTTP, curated tools), Scalar API reference |
| Collection | Playwright (bundled Chromium, persistent profile) + uBlock Origin Lite, `httpx` API client |
| Parsing | In-page JS extractors + BeautifulSoup/lxml offline twin |
| Validation | Pydantic v2 |
| Storage | SQLAlchemy 2 → SQLite (Postgres-ready via `DATABASE_URL`) |
| Analysis / export | Pandas + openpyxl |
| Scheduling / retries | APScheduler, tenacity (transient-only) |
| CLI / UX | Typer + Rich, std `logging`, python-dotenv |
| Tests | pytest + pytest-cov, 100% coverage gate, no browser/network in tests |

Deliberately **not** included: Selenium/Scrapy, fingerprint-spoofing or undetected-driver packages, proxy rotation, CAPTCHA solvers. Polite rate limits, honeypot-safe extraction, and manual-solve bot-wall handling are built in.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
bash vendor/download-ubol.sh   # fetch uBlock Origin Lite (unpacked, gitignored)
```

Start the control plane (recommended — dashboard + REST + MCP):

```bash
python -m src.main web
# open http://127.0.0.1:8000        → dashboard: collect lanes, skill scans, exports, runs, charts
# open http://127.0.0.1:8000/scalar → interactive API reference (/docs has Swagger UI)
```

Or use the CLI:

```bash
source .venv/bin/activate

# Full pipeline: browser/API → validated jobs → SQLite + timestamped JSON/CSV
python -m src.main scrape --keywords "python backend api" --locations "remote" --days 7 --pages 3
python -m src.main scrape --no-enrich --pages 2   # fast link sweep without detail visits

# LinkedIn email collector: recruiter emails from posts, last ~30 days
python -m src.main collect-emails                                  # all 11 target domains
python -m src.main collect-emails --domains cognizant.com,ltm.com  # subset, --max-scrolls N
python -m src.main export-emails --format excel                    # re-export contact snapshot

# Inspect and export
python -m src.main stats
python -m src.main export --format excel
python -m src.main export --format csv --location remote
python -m src.main export --format excel --include-java   # opt out of the stack filter

# Offline re-parse of a saved page (no browser needed)
python -m src.main parse output/debug_last_search.html

# Daily runs at 08:05 + 20:05 (blocking; or use cron/systemd)
python -m src.main schedule --hours 8,20
```

Typical dashboard flow: collect one lane per search profile (`POST /api/collect` with `keywords`, `location`, `experience`, `days`, `max_jobs`) → repeat for other profiles → `POST /api/exports {format: excel}` → open the spreadsheet and click titles to apply. See `docs/LANES_RUNBOOK.md` for a worked multi-lane example.

## Configuration

Everything is `.env`-driven (see `.env.example`); CLI flags and API fields override per run. The knobs that matter most:

| Var | Default | Meaning |
|---|---|---|
| `KEYWORDS` | `asp.net core c# .net fullstack` | Default search keywords |
| `LOCATIONS` | `pune,hyderabad` | Default search locations |
| `EXPERIENCE` / `DATE_FILTER` | `6` / `7` | Years of experience · posted within last N days |
| `MAX_PAGES_PER_SEARCH` / `MAX_JOBS_TOTAL` | `3` / `60` | Politeness caps |
| `ENRICH_DETAILS` | `true` | Visit each posting page for full text/skills |
| `EMAIL_DOMAINS` | 11 targets (cognizant, capgemini, ltm, …) | LinkedIn post-search domains for `collect-emails` |
| `EMAIL_MAX_SCROLLS` / `EMAIL_DATE_FACET` | `6` / `past-month` | Feed scrolls per domain · LinkedIn date window |
| `DATABASE_URL` | `sqlite:///jobs.db` | SQLite file (or any SQLAlchemy URL) |
| `WEB_HOST` / `WEB_PORT` | `127.0.0.1` / `8000` | Control-plane bind |
| `HEADLESS` | `false` | Background runs (do the first run headful) |

SQLite is the source of truth; every export is a disposable snapshot.

## Architecture

```
Trigger (dashboard / REST / MCP / CLI / scheduler)
         │  one polite pass at a time, cancellable, progress + stage timeline
         ▼
Collect ── fast path: board search API (RSA request token, 20/page)
          fallback: Playwright Chromium + uBO Lite + stealth init JS
         │  polite delays · honeypot-safe extraction · manual-solve walls
         ▼
Validate (Pydantic Job — one contract; bad cards dropped with field name)
         ▼
Filter (relevance gate + stack filter, e.g. pure-Java exclusion)
         ▼
Persist (SQLAlchemy → SQLite: upsert by posting id, first/last seen, run audit)
         ├──► Analyze (skill frequencies with per-company breakdowns)
         ├──► Export (Pandas → CSV / hyperlinked Excel)
         └──► Snapshots (timestamped JSON/CSV/TXT in output/)
```

Key modules: `src/web/` (FastAPI app, routers, orchestrator, MCP tools), `src/naukri_scraper.py` (collection pipeline + filters), `src/web/nkapi.py` (search-API client), `src/models.py` (Pydantic + ORM contract), `src/db.py`, `src/export.py`, `src/parser.py` (offline twin), `src/stealth_browser.py`, `src/scheduler.py`, `src/main.py` (CLI).

## API & MCP sketch

```
POST /api/collect   → 202 {run_id}   collect one search profile into SQLite
POST /api/scrape    → 202 {run_id}   full browser pass (409 when one already runs)
POST /api/skills    → 202 {run_id}   skill-demand scan (report + .txt artifact)
POST /api/exports   → 202 {run_id}   CSV/Excel snapshot
GET  /api/runs/{id} → live progress + events[] + verdict
POST /api/runs/{id}/cancel → cooperative cancel (partials kept)
GET  /api/runs/{id}/download → the finished artifact
GET  /api/health | /api/stats | /api/jobs… | /api/db/tables… | /api/logs…
/mcp                → Streamable HTTP MCP (trailing slash required)
```

Full contract: `docs/WEB_API.md` (kept alongside the code as the living spec).

## Testing

```bash
pytest   # 181 tests, 100% coverage gate — no browser or network needed (fakes included)
```

Live browser/network probes live in `scripts/` (practice suite, e-commerce spot checks) and are separate from the unit gate by design.

## Docs

- `docs/PROJECT.md` — pipeline, modules, config, data model, reference-repo survey
- `docs/WEB_API.md` — control-plane spec (REST + dashboard + MCP + Scalar)
- `docs/LANES_RUNBOOK.md` — reproducible multi-lane collect → Excel recipe
- `docs/CODE_EXPLANATION.md` — code style, patterns, module-by-module guide
- `docs/TESTING.md`, `docs/BOT_DETECTION.md` — practice progression, measurement-first bot-wall notes
- `docs/GRAPHIFY.md` — queryable knowledge graph of the repo (`graphify query "<q>"`)

## Fair use

Collect public listings only, at polite rates, for personal research. Respect each board's Terms of Service and `robots.txt`; never share or sell scraped data, and never run concurrent workers against a site. On a block page: back off and retry later — this tool does not bypass access controls.

## Contributing

Issues and pull requests are welcome. Keep the gates green: `pytest` must stay at 100% coverage, SQLite stays the source of truth, and new collectors should follow the existing extract → validate → filter → persist shape. Please don't commit secrets, browser profiles, or database/output artifacts (all gitignored).
