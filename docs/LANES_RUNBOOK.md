# Daily Lanes Runbook — fresh apply-links Excel, every morning

> Goal: one Excel file with clickable job titles covering the last 3 days
> across both lanes, reproducible daily in ~5 minutes (plus unattended run
> time). Generated 2026-10-15 as `output/naukri_export_20261015_235310.xlsx`
> (246 rows, 246 hyperlinked titles) — this doc records exactly how, so
> tomorrow's file is produced the same way.

## 0. Start the server (once per day)

```bash
cd /Users/aslamshaikh/Projects/PythonWebScraping
python3 -m src.main web --port 8000
# dashboard: http://127.0.0.1:8000  ·  API tester: http://127.0.0.1:8000/scalar
```

## 1. The two lanes (exact criteria — do not improvise)

| | Lane 1 — AI | Lane 2 — .NET |
|---|---|---|
| `keywords` | `AI Engineer, AI Agent Developer, LangChain, LangGraph, GenAI Engineer, LLM, RAG, Agentic AI, Python AI Engineer, MCP` | `Senior .NET Developer, ASP.NET Core, Web API, C#, Full Stack .NET Developer, React, Angular, Microservices` |
| `location` | `pune,hyderabad,bengaluru` | `pune,hyderabad,bengaluru` |
| `experience` | `6` | `6` |
| `days` | `3` (jobAge freshness filter) | `3` |
| `max_jobs` | `100` | `100` |

Why these strings: Lane 1 mirrors the current Senior Software Engineer
(AI/CCaaS, LangGraph/MCP) role; Lane 2 mirrors the 6-yr .NET full-stack
history. Scanned 2026-10-15, they overlapped ~90% — both lanes swim in one
pool, so one combined file is correct (no per-lane split needed).

## 2. Collect (API path, ~25s per lane, no browser)

Run **sequentially** (one browser/API lock; the second `POST` while busy
returns 409 — just wait and retry). Expect `source: "api"` in each summary;
if a run reports `source: "browser"`, the API rate-limited (406) and the
run still completed via fallback — file is still valid.

```bash
# Lane 1
curl -s -X POST http://127.0.0.1:8000/api/collect \
  -H 'content-type: application/json' \
  -d '{"keywords":"AI Engineer, AI Agent Developer, LangChain, LangGraph, GenAI Engineer, LLM, RAG, Agentic AI, Python AI Engineer, MCP","location":"pune,hyderabad,bengaluru","experience":6,"days":3,"max_jobs":100}'
# → {"run_id":"collect-NNNN", ...} — poll until succeeded:
curl -s http://127.0.0.1:8000/api/runs/collect-NNNN
# Lane 2 (same shape, .NET keywords above)
```

Dashboard equivalent: **collect lane** card → paste titles → locations
`pune,hyderabad,bengaluru` → exp 6 → days 3 → max 100 → collect → wait for
`succeeded` in the runs table. MCP equivalent: `collect_lane` tool, twice.

What "collect" does: direct `jobapi/v3/search` (20/page, `nkparam` auth,
3–7s polite pacing) → Pydantic validation → upsert into `jobs.db` by
`job_id` (re-runs only add *new* postings; `found` vs `new` in the summary
tells you the split) + audit row in `scrape_runs` + per-run timestamped
log in `logs/`.

## 3. Export the Excel (titles are real hyperlinks)

```bash
curl -s -X POST http://127.0.0.1:8000/api/exports \
  -H 'content-type: application/json' -d '{"format":"excel"}'
# poll the run, then:
curl -s -OJ http://127.0.0.1:8000/api/runs/export-NNNN/download
# file lands in output/naukri_export_<ts>.xlsx
```

Dashboard equivalent: **export** card → format `excel` → start → download
link when done. Open in Excel/LibreOffice: the **title column cells are
true hyperlinks** (blue, underlined) pointing at each posting's apply URL —
click a title, apply on the job page. (CSV exports keep plain URL text,
which Excel auto-linkifies on open.)

## 4. Sanity checks (2 minutes)

- Runs table: both collects `succeeded`, `source: "api"`, `found ≈ 100`
  each; export `succeeded` with a `.xlsx` file.
- `GET /api/stats`: `total_jobs` grows only by genuinely new postings.
- Anything odd → open the run's **log** link (runs table / logs card):
  every API request, fallback reason, and per-page count is timestamped.
- 406 rate-limit (back-to-back runs): wait a few minutes, re-run the lane —
  the 3–7s pacing normally prevents it.

## 5. Changing the recipe

- Different freshness: `days: 7` (weekly sweep) or `days: 1` (daily top-up).
- More volume: `max_jobs` up to `200` per lane.
- New lane: add a third `POST /api/collect` with its own titles — no code
  changes needed. If a lane becomes permanent, tell me and I'll pin it in
  this doc (and optionally as a scheduled job).
