# Web Control Plane — Spec + Guide

> One process, one port: the Python backend is the brain (orchestration, data,
> visualization, import/export); Playwright is only the hands (opens pages when
> a scrape run tells it to). No more CLI-fumbling to run anything: start the
> server once, then trigger or cancel every action from the dashboard, REST,
> or MCP.

Per the `spec-driven-development` skill this file is the spec (kept alive
alongside the code in `src/web/`). Built in thin slices per
`incremental-implementation`; contracts first per `api-and-interface-design`;
UI per `frontend-ui-engineering`. Gates were compressed on your explicit
"just implement it" instruction — the evidence section below is the proof.

## Objective

Run `python -m src.main web` (default `127.0.0.1:8000`, see `WEB_HOST` /
`WEB_PORT` in `.env.example`). Then:

| Surface | URL | Purpose |
|---|---|---|
| Dashboard | `GET /` | KPIs, scrape/export forms, live run + cancel, runs table, charts, jobs browser |
| Scalar API tester | `GET /scalar` | Try every endpoint in-browser |
| Swagger / OpenAPI | `GET /docs`, `GET /openapi.json` | Machine-readable contract |
| REST | `POST/GET /api/...` | Scriptable triggers + cancels |
| MCP (Streamable HTTP) | `/mcp` | 5 curated tools for LLM clients |

## Contract (every action has a cancel twin)

```
POST /api/scrape                 → 202 {run_id,...}   409 SCRAPE_ALREADY_RUNNING
POST /api/exports                → 202 {run_id,...}
POST /api/skills                 → 202 {run_id,...}   409 when a browser run is busy
GET  /api/runs                   → newest-first list
GET  /api/runs/{id}              → live progress + events[] stage timeline + verdict
POST /api/runs/{id}/cancel       → cancelling → cancelled (partials kept)
GET  /api/runs/{id}/download     → export file (409 until succeeded, 404 if lost)
GET  /api/health | /api/stats | /api/jobs[?q&location&page&page_size] | /api/jobs/{id}
GET  /api/db/tables | /api/db/tables/{name}[?page&page_size] → browse SQLite in the UI
GET  /api/logs | /api/logs/{name}[?max_lines]               → per-run timestamped logs
```

All failures share one envelope: `{"error": {"code": ..., "message": ...}}`
(`422 VALIDATION_ERROR` carries `details`). Run statuses:
`running → cancelling → cancelled | succeeded | failed`.

Rules: one scrape at a time (process lock, second start = 409); cancel is
cooperative (worker polls between pages, partial results upserted); run
history is a 200-entry ring (evicted ids → 404); SQLite stays source of truth.

## Architecture (FastAPI bigger-applications shape)

Per https://fastapi.tiangolo.com/tutorial/bigger-applications/ —
`APIRouter(prefix, tags)`, shared `dependencies`, `internal/` mounted with
prefix/tags at include time, `[tool.fastapi] entrypoint` in `pyproject.toml`:

```
src/web/
    main.py            ← FastAPI app + include_router + mounts + GET / (uvicorn src.web.main:app)
    dependencies.py    ← get_orchestrator (app.state; override via dependency_overrides)
    routers/jobs.py    ← APIRouter(prefix="/api/jobs", tags=["jobs"])
    routers/runs.py    ← APIRouter(prefix="/api", tags=["runs"])
    internal/ops.py    ← no prefix inside; included with prefix="/api", tags=["ops"]
    schemas.py         ← Pydantic contracts (RunOut now carries events[])
    crud.py            ← SQLite reads + stats + DB explorer (renamed from data.py)
    orchestrator.py    ← run threads, cancel events, stage timeline, verdicts
    runlog.py          ← per-run timestamped log files (python + playwright)
    mcp_tools.py       ← 5 curated MCP tools
    templates/dashboard.html
```

Deliberately NOT added (YAGNI): token auth (personal local tool), DuckDB
second store (SQLite is already serverless/engineless), global overdue
dependencies.

`run_scrape()` gained two optional hooks (`should_stop`, `on_progress`;
CLI passes neither — behavior unchanged). Defaults resolve from `SETTINGS`;
per-run overrides are restored in `finally`.

## UI

