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
GET  /api/runs                   → newest-first list
GET  /api/runs/{id}              → live progress (progress.stage/page/found)
POST /api/runs/{id}/cancel       → cancelling → cancelled (partials kept)
GET  /api/runs/{id}/download     → export file (409 until succeeded, 404 if lost)
GET  /api/health | /api/stats | /api/jobs[?q&location&page&page_size] | /api/jobs/{id}
```

All failures share one envelope: `{"error": {"code": ..., "message": ...}}`
(`422 VALIDATION_ERROR` carries `details`). Run statuses:
`running → cancelling → cancelled | succeeded | failed`.

Rules: one scrape at a time (process lock, second start = 409); cancel is
cooperative (worker polls between pages, partial results upserted); run
history is a 200-entry ring (evicted ids → 404); SQLite stays source of truth.

## Architecture

```
browser UI / REST / MCP  ──→  FastAPI (src/web/app.py)
                                   ├── data.py ......... reads: jobs/stats (SQLite)
                                   ├── orchestrator.py . runs: threads + cancel events + lock
                                   │     ├── default_scrape_runner (browser→DB→files, lazy imports)
                                   │     └── default_export_runner (snapshot → file)
                                   ├── mcp_tools.py .... 5 curated tools (not auto-converted)
                                   └── templates/dashboard.html (Tailwind v4 + IBM Plex Mono)
```

`run_scrape()` gained two optional hooks (`should_stop`, `on_progress`;
CLI passes neither — behavior unchanged). Defaults resolve from `SETTINGS`;
per-run overrides are restored in `finally`.

## UI

Single self-contained `dashboard.html`: Tailwind v4 browser CDN + IBM Plex
Mono everywhere, zinc/emerald dev-console look (flat, no gradients, dense
tables). Works without the CDN too (inline `<style>` fallback). Polls run
state every 3s; charts are CSS bars from `/api/stats`.

## MCP tools (curated)

`collector_stats`, `search_jobs(query, location, page_size)`,
`start_scrape(keywords, locations)`, `run_status(run_id)`,
`cancel_run(run_id)`. Errors return `{"error": ...}` dicts (never raise).

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

- `pytest`: **120 passed, 100% coverage** (gate `--cov-fail-under=100` green).
- Live boot on `:8123` against the real `jobs.db` (45 jobs): health/stats/
  dashboard/scalar all 200; export run `export-0001` → succeeded → download
  200; cancel-after-finish → `409 RUN_NOT_CANCELLABLE`; jobs search returned
  real TCS listing. Cancel-mid-run proven in tests with blocking runners.
