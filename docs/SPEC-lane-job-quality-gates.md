# Spec: Lane Job-Quality Gates (irrelevant · pure-frontend · external-apply · dedupe)

> Status: **DRAFT — awaiting approval** (spec-driven-development, Phase 1).
> Source of truth for the change; `docs/LANES_RUNBOOK.md` + `docs/WEB_API.md`
> are updated to match once this is approved and implemented.

## Objective

Naukri's `jobapi/v3/search` is fuzzy: lane keyword scans return mixed and
unrelated postings, pure-Java (already gated), pure-frontend roles, near
identical reposts, and postings whose Apply button leaves Naukri for the
**company's own application portal** (which the user does not want to use).

Build four **durable, API-only** quality gates (no Playwright) so that every
lane collect + export produces an accurate, duplicate-free Excel of
applicable-on-Naukri Lane 1 (AI) and Lane 2 (.NET) jobs.

User-facing acceptance:

- Excel contains only jobs matching **at least one** lane anchor (AI or .NET
  full-stack domain) — no Product Owners, Data Engineers, SREs, Identity
  Specialists, Hardware designers pulled in by fuzzy search.
- No pure-frontend postings (React/Angular/HTML/CSS… with no server-side anchor).
- No pure-Java postings (existing gate stays as is).
- No row that redirects off Naukri to a company careers/ATS portal.
- No duplicate posts (same title + company appearing twice under different job ids).
- Titles in the sheet remain true hyperlinks to the Naukri job page.

## Verified external facts (reference-repo based, browser-free)

From `speedyapply/JobSpy` (`jobspy/naukri/__init__.py`, `model.py`,
`constant.py`) plus live probes against Naukri today:

| Fact | Value |
|---|---|
| Search endpoint | `GET /jobapi/v3/search`, headers `appid: 109`, `systemid: Naukri`, per-request `nkparam` (already implemented) |
| Detail endpoint | `GET /jobapi/v4/job/<jobId>`, headers `appid: 121`, `systemid: Naukri`, `nkparam = generate_nkparam(jobId)` — returns `description`, `keySkills`, `applyRedirectUrl`, … |
| `companyApplyJob: true` on a search row | job applies on the **company** side — JobSpy drops these under `easy_apply`; confirmed live: such a job's detail carries `applyRedirectUrl = https://careers.unitedhealthgroup.com/...` |
| `clientCareersUrl` on a search row | client careers URL (external) |
| `applyRedirectUrl` | external apply target (doubleclick-tracked company ATS link) |
| Detail API needs no browser | verified with plain `httpx` (200s above) |

Browser (Playwright) is **explicitly out of scope** for this change at the
user's instruction.

## Tech Stack / Commands

Python 3.10+, Pydantic v2, SQLAlchemy + SQLite (`jobs.db`), Pandas + openpyxl
exports, FastAPI web app, `pytest` with a hard 100 % coverage gate.

```bash
# run the full gate (coverage-fail-under=100 is in pyproject addopts)
cd /Users/aslamshaikh/Projects/PythonWebScraping && python3 -m pytest

# server (once), then collect + export as per docs/LANES_RUNBOOK.md
python3 -m src.main web --port 8000
curl -s -X POST http://127.0.0.1:8000/api/collect  -H 'content-type: application/json' -d '{...}'
curl -s -X POST http://127.0.0.1:8000/api/exports  -H 'content-type: application/json' -d '{"format":"excel","days":1}'
```

## Project Structure (files touched)

```
src/naukri_scraper.py   # new gate functions + regexes (replaces is_relevant)
src/web/nkapi.py        # API-collect: external-apply + unwanted gates
src/export.py           # export gates + dedupe (load_frame / export_jobs)
src/web/schemas.py      # exclude_unwanted: bool = True on Collect + Export
src/web/orchestrator.py # pass exclude_unwanted through both runners
src/main.py             # CLI: --exclude-unwanted/--include-unwanted on export
tests/test_scraper.py   # gate truth tables (new), is_relevant test removed
tests/test_export.py    # dedupe, external-host gate, flag off
tests/test_web.py       # param plumbing (collect + export)
docs/LANES_RUNBOOK.md   # new §1c quality gates, updated params
docs/WEB_API.md         # exclude_unwanted contract lines
```