Single self-contained `dashboard.html`: Tailwind v4 browser CDN + IBM Plex
Mono everywhere, zinc/emerald dev-console look (flat, no gradients, dense
tables). Works without the CDN too (inline `<style>` fallback). Polls run
state every 3s; charts are CSS bars from `/api/stats`. Live run panel shows
counters (found / steps / elapsed), the `events[]` stage timeline, and a
final **verdict** card (`"3 new of 12 collected across 2 location(s) in
41.2s"` + duration + link to the run's log file). Separate cards browse the
SQLite tables and tail per-run logs.

## Run logs

Every run writes `logs/<kind>_<run-id>_YYYYMMDD_HHMMSS.log`
(`LOG_DIR`, default `logs/`, gitignored): root logger (all Python code) +
`playwright` logger at INFO, line shape
`2026-10-15 19:02:11 INFO     src.web.orchestrator: message`. Console output
unchanged. Browse via dashboard or `GET /api/logs[/{name}]`.

## Key-skills scan (API fast path + browser fallback)

> Deep dive (DOM, pagination bug, verification snapshot):
> [`docs/SPEC-naukri-skills-scan.md`](SPEC-naukri-skills-scan.md).

`POST /api/skills` first tries Naukri's own search API — the JobSpy-port
(`src/web/nkapi.py`): `GET jobapi/v3/search` with `appid: 109` and a fresh
per-request RSA `nkparam` (`v0|<ms>|121_srp`, stdlib-only port of
JobSpy's generator; HAR-captured tokens are time-bound and never replayed).
Freshness-first (`jobAge` + `sort=f`), 20 rows/page, `tagsAndSkills` split
per row through the same Pydantic gate. `406` (rate-limit/rotated key) or
any network failure falls back to the polite browser scan; the summary
stamps `"source": "api"|"browser"` so you can see which path served.

`POST /api/skills {keywords (comma titles), location, experience, days,
pages (cap 30), max_jobs (default 100, cap 600), count_mode}` — `companies`
(default): each skill counts DISTINCT companies (`C#` in 20 Capgemini +
10 TCS postings scores 2, over `companies_total`); `postings` keeps the
legacy one-vote-per-posting count. The dashboard switch defaults ON.
Both `exclude_unwanted` and `exclude_java` are pinned `False`: a skills scan
is exploratory, and the raw result pool is the point.
Page 1 is loaded from the slug URL
(`/<keyword-slug>-jobs-in-<first-city>?k=&l=&experience=&jobAge=`). For a
multi-city `location`, the full comma list goes in `l` while the path uses
only the first city — exactly the URL Naukri itself generates. Putting the
whole list in the path (`...-jobs-in-pune, hyderabad, bangalore-2`) makes
Naukri redirect to page 1 and strip every filter; that was the old
"pagination keeps reloading page 1" bug. Pages 2+ are reached by clicking
the native **Next** control (`nav[aria-label="Pagination"]`), which keeps
the SPA's experience/jobAge/multi-city state. A direct `...-2` load keeps
the page number but loses those filters (verified live: 68 Pune-only rows
instead of 442), so the browser scan never `goto()`s a `-N` URL.
`?page=2` on a slug URL is likewise ignored by Naukri.
Key skills come from each card's `ul.tags-gt > li.tag-li` chips (promoted
cards use `.keyskill > span`), so no detail-page visits are needed — 438
cards cost 22 page loads, not 438 job-page loads. This is the same list the
search API returns as `tagsAndSkills`; the standard card also exposes
`span.job-post-day` for freshness. The frequency report is top 30, one vote
per posting, case-folded. Every skill carries a company breakdown
(`companies: [{name, count}]`, count desc) so a skill repeated by 4–5
prolific hirers reads honestly — shown as tags under each bar (top 5 +
"+N more") and as `@ Company xN` lines in the .txt.
Analysis-only: postings are NOT upserted to SQLite; the report + `skills_<ts>.txt` (same shape as
the export download) is the artifact, with `verdict` + `duration_s` in the
summary. Dashboard renders top-5 chips + ranked bars (top 10 numbered) +
meta + .txt link. Shares the single browser lock (409 when busy) and the
cancel twin. Sort order inside Naukri pages is Naukri's own; the freshness
window (`days`) is what keeps the pool recent.

## Lane collection → Excel with hyperlinks

`POST /api/collect {keywords, location, experience, days (default 3),
max_jobs}` fetches a lane straight from the search API (JobSpy-clone:
`nkparam` + `tagsAndSkills`, no browser) and upserts into SQLite, with the
browser scrape as fallback. Both `POST /api/collect` and
`POST /api/exports {format: excel}` take `exclude_java` (default `true`):
pure-Java postings (Java/Spring/Selenium/… signal, no `c#/.NET` anchor —
see `should_exclude_java_job` in `src/naukri_scraper.py`) are skipped at
collect time and gated again at export time.

Both endpoints also take **`exclude_unwanted`** (default `true`) — the lane
quality gates (spec: `docs/SPEC-lane-job-quality-gates.md`, runbook §1c):
irrelevant postings (no Lane-1 AI / Lane-2 `.NET` anchor —
`should_exclude_irrelevant_job`), pure-frontend roles
(`should_exclude_frontend_job`), and postings that apply on the **company's
own portal** (`is_external_apply` in `src/web/nkapi.py`: `companyApplyJob` /
`clientCareersUrl` / `applyRedirectUrl` on the search row; export re-checks
that `apply_url` stays on `naukri.com`). Collect progress reports the drop
counts as `excluded` (irrelevant/frontend/Java) and `external`
(company-portal). Exports additionally always collapse near-identical
reposts sharing `(title, company, location, experience)` — freshest wins.
`{"exclude_unwanted": false}` restores the raw pool (the Java gate stays on);
CLI mirrors it as `export --exclude-unwanted/--include-unwanted`. Skills
scans pin the gates **off** — exploratory keyword scans keep the raw pool.

`POST /api/exports` also takes an optional `days` (integer, `>0`, omit for
the whole DB): only rows whose `first_seen` falls inside the last N days are
written, so `days: 1` is exactly the "posted in the last 24h" slice. The
cutoff is computed in **UTC** (`fresh_cutoff()` in `src/export.py`) because
`first_seen` comes from SQLite's `CURRENT_TIMESTAMP` — a local-time cutoff
would shrink the window by the machine's UTC offset. CLI mirrors it:
`python3 -m src.main export --format excel --days 1`.

`location` is interpreted through `location_match` (default `contains`):
substring matching, so `"pune"` also passes the combined
`"pune,hyderabad,bengaluru"` `search_location` written by a multi-city
search. Send `location_match: "exact"` for a city-pure sheet — equality
against the job's own `location` **or** its `search_location`, case- and
whitespace-insensitive (`^(contains|exact)$`, 422 otherwise; CLI
`--location-match exact`). Exact matters because API-collected rows leave
the job's `location` blank — `search_location` is the only city signal, and
`pune` alone would smuggle in 3-city results.

Then `POST /api/exports {format: excel}` writes
a snapshot whose title cells are true clickable hyperlinks (openpyxl
`Hyperlink` → apply URL); CSV keeps plain URL text (Excel auto-linkifies).
Flow for apply-links day: collect lane 1 + lane 2 → one excel export →
open, click titles, apply. For a last-24h-only file, send `days: 1` to
**both** the collect and the export.

## MCP tools (curated) + optional harness wiring

`collector_stats`, `search_jobs(query, location, page_size)`,
`start_scrape(keywords, locations)`, `start_skill_scan(keywords, location,
max_jobs)`, `collect_lane(keywords, location, days)`, `run_status(run_id)`,
`cancel_run(run_id)`. Errors return `{"error": ...}` dicts (never raise).

The server still serves MCP at `/mcp`, but the harness **no longer wires
it**: `.opencode/opencode.json` previously declared
`mcp.servers["naukri-collector"]` → `http://127.0.0.1:8000/mcp/`, and that
entry was removed — day-to-day collection goes through the REST/CLI paths
above. To re-wire any harness, start the server first
(`python -m src.main web`), declare a remote MCP server pointing at
`http://127.0.0.1:8000/mcp/` (Streamable HTTP; trailing slash is required —
the mount answers the canonical path and plain `/mcp` only 307-redirects,
which strict MCP clients do not follow), restart the harness session so it
connects, and verify with `opencode mcp debug <server-name>`.

## Boundaries

- Always: 100% coverage gate holds (`pytest`); polite caps unchanged.
- Ask first: new endpoints, scheduler-in-web, auth.
- Never: auto-solve CAPTCHAs (manual-solve pause preserved), commit secrets,
  expose runs across restarts (history is in-memory by design).

## Sources (source-driven-development)

- Scalar FastAPI: https://scalar.com/products/api-references/integrations/fastapi
  (`add_scalar_reference(app)` → `/scalar`).
- FastMCP FastAPI: https://gofastmcp.com/integrations/fastapi (`http_app`,
  `lifespan` passthrough, `mount`; curated-tools-over-auto-convert tip).
- agent-skills: https://github.com/addyosmani/agent-skills (`spec-driven-development`,
  `api-and-interface-design`, `frontend-ui-engineering`,
  `incremental-implementation`, `source-driven-development`).
- UNVERIFIED (fetch blocked, graceful fallback shipped): Tailwind v4 browser
  CDN snippet; ui-skills MCP docs page (JS shell only — UI follows the
  frontend-ui-engineering skill instead).

## Evidence (verify-before-claim)

- `pytest`: **336 passed, 100% coverage** (gate `--cov-fail-under=100` green).
- Live boot on `:8123` against the real `jobs.db` (45 jobs): health/stats/
  dashboard/scalar all 200; export run `export-0001` → succeeded → download
  200; cancel-after-finish → `409 RUN_NOT_CANCELLABLE`; jobs search returned
  real TCS listing. Cancel-mid-run proven in tests with blocking runners.
- Restructure verified: `uvicorn src.web.main:app` boots; routers resolve
  every route; `[tool.fastapi] entrypoint` declared per the guide; MCP tools
  reachable over HTTP `/mcp` via the FastMCP Streamable-HTTP mount.
