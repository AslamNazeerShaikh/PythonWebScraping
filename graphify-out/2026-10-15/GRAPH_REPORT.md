# Graph Report - PythonWebScraping  (2026-10-15)

## Corpus Check
- 102 files · ~124,736 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1735 nodes · 2724 edges · 96 communities (88 shown, 6 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 81 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1b2aa103`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- handle_possible_block
- Job
- FakePage
- Page
- src/main.py
- test_parser.py
- test_main.py
- config.py
- test_web.py
- LinkedIn Jobs Expansion — Deep Research
- crud.py
- export_jobs
- orchestrator.py
- do_scrape
- Project Document — Secure Naukri.com Jobs Collector
- Secure Naukri.com Jobs Collector
- ops.py
- Bot-Detection Test Guide — measure exposure, don't chase “Human”
- RunOut
- Hardening Controls
- upsert_jobs
- RunRecord
- What You Must Do When Invoked
- agent-skills
- runs.py
- Web Control Plane — Spec + Guide
- Orchestrator
- Agent Skills (OpenCode)
- nkapi.py
- OpenCode Setup (v2) — plugins, skills, MCP servers
- Worked example: Agent Teams for competing-hypothesis debugging
- web/__init__.py
- Code Review and Quality
- Test-Driven Development
- Context Engineering
- Performance Checklist
- Git Workflow and Versioning
- Optimization Patterns
- Shipping and Launch
- API and Interface Design
- Browser Testing with DevTools
- Frontend UI Engineering
- schemas.py
- CI/CD and Automation
- Constraint-Driven Development
- Deprecation and Migration
- raw_card
- Documentation and ADRs
- Incremental Implementation
- FakeContext
- Code Simplification
- Debugging and Error Recovery
- db.py
- _FakeSched
- Interview Me
- Planning and Task Breakdown
- setup_logging
- Security Checklist
- ReOrder: Keep Your Regulars Ordering Direct
- Idea Refine
- launch_context
- Accessibility Checklist
- Doubt-Driven Development
- Process
- Using Agent Skills
- ._squeeze
- Testing Patterns Reference (JavaScript/TypeScript)
- Spec-Driven Development
- Source-Driven Development
- Testing Guide — practice progression + automated suite
- Refinement & Evaluation Criteria
- The Standing Checklist
- Observability Checklist
- Ideation Frameworks Reference
- Full Code Explanation — Secure Naukri.com Jobs Collector
- build_mcp
- test_scraper.py
- default_scrape_runner
- 7. Module-by-module explanation
- graphify reference: extra exports and benchmark
- idea-refine.sh
- Graphify — queryable knowledge graph of this repo
- 9. Mermaid diagrams (detail)
- 9. External repo survey (5 repos, verified Oct 2026)
- 5. Architecture patterns
- graphify reference: query, path, explain
- naukri_scraper.py
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify.js
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- extraction-spec.md

## God Nodes (most connected - your core abstractions)
1. `FakePage` - 62 edges
2. `Orchestrator` - 51 edges
3. `Job` - 42 edges
4. `FakeContext` - 37 edges
5. `RunRecord` - 35 edges
6. `make_job()` - 31 edges
7. `upsert_jobs()` - 29 edges
8. `run_skills_scan()` - 24 edges
9. `raw_card()` - 23 edges
10. `run_scrape()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `test_get_returns_default_when_unset()` --calls--> `_get()`  [EXTRACTED]
  tests/test_config.py → src/config.py
- `test_get_strips_whitespace()` --calls--> `_get()`  [EXTRACTED]
  tests/test_config.py → src/config.py
- `test_get_engine_caches_singleton()` --calls--> `get_engine()`  [EXTRACTED]
  tests/test_db.py → src/db.py
- `test_coerce_job_valid_and_dropped()` --uses--> `Job`  [INFERRED]
  tests/test_scraper.py → src/models.py
- `test_human_pause_zero_is_instant()` --calls--> `human_pause()`  [EXTRACTED]
  tests/test_stealth.py → src/stealth_browser.py

## Import Cycles
- None detected.

## Communities (96 total, 6 thin omitted)

### Community 0 - "handle_possible_block"
Cohesion: 0.13
Nodes (11): check_bot_wall(), handle_possible_block(), True only on *visible* block pages (not raw HTML, avoids false positives)., Pause for MANUAL bot-wall solving when one is detected (never bypass). No-op on…, human_pause(), Sleep a random politeness interval (defaults: SETTINGS min/max delay).…, test_check_bot_wall_clean_and_blocked(), test_check_bot_wall_evaluate_failure_is_safe() (+3 more)

### Community 1 - "Job"
Cohesion: 0.18
Nodes (16): Job, JobRow, BaseModel, Build a new ORM row from a validated :class:`Job`., Convert a DB row back into a validated :class:`Job`., One validated job record. Attributes: job_id: Stable Naukri numeric id parsed…, Return skills as a single comma-joined string (DB column shape)., ``jobs`` table: one row per unique Naukri job id. ``first_seen``/``last_seen``… (+8 more)

### Community 2 - "FakePage"
Cohesion: 0.09
Nodes (24): BrowserContext, ProgressHook, StopHook, Drive Naukri's search bar like a human; return the landed results URL. Fills…, Scan detail pages for key skills: one search → enriched → report. The full…, run_skills_scan(), submit_searchbar(), FakePage (+16 more)

### Community 3 - "Page"
Cohesion: 0.14
Nodes (17): Page, extract_listing_cards(), _first_match(), human_scroll(), _pick_option(), Mimic human reading: mouse-wheel scrolls + small pauses + mouse wiggle.…, Load ONE search page and return raw (pre-Pydantic) job-card dicts. Flow:…, Extract job cards from the CURRENT page (no navigation). Used after search-bar… (+9 more)

### Community 4 - "src/main.py"
Cohesion: 0.11
Nodes (26): command, rich_console, rich_table, shutil, _ensure_env(), export(), parse(), _print_jobs() (+18 more)

### Community 5 - "test_parser.py"
Cohesion: 0.12
Nodes (27): bs4, bs4_element, re, _card_text(), _is_trap(), parse_detail_html(), parse_search_html(), Layer 2 (extraction, offline twin): BeautifulSoup + lxml over saved HTML.… (+19 more)

### Community 6 - "test_main.py"
Cohesion: 0.12
Nodes (7): _FakePW, Tests for src.main — startup setup, pipeline wiring, all 5 commands., sync_playwright() stand-in (context manager yielding a fake handle)., test_do_scrape_empty_returns_zero(), test_do_scrape_found_persists_and_snapshots(), _wire_pipeline(), typer_testing

### Community 7 - "config.py"
Cohesion: 0.10
Nodes (19): dataclasses, dotenv, os, _get_bool(), _get_float(), _get_int(), Central configuration — every tunable lives here, loaded from `.env`.…, Return env var ``name`` parsed as :class:`int`, else ``default``. (+11 more)

### Community 8 - "test_web.py"
Cohesion: 0.09
Nodes (15): asyncio, fastapi_testclient, default_export_runner(), Snapshot export in the worker thread (fast op, still tracked)., _isolated_logs(), _payload(), fixture, Tests for src.web — orchestrator, REST, dashboard, Scalar, MCP tools. Strategy… (+7 more)

### Community 9 - "LinkedIn Jobs Expansion — Deep Research"
Cohesion: 0.12
Nodes (16): 10. Fair-use note (extends README §5 to LinkedIn), 1. Link index (everything in one place), 2. awesome-agent-skills (S1) — how the catalog is organized, 3. Skills relevant to THIS project (checked hyperlink by hyperlink), 3a. Directly usable — browser automation / scraping, 3b. Usable as services (API, not browser) — discovery / enrichment, 3c. Job-domain (career) skills — pipeline-adjacent, not scraping, 4. awesome-agent-skills-mcp (S2/S3) — evaluation for this repo (+8 more)

### Community 10 - "crud.py"
Cohesion: 0.10
Nodes (25): collections, fastapi_encoders, get_engine(), init_db(), Return the cached engine, creating it (and the session factory) first., Create ``jobs`` / ``scrape_runs`` tables if they don't exist (idempotent)., get_job(), JobNotFound (+17 more)

### Community 12 - "export_jobs"
Cohesion: 0.19
Nodes (15): DataFrame, export_jobs(), _hyperlink_titles(), load_frame(), Path, Load jobs from SQLite into a :class:`~pandas.DataFrame`. Args: location:…, Export the current DB snapshot to CSV or Excel. Args: fmt: ``"csv"`` (default)…, Turn title cells into clickable apply hyperlinks (Excel-ready). Display text… (+7 more)

### Community 13 - "orchestrator.py"
Cohesion: 0.12
Nodes (22): collections_abc, contextlib, Shared API error type — one shape for every failure. All errors surface as…, _target(), Operation orchestrator — the brain. Browsers are only the hands. Every long…, attached_run_log(), list_log_files(), log_dir() (+14 more)

### Community 14 - "do_scrape"
Cohesion: 0.18
Nodes (11): apscheduler_schedulers_blocking, apscheduler_triggers_cron, do_scrape(), Execute the shared scrape pipeline; return process exit code. Opens the…, Path, Timestamped JSON + CSV file export (SQLite remains the source of truth)., save_results(), APScheduler wrapper — periodic collection without babysitting tabs. Usage::… (+3 more)

### Community 15 - "Project Document — Secure Naukri.com Jobs Collector"
Cohesion: 0.22
Nodes (9): 1. How it works (pipeline), 2. Module reference, 3. Configuration (`.env`, see `.env.example`), 4. Commands, 5. Data model, 6. Known environment notes (verified), 7. Fair use, 8. Knowledge graph (Graphify) (+1 more)

### Community 16 - "Secure Naukri.com Jobs Collector"
Cohesion: 0.20
Nodes (9): 1. Setup (one time), 2. Usage, 2b. Docs, knowledge graph & testing phase, 3. Architecture (your proposed stack, as built), 4. Files, 5. Fair-use note, Playwright (bundled Chromium) + uBlock Origin Lite | Pydantic + SQLite | Typer + Rich | personal use, Secure Naukri.com Jobs Collector (+1 more)

### Community 17 - "ops.py"
Cohesion: 0.11
Nodes (22): PlainTextResponse, _get(), Return stripped env var ``name`` or ``default`` when unset., health(), log_tail(), logs(), Ops router — liveness, stats, DB explorer, and run-log viewer. Mirrors the…, Liveness: process up, DB reachable, run-hub size. (+14 more)

### Community 18 - "Bot-Detection Test Guide — measure exposure, don't chase “Human”"
Cohesion: 0.29
Nodes (6): 1. Sites (comparison order), 2. Procedure — Test A/B/C matrix, 3. Signal table (fill from your runs), 4. Reading the results, 5. Fix applied from these measurements (2026-09-19), Bot-Detection Test Guide — measure exposure, don't chase “Human”

### Community 19 - "RunOut"
Cohesion: 0.17
Nodes (18): post, cancel(), get_one(), list_all(), Start a scrape run (202 + run id; 409 when one already runs)., Start an export run; fetch the file at its download URL when done., Scan key skills across fresh postings (202 + run id; 409 when busy)., Collect one lane into SQLite (202 + run id; 409 when busy). (+10 more)

### Community 20 - "Hardening Controls"
Cohesion: 0.05
Nodes (42): Broken Access Control, Broken Authentication, Cross-Site Scripting (XSS), Data Classification, Dependency Audit Triage, Destructive Operations on Derived Paths, File Upload Safety, Hardening Patterns (+34 more)

### Community 21 - "upsert_jobs"
Cohesion: 0.14
Nodes (21): Session, count_jobs(), fetch_all_jobs(), get_session(), Append one audit row to ``scrape_runs`` for this pipeline execution., Return the freshest jobs (by ``last_seen`` desc) as validated models., Return the total number of unique jobs stored., Open a new ORM session from the shared factory. (+13 more)

### Community 22 - "RunRecord"
Cohesion: 0.11
Nodes (24): default_collect_runner(), API collection into SQLite (JobSpy-clone): fetch → upsert → audit. Falls back…, All runs, newest first., Mutable state for one background run (owned by the orchestrator)., True once ``cancel`` was requested (polled between pages)., Merge a progress update and append it to the stage timeline., JSON-safe snapshot for REST responses and MCP tool results., RunRecord (+16 more)

### Community 23 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 24 - "agent-skills"
Cohesion: 0.08
Nodes (23): codemode, environment, timeout, type, LOG_LEVEL, SKILLS_CACHE_DIR, SKILLS_SYNC_INTERVAL, headers (+15 more)

### Community 25 - "runs.py"
Cohesion: 0.14
Nodes (13): FastAPI, fastapi_exceptions, fastapi_responses, Request, get_orchestrator(), Shared dependencies — one place for cross-router needs. Per the FastAPI bigger-…, Resolve the process-wide :class:`Orchestrator` from app state. Tests and the…, _mount_scalar() (+5 more)

### Community 26 - "Web Control Plane — Spec + Guide"
Cohesion: 0.15
Nodes (12): Architecture (FastAPI bigger-applications shape), Boundaries, Contract (every action has a cancel twin), Evidence (verify-before-claim), Key-skills scan (API fast path + browser fallback), Lane collection → Excel with hyperlinks, MCP tools (curated) + harness wiring, Objective (+4 more)

### Community 27 - "Orchestrator"
Cohesion: 0.08
Nodes (33): RunnerFunc, create_app(), Build the app (pass an :class:`Orchestrator`, else one is made). Routers…, BusyError, Orchestrator, Spawns, tracks, and cancels background runs (thread-safe)., Start a scrape run; 409-style :class:`BusyError` if one runs., Start an export run (exports never contend with each other). (+25 more)

### Community 28 - "Agent Skills (OpenCode)"
Cohesion: 0.33
Nodes (5): Agent Skills (OpenCode), Core Rules, Execution Model, graphify, Intent → Skill Mapping

### Community 29 - "nkapi.py"
Cohesion: 0.09
Nodes (29): base64, functools, httpx, secrets, api_collect_jobs(), api_job_to_raw(), api_scan_skills(), company_mode() (+21 more)

### Community 30 - "OpenCode Setup (v2) — plugins, skills, MCP servers"
Cohesion: 0.29
Nodes (6): 1. Config file — `.opencode/opencode.json`, 2. Plugin — `.opencode/plugins/graphify.js`, 3. MCP servers, 4. Skills — `.opencode/skills/`, 5. Verify (run after any change here), OpenCode Setup (v2) — plugins, skills, MCP servers

### Community 31 - "Worked example: Agent Teams for competing-hypothesis debugging"
Cohesion: 0.06
Nodes (31): 1. Direct invocation (no orchestration), 2. Single-persona slash command, 3. Parallel fan-out with merge, 4. Sequential pipeline as user-driven slash commands, 5. Research isolation (context preservation), A. Router persona ("meta-orchestrator"), Anti-pattern in this scenario, Anti-patterns (+23 more)

### Community 33 - "Code Review and Quality"
Cohesion: 0.07
Nodes (29): 1. Correctness, 2. Readability & Simplicity, 3. Architecture, 4. Security, 5. Performance, Change Descriptions, Change Sizing, Code Review and Quality (+21 more)

### Community 34 - "Test-Driven Development"
Cohesion: 0.07
Nodes (29): Browser Testing with DevTools, Common Rationalizations, DAMP Over DRY in Tests, Decision Guide, Discover the Stack First, Name Tests Descriptively, One Assertion Per Concept, Overview (+21 more)

### Community 35 - "Context Engineering"
Cohesion: 0.07
Nodes (28): Anti-Patterns, Common Rationalizations, Compress before dropping, Confusion Management, Context Budget Management, Context Engineering, Context Packing Strategies, Level 1: Rules Files (+20 more)

### Community 36 - "Performance Checklist"
Cohesion: 0.07
Nodes (26): API, Backend Checklist, Cache checklist, Caching Strategies, Common Anti-Patterns, Connection pooling, Core Web Vitals Targets, CSS (+18 more)

### Community 37 - "Git Workflow and Versioning"
Cohesion: 0.07
Nodes (26): 1. Commit Early, Commit Often, 2. Atomic Commits, 3. Descriptive Messages, 4. Keep Concerns Separate, 5. Size Your Changes, Branch Naming, Branching Strategy, Change Summaries (+18 more)

### Community 38 - "Optimization Patterns"
Cohesion: 0.07
Nodes (25): Connection Pool Exhaustion, Large Bundle Size, Missing Caching (Backend), Missing Image Optimization (Frontend), N+1 Queries (Backend), Optimization Patterns, Queries That Ignore Their Index, Unbounded Data Fetching (+17 more)

### Community 39 - "Shipping and Launch"
Cohesion: 0.08
Nodes (25): Accessibility, Code Quality, Common Rationalizations, Documentation, Error Budget Release Gate, Error Reporting, Feature Flag Strategy, Infrastructure (+17 more)

### Community 40 - "API and Interface Design"
Cohesion: 0.08
Nodes (24): 1. Contract First, 2. Consistent Error Semantics, 3. Validate at Boundaries, 4. Prefer Addition Over Modification, 5. Predictable Naming, 6. Honouring an Idempotency Key, API and Interface Design, Common Rationalizations (+16 more)

### Community 41 - "Browser Testing with DevTools"
Cohesion: 0.08
Nodes (24): Accessibility Verification with DevTools, Available Tools, Browser Testing with DevTools, Clean Console Standard, Common Rationalizations, Console Analysis Patterns, Content Boundary Markers, For Network Issues (+16 more)

### Community 42 - "Frontend UI Engineering"
Cohesion: 0.08
Nodes (24): Accessibility (WCAG 2.1 AA), ARIA Labels, Avoid the AI Aesthetic, Color, Common Rationalizations, Component Architecture, Component Patterns, Design System Adherence (+16 more)

### Community 43 - "schemas.py"
Cohesion: 0.12
Nodes (22): CollectRequest, DbTable, DbTablePage, ExportRequest, JobsPage, LogFile, BaseModel, REST contracts — typed input/output for every endpoint (contract-first).… (+14 more)

### Community 44 - "CI/CD and Automation"
Cohesion: 0.08
Nodes (23): Automation Beyond CI, Basic CI Pipeline, Build Cop Role, CI/CD and Automation, CI Optimization, Common Rationalizations, Dependabot / Renovate, Deployment Strategies (+15 more)

### Community 45 - "Constraint-Driven Development"
Cohesion: 0.08
Nodes (22): Adapting it, Contract, Floor guard: reference implementation, Reference (Node, ~stack-agnostic patterns), Common Rationalizations, Constraint-Driven Development, Escalation Path, Loading Constraints (+14 more)

### Community 46 - "Deprecation and Migration"
Cohesion: 0.08
Nodes (23): Adapter Pattern, Code Is a Liability, Common Rationalizations, Compulsory vs Advisory Deprecation, Core Principles, Database Schema Migrations (Expand/Contract), Deprecation and Migration, Deprecation Planning Starts at Design Time (+15 more)

### Community 47 - "raw_card"
Cohesion: 0.23
Nodes (14): Run the full collection pass: all locations × pages → enriched Jobs. Stages:…, run_scrape(), Build an in-page-JS-style raw card dict (camelCase keys)., raw_card(), test_run_scrape_cap_breaks_next_page_loop(), test_run_scrape_close_failure_swallowed(), test_run_scrape_full_flow(), test_run_scrape_no_enrich_and_cap() (+6 more)

### Community 48 - "Documentation and ADRs"
Cohesion: 0.09
Nodes (22): ADR Lifecycle, ADR Template, API Documentation, Architecture Decision Records (ADRs), Changelog Maintenance, Common Rationalizations, Document Known Gotchas, Documentation and ADRs (+14 more)

### Community 49 - "Incremental Implementation"
Cohesion: 0.09
Nodes (22): Common Rationalizations, Contract-First Slicing, Implementation Rules, Increment Checklist, Incremental Implementation, Overview, Red Flags, Risk-First Slicing (+14 more)

### Community 50 - "FakeContext"
Cohesion: 0.06
Nodes (38): pytest, _extension_args(), Build ``--load-extension`` args for uBOL (headed mode only). Headless-shell…, fake_playwright(), FakeBrowserType, FakeContext, FakeKeyboard, FakeMouse (+30 more)

### Community 51 - "Code Simplification"
Cohesion: 0.09
Nodes (21): 1. Preserve Behavior Exactly, 2. Follow Project Conventions, 3. Prefer Clarity Over Cleverness, 4. Maintain Balance, 5. Scope to What Changed, Code Simplification, Common Rationalizations, Language-Specific Guidance (+13 more)

### Community 52 - "Debugging and Error Recovery"
Cohesion: 0.09
Nodes (21): Build Failure Triage, Common Rationalizations, Debugging and Error Recovery, Error-Specific Patterns, Instrumentation Guidelines, Overview, Red Flags, Runtime Error Triage (+13 more)

### Community 53 - "db.py"
Cohesion: 0.17
Nodes (13): DeclarativeBase, pandas, pydantic, sqlalchemy, sqlalchemy_orm, SQLite access via SQLAlchemy — engine, sessions, and upsert logic. Design…, Resolve a relative ``sqlite:///jobs.db`` URL against the project root. Absolute…, _resolve_url() (+5 more)

### Community 54 - "_FakeSched"
Cohesion: 0.25
Nodes (6): _FakeSched, BlockingScheduler stand-in — records jobs, scriptable start()., test_run_scheduled_handles_interrupt(), _factory(), test_run_scheduled_handles_system_exit(), _factory()

### Community 55 - "Interview Me"
Cohesion: 0.11
Nodes (18): Common Rationalizations, Example, Interaction with Other Skills, Interview Me, Loading Constraints, Output, Overview, Red Flags (+10 more)

### Community 56 - "Planning and Task Breakdown"
Cohesion: 0.11
Nodes (18): Common Rationalizations, Output Files, Overview, Parallelization Opportunities, Plan Document Template, Planning and Task Breakdown, Red Flags, See Also (+10 more)

### Community 57 - "setup_logging"
Cohesion: 0.23
Nodes (9): logging, Logging setup — one call at startup, standard library only. We deliberately use…, Configure root logging to stdout. Args: level: Level name such as…, setup_logging(), browser_scan_skills(), Browser skills scan (fallback when the API fast path fails). Same report shape…, Tests for src.log and src.scheduler., test_setup_logging_levels() (+1 more)

### Community 58 - "Security Checklist"
Cohesion: 0.11
Nodes (17): AI / LLM Security, Authentication, Authorization, CORS Configuration, Data Protection, Dependency Security, Destructive Path Operations, Error Handling (+9 more)

### Community 59 - "ReOrder: Keep Your Regulars Ordering Direct"
Cohesion: 0.11
Nodes (17): Example 1: Vague Early-Stage Concept (Full 3-Phase Session), Example 2: Feature Idea Within an Existing Product (Codebase-Aware), Example 3: Process/Workflow Idea (Non-Product), Ideation Session Examples, Key Assumptions to Validate, MVP Scope, Not Doing (and Why), Open Questions (+9 more)

### Community 60 - "Idea Refine"
Cohesion: 0.11
Nodes (17): Anti-patterns to Avoid, Common Rationalizations, Detailed Instructions, How It Works, Idea Refine, Output, Overview, Phase 1: Understand & Expand (Divergent) (+9 more)

### Community 61 - "launch_context"
Cohesion: 0.06
Nodes (47): argparse, datetime, json, pathlib, Playwright, playwright_sync_api, random, retry (+39 more)

### Community 62 - "Accessibility Checklist"
Cohesion: 0.12
Nodes (16): Accessibility Checklist, Accessible Lists, ARIA Roles, Buttons vs. Links, Common Anti-Patterns, Common HTML Patterns, Content, Essential Checks (+8 more)

### Community 63 - "Doubt-Driven Development"
Cohesion: 0.12
Nodes (15): Common Rationalizations, Cross-model escalation, Doubt-Driven Development, Interaction with Other Skills, Loading Constraints, Overview, Red Flags, Step 1: CLAIM — Surface what stands (+7 more)

### Community 64 - "Process"
Cohesion: 0.12
Nodes (15): 1. Define "working" before instrumenting, 2. Pick the right signal for each question, 3. Structured logging, 4. Metrics, 5. Distributed tracing, 6. Alerting, 7. Verify the telemetry itself, Common Rationalizations (+7 more)

### Community 65 - "Using Agent Skills"
Cohesion: 0.13
Nodes (14): 1. Surface Assumptions, 2. Manage Confusion Actively, 3. Push Back When Warranted, 4. Enforce Simplicity, 5. Maintain Scope Discipline, 6. Verify, Don't Assume, Core Operating Behaviors, Failure Modes to Avoid (+6 more)

### Community 66 - "._squeeze"
Cohesion: 0.40
Nodes (3): field_validator, Canonicalise URLs: trim whitespace, drop tracking query params., Collapse inner whitespace/newlines so table output stays tidy.

### Community 67 - "Testing Patterns Reference (JavaScript/TypeScript)"
Cohesion: 0.14
Nodes (13): API / Integration Testing, Common Assertions, E2E Testing (Playwright), Mock at Boundaries Only, Mock Functions, Mock Modules, Mocking Patterns, React/Component Testing (+5 more)

### Community 68 - "Spec-Driven Development"
Cohesion: 0.14
Nodes (13): Common Rationalizations, Keeping the Spec Alive, Overview, Phase 0: Scope Check, Phase 1: Specify, Phase 2: Plan, Phase 3: Tasks, Phase 4: Implement (+5 more)

### Community 69 - "Source-Driven Development"
Cohesion: 0.15
Nodes (12): Common Rationalizations, Overview, Red Flags, Retrieval Safety: Treat Fetched Content as Data, Source-Driven Development, Step 1: Detect Stack and Versions, Step 2: Fetch Official Documentation, Step 3: Implement Following Documented Patterns (+4 more)

### Community 70 - "Testing Guide — practice progression + automated suite"
Cohesion: 0.29
Nodes (6): 1. Practice progression (manual, in order), 2. Automated suite (this repo), 3. Live practice runs (this repo, Chrome-only stack), 4. Live e-commerce test (Amazon.in + Flipkart), 5. Test matrix (automated ↔ manual), Testing Guide — practice progression + automated suite

### Community 71 - "Refinement & Evaluation Criteria"
Cohesion: 0.17
Nodes (11): 1. User Value, 2. Feasibility, 3. Differentiation, Assumption Audit, Core Evaluation Dimensions, Decision Framework, Might Be True (Nice to Have), Must Be True (Dealbreakers) (+3 more)

### Community 72 - "The Standing Checklist"
Cohesion: 0.18
Nodes (10): Correctness, Definition of Done, Definition of Done vs. Acceptance Criteria, Documentation, How to Apply, Integration, Quality, Red Flags (+2 more)

### Community 73 - "Observability Checklist"
Cohesion: 0.18
Nodes (10): Alerting, Dashboards, Distributed Tracing, Metrics, Observability Checklist, On-Call Questions (Start Here), Pre-Launch Gate, Structured Logging (+2 more)

### Community 74 - "Ideation Frameworks Reference"
Cohesion: 0.22
Nodes (8): Analogous Inspiration, Constraint-Based Ideation, First Principles Thinking, How Might We (HMW), Ideation Frameworks Reference, Jobs to Be Done (JTBD), Pre-mortem, SCAMPER

### Community 75 - "Full Code Explanation — Secure Naukri.com Jobs Collector"
Cohesion: 0.17
Nodes (12): 10. Testing architecture (why 100% is feasible), 11. Knowledge graph + living docs, 12. Fair use (binding), 1. Project structure (where everything lives), 2. Start point (how the app boots), 3. Endpoints (CLI commands — this app has no HTTP server), 4. Code style (the conventions used everywhere), 6. Design patterns — GoF catalog (with file:line evidence) (+4 more)

### Community 76 - "build_mcp"
Cohesion: 0.10
Nodes (18): get_stats(), list_jobs(), Filter + paginate collected jobs (freshest first). Args: q: Case-insensitive…, Aggregate DB overview for KPIs + charts (safe on an empty DB)., build_mcp(), collector_stats(), search_jobs(), Curated MCP tools over the orchestrator (purpose-built, not auto-converted).… (+10 more)

### Community 77 - "test_scraper.py"
Cohesion: 0.19
Nodes (17): build_skills_report(), enrich_job(), Visit ONE job page and merge detail fields (description/skills/apply). Returns…, Aggregate key-skill frequencies across enriched jobs. ``by_company=True``…, make_job(), Build a valid Job with sensible defaults; ``over`` overrides fields., Tests for src.naukri_scraper — URLs, guards, extraction, full fake runs., test_build_skills_report_counts_postings_once() (+9 more)

### Community 78 - "default_scrape_runner"
Cohesion: 0.18
Nodes (17): default_scrape_runner(), default_skills_runner(), Full collection pipeline in the worker thread (browser + DB + files). Imports…, Key-skills scan in the worker thread (API fast path, browser fallback). Tries…, Render the frequency report as a plain-text file (the .txt export)., render_skills_text(), _FakePW, _force_browser_fallback() (+9 more)

### Community 80 - "7. Module-by-module explanation"
Cohesion: 0.18
Nodes (11): 7. Module-by-module explanation, `config.py` — Layer 0, env-driven settings, `db.py` — Layer 4, repository, `export.py` — Layer 5, Pandas snapshots, `log.py` — one-call logging, `main.py` — shell, front door, `models.py` — Layers 3+4, the data contract, `naukri_scraper.py` — Layer 2-live, the pipeline core (+3 more)

### Community 82 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 85 - "Graphify — queryable knowledge graph of this repo"
Cohesion: 0.25
Nodes (5): Artifacts (`graphify-out/`, committed), Graphify — queryable knowledge graph of this repo, Repo wiring, This repo's map (from `GRAPH_REPORT.md`), Usage (no API key needed for code)

### Community 86 - "9. Mermaid diagrams (detail)"
Cohesion: 0.25
Nodes (8): 9.1 Full data-flow (browser → DB → files), 9.1b Live network trace — measured session on naukri.com (2026-09-19), 9.2 Class / data-model diagram, 9.3 Database ER, 9.4 Module dependency graph, 9.5 Browser-launch decision flow, 9.6 Bot-wall / politeness state, 9. Mermaid diagrams (detail)

### Community 87 - "9. External repo survey (5 repos, verified Oct 2026)"
Cohesion: 0.29
Nodes (7): 9.1 speedyapply/JobSpy (~4.5k stars, MIT, `pip install python-jobspy`), 9.2 lordzohar/Naukri-autoapply-bot (~61 stars, educational), 9.3 navchandar/Naukri (~93 stars, GPL-3.0), 9.4 ankitbaghel01/naukri_update (~83 stars, Node.js 18+, Windows), 9.5 Traverser25/NopeRi (~88 stars, self-reports working Jul 2026), 9.6 Adoption map for our collector (read-side stays, write-side optional), 9. External repo survey (5 repos, verified Oct 2026)

### Community 88 - "5. Architecture patterns"
Cohesion: 0.33
Nodes (6): 5.1 Layered architecture (the backbone), 5.2 ETL / pipeline pattern, 5.3 Modular monolith, CLI-first (no server, no microservices), 5.4 Repository / DAO (data-access encapsulation), 5.5 Other architectural idioms, 5. Architecture patterns

### Community 89 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 90 - "naukri_scraper.py"
Cohesion: 0.10
Nodes (20): csv, build_search_url(), build_slug_search_url(), coerce_job(), is_relevant(), normalize_raw(), Naukri.com scraper with honeypot / anti-bot hardening. Personal-use design: -…, Light relevance filter for .NET fullstack roles; keeps recall high. (+12 more)

### Community 93 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 94 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 95 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **746 isolated node(s):** `$schema`, `plugins`, `type`, `url`, `oauth` (+741 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1121 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Job` connect `Job` to `._squeeze`, `FakePage`, `src/main.py`, `crud.py`, `schemas.py`, `build_mcp`, `test_scraper.py`, `do_scrape`, `raw_card`, `ops.py`, `FakeContext`, `upsert_jobs`, `db.py`, `runs.py`, `naukri_scraper.py`, `nkapi.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `Orchestrator` connect `Orchestrator` to `test_web.py`, `build_mcp`, `orchestrator.py`, `ops.py`, `RunOut`, `RunRecord`, `runs.py`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `FakePage` connect `FakePage` to `handle_possible_block`, `Page`, `test_web.py`, `test_scraper.py`, `default_scrape_runner`, `raw_card`, `FakeContext`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `Orchestrator` (e.g. with `get_orchestrator()` and `health()`) actually correct?**
  _`Orchestrator` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Job` (e.g. with `fetch_all_jobs()` and `upsert_jobs()`) actually correct?**
  _`Job` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `plugins`, `type` to the rest of the system?**
  _746 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `handle_possible_block` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._