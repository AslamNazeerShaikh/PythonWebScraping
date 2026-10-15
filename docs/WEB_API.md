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

## Key-skills scan

`POST /api/skills {keywords (comma titles), location, experience, days,
pages, max_jobs (default 100, cap 200)}` starts a `skills` run: one search
per title (freshness-filtered via `jobPostDate`), detail enrichment for key
skills (no relevance filter — the titles are the query), then a frequency
report (top 30, one vote per posting, case-folded). Analysis-only: postings
are NOT upserted to SQLite; the report + `skills_<ts>.txt` (same shape as
the export download) is the artifact, with `verdict` + `duration_s` in the
summary. Dashboard renders top-5 chips + ranked bars (top 10 numbered) +
meta + .txt link. Shares the single browser lock (409 when busy) and the
cancel twin. Sort order inside Naukri pages is Naukri's own; the freshness
window (`days`) is what keeps the pool recent.

## MCP tools (curated) + harness wiring

`collector_stats`, `search_jobs(query, location, page_size)`,
`start_scrape(keywords, locations)`, `start_skill_scan(keywords, location,
max_jobs)`, `run_status(run_id)`, `cancel_run(run_id)`. Errors return
`{"error": ...}` dicts (never raise).

The agent harness talks to the **running** server: `.opencode/opencode.json`
declares `mcp.servers["naukri-collector"]` → `http://127.0.0.1:8000/mcp/`
(Streamable HTTP; trailing slash is required — the mount answers the
canonical path and plain `/mcp` only 307-redirects, which strict MCP
clients do not follow). Start the server first (`python -m src.main web`),
then restart the harness session so it reconnects; verify with
`opencode mcp debug naukri-collector`.

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

- `pytest`: **127 passed, 100% coverage** (gate `--cov-fail-under=100` green).
- Live boot on `:8123` against the real `jobs.db` (45 jobs): health/stats/
  dashboard/scalar all 200; export run `export-0001` → succeeded → download
  200; cancel-after-finish → `409 RUN_NOT_CANCELLABLE`; jobs search returned
  real TCS listing. Cancel-mid-run proven in tests with blocking runners.
- Restructure verified: `uvicorn src.web.main:app` boots; routers resolve
  every route; `[tool.fastapi] entrypoint` declared per the guide; MCP tools
  reachable over HTTP `/mcp` by the harness config.