## Gate definitions (the contract)

Text used by gates 1–2 is **`title` + `skills` + `snippet`** (what both the
API collect and a DB row have — deterministic across collect and export).

### G1 — relevance (kills mixed / unrelated results)

`should_exclude_irrelevant_job(title, skills, snippet) -> bool` is **True**
(no lane anchor found) unless either holds:

1. **any anchor in title or skills** — matches `AI_ANCHOR_RE ∪ DOTNET_LANE_RE`
   - `AI_ANCHOR_RE`: `\bai\b`, `gen ?ai`, `llm`, `large language model`,
     `rag`, `retrieval[- ]augmented`, `langchain`, `langgraph`, `agentic`,
     `multi[- ]agent`, `mcp`, `machine learning`, `\bml\b`, `nlp`,
     `natural language`, `generative`, `deep learning`, `computer vision`,
     `pytorch`, `tensorflow`, `hugging ?face`, `openai`, `chatgpt`,
     `copilot`, `claude`, `prompt engineering`, `vector (db|store|database)`,
     `embedding`
   - `DOTNET_LANE_RE`: existing `DOTNET_ANCHOR_RE` (c#, .net, dotnet, asp.net,
     blazor, entity framework, vb.net) **plus** `full ?stack`, `microservice`,
     `web api`, `restful api`, `rest api`, `\bmvc\b`
2. **a *strong* term in the snippet** — `STRONG_SNIPPET_RE` = `llm`, `rag`,
   `langchain`, `langgraph`, `agentic`, `gen ?ai`, `mcp`, `\.net`, `c#`,
   `asp\.?net`, `dotnet`, `microservice`, `full ?stack`
   (a bare `\bai\b` in prose does **not** qualify — that is the main noise path).

Truth table (unit-tested): `AI Engineer` keep · `Senior .NET Developer` keep ·
`Sr. SW Engineer - Python, AI & Agentic Automation` keep ·
`Product Owner` drop · `Hardware Design Engineer` drop ·
`Data Engineer` (AI only in prose) drop · `UI/UX Designer` drop.

### G2 — pure frontend

`should_exclude_frontend_job(title, skills, snippet) -> bool` is True iff a
frontend signal matches **and** no server-side anchor rescues it:

- `FRONTEND_RE`: `frontend|front[- ]end|react( ?native)?|angular|vue|next\.?js|
  nuxt|svelte|html5?|css3?|javascript|typescript|jquery|bootstrap|tailwind|
  ui[- /]?ux|ux designer|web design|ui developer|storybook|webpack|vite`
- `SERVER_ANCHOR_RE` (rescue): `DOTNET_ANCHOR_RE ∪ {python, node, express,
  django, flask, fastapi, sql, backend, full ?stack, microservice, rest ?api,
  web api, restful, ruby, php, rails, golang}`

So `React Developer` / `React, Redux, HTML, CSS` **drop**, while
`Full Stack Developer (React, .NET)` and `Fullstack JavaScript Engineer`
**stay** (not pure frontend).

### G3 — external apply (company-portal redirect)

- **Collect time (API row):** drop iff `companyApplyJob` truthy **or**
  `clientCareersUrl` truthy **or** `applyRedirectUrl` truthy on the raw search
  row → new `is_external_apply(api_job: dict) -> bool` in `nkapi.py`.
- **Export time (safety net, catches browser-enriched rows):** drop iff
  `apply_url` has a host that is **not** `naukri.com` (empty host/empty value
  = kept — it falls back to the Naukri job URL).

### G4 — duplicates

Always on in `load_frame()`: collapse rows sharing the normalized
`(title.casefold(), company.casefold())` key (whitespace squeezed), keeping the
freshest row (input order is `last_seen DESC`). `job_id` dedupe already exists
at upsert level.

### Flag

`exclude_unwanted: bool = True` on `CollectRequest` and `ExportRequest`
(defaults to on; `"exclude_unwanted": false` restores today's raw pool except
the pre-existing Java gate). Plumbed through `default_collect_runner` /
`default_export_runner` and CLI `export --exclude-unwanted/--include-unwanted`.

