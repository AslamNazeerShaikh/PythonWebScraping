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
| `max_jobs` | `150` (post-gate cap counts *kept* rows — §1c) | `150` |

Why these strings: Lane 1 mirrors the current Senior Software Engineer
(AI/CCaaS, LangGraph/MCP) role; Lane 2 mirrors the 6-yr .NET full-stack
history. Scanned 2026-10-15, they overlapped ~90% — both lanes swim in one
pool, so one combined file is correct (no per-lane split needed).

## 1b. Pure-Java exclusion (always on)

Naukri's search is fuzzy: both lanes pull Java/Spring/Selenium postings.
Every collect and every export now drops **pure-Java** jobs by default
(`exclude_java: true` on `POST /api/collect` and `POST /api/exports`;
`--exclude-java/--include-java` on the `export` CLI):

- **Exclude** iff a Java-stack signal appears in the title, key skills,
  snippet, or description — `java` (never `javascript`), `spring( boot)`,
  `hibernate`, `selenium`, `gradle`, `maven`, `kotlin`, `groovy`, `scala`,
  `jsp`, `servlet`, `struts`, `j2ee/j2se`, `junit`, `testng`, `micronaut`,
  `quarkus` — **and** no `.NET` anchor is present.
- **Keep** when a `.NET` anchor co-occurs (`c#`, `.net`, `dotnet`,
  `asp.net`, `blazor`, `entity framework`, `vb.net`) — so `java + .NET`,
  `AI + C#`, and `Selenium + C#` test roles stay, while `AI + Java`
  (no .NET) and pure-Java go.
- `React` / `Angular` / `Microservices` are deliberately **not** anchors
  (they appear in pure-Java postings too).

Implementation: `should_exclude_java_job()` in `src/naukri_scraper.py`
(ports the title keyword/blocklist idea from
ankitbaghel01/naukri_update's auto-apply runner) — applied at API-collect
time, at browser-collect time (pre- and post-enrichment), and as a final
gate at export time (so older DB rows are filtered from the Excel too).
2026-10-16 proof: Lane 1 excluded 17, Lane 2 excluded 83 at collect;
the Excel carried 325 of 371 DB rows with **0** pure-Java leaks.
Opt out per-run with `"exclude_java": false` if you ever want the raw pool.

## 1c. Lane-quality gates (always on — irrelevant / frontend / portal / dupes)

Naukri's fuzzy search also returns mixed postings unrelated to either lane
(Product Owners, Data Engineers, SREs…), pure-frontend roles, near-identical
reposts, and postings whose **Apply hands you off to the company's own
portal** instead of applying on Naukri. Four gates keep them out (spec:
`docs/SPEC-lane-job-quality-gates.md`; text basis = title + key skills +
snippet, so collect-time and export-time always agree):

1. **Relevance** — `should_exclude_irrelevant_job()`: keep only if a lane
   anchor (Lane 1 `ai/genai/llm/rag/langchain/langgraph/agentic/mcp/ml/nlp/
   pytorch/openai/…` ∪ Lane 2 `c#/.net/asp.net/full stack/microservices/
   web api/mvc`) matches in title/skills, **or** a strong term (`llm`, `rag`,
   `langchain`, `.net`, `c#`, `microservices`, …) appears in the snippet — a
   bare "ai" in prose does NOT count (that is the main noise path).
2. **Pure frontend** — `should_exclude_frontend_job()`: drop when a frontend
   signal (react/angular/vue/html/css/javascript/typescript/ui-ux/…) appears
   with **no** server-side anchor (.NET/python/node/api/full stack/…).
   React/Angular stay Lane-2 *search keywords* but are not relevance
   anchors, so React-only postings die here.
3. **Company-portal redirects** — `is_external_apply()` in `src/web/nkapi.py`:
   drop search rows carrying `companyApplyJob` / `clientCareersUrl` /
   `applyRedirectUrl` (JobSpy uses the same flag for `easy_apply`; verified
   live — such a row's `applyRedirectUrl` points at e.g.
   `careers.<company>.com`). Export re-checks that `apply_url` stays on
   `naukri.com`, so browser-enriched external links cannot leak either.
4. **Duplicates** — always on at export: rows sharing
   `(title, company, location, experience)` collapse (freshest wins);
   `job_id` dedupe already covers upserts.

Gates are governed by **`exclude_unwanted`** (default `true`) on
`POST /api/collect` and `POST /api/exports` (`--exclude-unwanted` /
`--include-unwanted` on the CLI) — opt out per-run with
`"exclude_unwanted": false`; the Java gate stays on regardless. Collect
progress reports drops as `excluded` (irrelevant/frontend/Java) and
`external` (company-portal). Skills scans pin **both** the lane-quality gates
and the Java gate **off** (the raw pool is the point; card key-skill chips are
read directly, so a skills scan never enrich-visits a job page). Because gates keep fewer rows per raw page, the daily
apply-links run collects with `max_jobs: 150` per lane (the cap counts
*kept* rows). 2026-10-21: full suite green at 100 % coverage (202 tests).

## 2. Collect (API path, ~25s per lane, no browser)

Run **sequentially** (one browser/API lock; the second `POST` while busy
returns 409 — just wait and retry). Expect `source: "api"` in each summary;
if a run reports `source: "browser"`, the API rate-limited (406) and the
run still completed via fallback — file is still valid.

```bash
# Lane 1 (add "exclude_unwanted":false only if you ever want the raw pool)
curl -s -X POST http://127.0.0.1:8000/api/collect \
  -H 'content-type: application/json' \
  -d '{"keywords":"AI Engineer, AI Agent Developer, LangChain, LangGraph, GenAI Engineer, LLM, RAG, Agentic AI, Python AI Engineer, MCP","location":"pune,hyderabad,bengaluru","experience":6,"days":3,"max_jobs":150}'
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

Add `"days":1` to the body for a **last-24-hours-only** file (it filters the
export on `first_seen`, so older DB rows never reach the sheet — the collect
`days` alone does NOT filter the export):

```bash
curl -s -X POST http://127.0.0.1:8000/api/exports \
  -H 'content-type: application/json' -d '{"format":"excel","days":1}'
# poll the run, then:
curl -s -OJ http://127.0.0.1:8000/api/runs/export-NNNN/download
# file lands in output/naukri_export_<ts>.xlsx
```

The §1b/§1c gates (`exclude_java`, `exclude_unwanted` — both default `true`)
plus the repost collapse run inside every export, so the sheet carries only
applicable-on-Naukri lane jobs.

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
- Last-24h-only sheet: send `days: 1` to **both** the collect and the export
  (`{"format":"excel","days":1}`) — the collect sets Naukri's `jobAge`, the
  export is what actually filters the rows written to the file.
- City-pure sheet: `{"format":"excel","days":3,"location":"pune","location_match":"exact"}`.
  Without `location_match` the `location` value is a **substring** match, so
  `"pune"` also matches an earlier `pune,hyderabad,bengaluru` search —
  API-collected rows have a blank job `location`, so `search_location` is
  the only city signal.
- More volume: `max_jobs` up to `200` per lane.
- New lane: add a third `POST /api/collect` with its own titles — no code
  changes needed. If a lane becomes permanent, tell me and I'll pin it in
  this doc (and optionally as a scheduled job).