- Browser collect (`run_scrape`) applies G1+G2 unconditionally, mirroring how
  the Java gate is already unconditional there; `is_relevant` (the .NET-only
  browser gate) is **removed** — it would silently drop Lane 1 AI postings on
  the fallback path.
- Skills scans (`POST /api/skills` → `api_scan_skills`) pin **both**
  `exclude_unwanted: False` and `exclude_java: False` — exploratory keyword
  scans keep the raw result pool (a Java posting returned for a .NET query
  still contributes honest demand data).

## Code style

Mirrors the existing gate, e.g.:

```python
#: Lane 1 (AI) + Lane 2 (.NET/full-stack) anchors — word-boundary guarded.
AI_ANCHOR_RE = re.compile(r"\bai\b|gen ?ai|\bllm\b|langchain|langgraph|agentic|…", re.I)

def should_exclude_irrelevant_job(title: str = "", skills=(), snippet: str = "") -> bool:
    """True when a posting matches neither lane and must stay out of the Excel."""
    ...
```

Pure functions, module-level compiled regexes, docstrings that state the rule
and the truth table, `log.info("Skipping …: %s", job.title[:70])` on drops.

## Testing Strategy

`pytest` (tests/), offline — no network, no browser.

- `tests/test_scraper.py`: truth-table tests for `should_exclude_irrelevant_job`,
  `should_exclude_frontend_job`, removal of `test_is_relevant`;
  `run_scrape` fake-context tests cover both branches of the new skips.
- `tests/test_web.py`: `api_collect_jobs` drops external-apply rows, honours
  `exclude_unwanted: false`; progress reports the new counters.
- `tests/test_export.py`: dedupe keeps freshest, non-naukri `apply_url` dropped,
  `exclude_unwanted: false` bypass.
- Gate: `python3 -m pytest` must stay at `--cov-fail-under=100`.

## Boundaries

- **Always do:** keep every drop counted + logged, keep `exclude_unwanted`
  opt-out-able, keep tests offline, update `LANES_RUNBOOK.md`/`WEB_API.md`.
- **Ask first:** schema changes to `jobs` (none needed — no migration), new
  dependencies, endpoint/contract renames, raising request rates against Naukri.
- **Never do:** browser/Playwright calls in this flow, CAPTCHA solving,
  relaxing the 100 % coverage gate, weakening the existing Java gate.

## Run plan (after implementation, same session)

1. `python3 -m pytest` → green at 100 %.
2. Start server, `POST /api/collect` Lane 1 then Lane 2 with runbook strings,
   `days: 3`, **`max_jobs: 150`** (the cap counts *kept* rows, so it absorbs
   filter losses), `exclude_unwanted: true`.
3. `POST /api/exports {"format":"excel","days":1,"exclude_unwanted":true}` →
   download → hand over `output/naukri_export_<ts>.xlsx`.
4. Sanity: runs `succeeded`, `source: "api"`, drop counters in the run log
   match expectations (mixed results + portal-redirects actually removed).

## Success Criteria

- [ ] All four gates implemented as pure functions, opt-out flag plumbed end
      to end (API → orchestrator → export → CLI).
- [ ] `python3 -m pytest` passes with 100 % coverage; no new deps.
- [ ] Probe on today's pool: `Product Owner`, `Hardware Design Engineer`,
      `Data Engineer`-style rows drop; AI/.NET rows survive; every row in the
      Excel links to `naukri.com`.
- [ ] Excel has zero duplicate (title, company) pairs.
- [ ] `LANES_RUNBOOK.md` + `WEB_API.md` describe the new gates and params.

## Open Questions

1. Dedupe key `(title, company)` will also collapse genuinely distinct
   openings that share an exact title at one company (e.g. two `Sr. SW
   Engineer` postings differing only by experience band). Acceptable? (default:
   yes — that is what "avoid duplicate posts" means for an apply sheet)
2. `react`/`angular` are Lane 2 **search keywords** but are deliberately not
   relevance anchors — pure-React results are dropped by G2 instead. Confirm
   that is the intent (default: yes).
3. Lane scan volume: `max_jobs: 150` per lane instead of the runbook's 100,
   because gates keep fewer rows per raw page. OK? (default: yes)
