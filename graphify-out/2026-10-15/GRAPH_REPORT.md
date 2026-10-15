# Graph Report - PythonWebScraping  (2026-10-15)

## Corpus Check
- 91 files · ~109,522 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .example 1)

## Summary
- 1601 nodes · 2740 edges · 82 communities (76 shown, 6 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 327 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `908c39b5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Module responsibility matrix
- Job
- launch_context
- test_scraper.py
- src/main.py
- test_parser.py
- test_main.py
- config.py
- practice_tests.py
- LinkedIn Jobs Expansion — Deep Research
- web/main.py
- ops.py
- runlog.py
- 2. Module reference
- Project Document — Secure Naukri.com Jobs Collector
- Secure Naukri.com Jobs Collector
- schemas.py
- Bot-Detection Test Guide — measure exposure, don't chase “Human”
- runs.py
- Hardening Controls
- upsert_jobs
- BusyError
- test_web.py
- agent-skills
- build_mcp
- Web Control Plane — Spec + Guide
- Orchestrator
- Agent Skills (OpenCode)
- scrape_site
- OpenCode Setup (v2) — plugins, skills, MCP servers
- Worked example: Agent Teams for competing-hypothesis debugging
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
- FakePage
- CI/CD and Automation
- Constraint-Driven Development
- Deprecation and Migration
- crud.py
- Documentation and ADRs
- Incremental Implementation
- run_skills_scan
- Code Simplification
- Debugging and Error Recovery
- test_stealth.py
- FakeContext
- Interview Me
- Planning and Task Breakdown
- Full Code Explanation — Secure Naukri.com Jobs Collector
- Security Checklist
- ReOrder: Keep Your Regulars Ordering Direct
- Idea Refine
- stealth_browser.py
- Accessibility Checklist
- Doubt-Driven Development
- Process
- Using Agent Skills
- FakeRoute
- Testing Patterns Reference (JavaScript/TypeScript)
- Spec-Driven Development
- Source-Driven Development
- fresh_db
- Refinement & Evaluation Criteria
- The Standing Checklist
- Observability Checklist
- Ideation Frameworks Reference
- build_skills_report
- jobs.py
- _FakePW
- 9. Mermaid diagrams (detail)
- test_check_bot_wall_evaluate_failure_is_safe
- conftest.py
- idea-refine.sh

## God Nodes (most connected - your core abstractions)
1. `FakePage` - 63 edges
2. `Job` - 48 edges
3. `Orchestrator` - 48 edges
4. `FakeContext` - 39 edges
5. `Module responsibility matrix` - 39 edges
6. `upsert_jobs()` - 35 edges
7. `make_job()` - 31 edges
8. `run_scrape()` - 29 edges
9. `2. Module reference` - 29 edges
10. `launch_context()` - 27 edges

## Surprising Connections (you probably didn't know these)
- `5.3 Modular monolith, CLI-first (no server, no microservices)` --references--> `do_scrape()`  [INFERRED]
  docs/CODE_EXPLANATION.md → src/main.py
- `6. R2 joeyism/linkedin_scraper — deep dive (stack twin)` --references--> `Job`  [INFERRED]
  docs/LINKEDIN_RESEARCH.md → src/models.py
- `3c. Job-domain (career) skills — pipeline-adjacent, not scraping` --references--> `ScrapeRun`  [INFERRED]
  docs/LINKEDIN_RESEARCH.md → src/models.py
- ``stealth_browser.py` — Layer 1, Chromium launcher` --references--> `launch_context()`  [INFERRED]
  docs/CODE_EXPLANATION.md → src/stealth_browser.py
- `Module responsibility matrix` --references--> `Settings`  [INFERRED]
  docs/CODE_EXPLANATION.md → src/config.py

## Import Cycles
- None detected.

## Communities (82 total, 6 thin omitted)

### Community 0 - "Module responsibility matrix"
Cohesion: 0.13
Nodes (17): 4. Code style (the conventions used everywhere), 5.5 Other architectural idioms, 9.1b Live network trace — measured session on naukri.com (2026-09-19), Module responsibility matrix, `naukri_scraper.py` — Layer 2-live, the pipeline core, This repo's map (from `GRAPH_REPORT.md`), build_search_url(), check_bot_wall() (+9 more)

### Community 1 - "Job"
Cohesion: 0.14
Nodes (12): 6. Design patterns — GoF catalog (with file:line evidence), `models.py` — Layers 3+4, the data contract, Non-GoF / idiomatic patterns used, Job, JobRow, test_job_rejects_short_title_and_id(), test_job_title_squeezed(), test_job_url_canonicalisation() (+4 more)

### Community 2 - "launch_context"
Cohesion: 0.25
Nodes (4): _launch_chromium(), launch_context(), launch_playwright(), _maybe_block_ads()

### Community 3 - "test_scraper.py"
Cohesion: 0.15
Nodes (20): raw_card(), _detail_skills(), test_build_search_url_encodes_params(), test_coerce_job_valid_and_dropped(), test_handle_block_prompts_then_continues(), test_is_relevant(), test_normalize_raw_camel_and_snake_shapes(), test_run_scrape_cap_breaks_next_page_loop() (+12 more)

### Community 4 - "src/main.py"
Cohesion: 0.10
Nodes (16): 3. Endpoints (CLI commands — this app has no HTTP server), `config.py` — Layer 0, env-driven settings, `main.py` — shell, front door, 5. Test matrix (automated ↔ manual), command, export_jobs(), _ensure_env(), export() (+8 more)

### Community 5 - "test_parser.py"
Cohesion: 0.12
Nodes (15): `parser.py` — Layer 2-offline, BS4 twin, _card_text(), _is_trap(), parse_detail_html(), _anchor(), test_card_text_none_card(), test_parse_detail_external_apply_wins_over_traps(), test_parse_detail_internal_apply_keeps_canonical() (+7 more)

### Community 6 - "test_main.py"
Cohesion: 0.10
Nodes (7): _FakePW, test_do_scrape_empty_returns_zero(), test_do_scrape_found_persists_and_snapshots(), test_ensure_env_default_base_no_copy(), test_ensure_env_first_run_copies_example(), test_stats_command(), _wire_pipeline()

### Community 7 - "config.py"
Cohesion: 0.09
Nodes (16): _get(), _get_bool(), _get_float(), _get_int(), Settings, test_get_bool_variants(), test_get_float_valid_and_invalid(), test_get_int_valid_and_invalid() (+8 more)

### Community 8 - "practice_tests.py"
Cohesion: 0.16
Nodes (5): crawl_books(), _get_with_retry(), main(), Reporter, store_books()

### Community 9 - "LinkedIn Jobs Expansion — Deep Research"
Cohesion: 0.11
Nodes (17): 10. Fair-use note (extends README §5 to LinkedIn), 1. Link index (everything in one place), 2. awesome-agent-skills (S1) — how the catalog is organized, 3. Skills relevant to THIS project (checked hyperlink by hyperlink), 3a. Directly usable — browser automation / scraping, 3b. Usable as services (API, not browser) — discovery / enrichment, 3c. Job-domain (career) skills — pipeline-adjacent, not scraping, 4. awesome-agent-skills-mcp (S2/S3) — evaluation for this repo (+9 more)

### Community 10 - "web/main.py"
Cohesion: 0.10
Nodes (5): ApiError, create_app(), _mount_scalar(), _isolated_logs(), web_env()

### Community 12 - "ops.py"
Cohesion: 0.11
Nodes (11): list_tables(), table_rows(), TableNotFound, db_table(), db_tables(), health(), log_tail(), logs() (+3 more)

### Community 13 - "runlog.py"
Cohesion: 0.07
Nodes (17): setup_logging(), _target(), attached_run_log(), list_log_files(), log_dir(), LogNotFound, read_log_file(), run_log_path() (+9 more)

### Community 14 - "2. Module reference"
Cohesion: 0.19
Nodes (8): 2. Start point (how the app boots), 2. Module reference, init_db(), record_run(), do_scrape(), ScrapeRun, save_results(), run_scheduled()

### Community 15 - "Project Document — Secure Naukri.com Jobs Collector"
Cohesion: 0.09
Nodes (19): Artifacts (`graphify-out/`, committed), Graphify — queryable knowledge graph of this repo, Repo wiring, Usage (no API key needed for code), 1. How it works (pipeline), 3. Configuration (`.env`, see `.env.example`), 4. Commands, 5. Data model (+11 more)

### Community 16 - "Secure Naukri.com Jobs Collector"
Cohesion: 0.20
Nodes (9): 1. Setup (one time), 2. Usage, 2b. Docs, knowledge graph & testing phase, 3. Architecture (your proposed stack, as built), 4. Files, 5. Fair-use note, Playwright (bundled Chromium) + uBlock Origin Lite | Pydantic + SQLite | Typer + Rich | personal use, Secure Naukri.com Jobs Collector (+1 more)

### Community 17 - "schemas.py"
Cohesion: 0.13
Nodes (9): DbTable, DbTablePage, ExportRequest, HealthOut, ScrapeRequest, SkillsRequest, SkillTop, StatsOut (+1 more)

### Community 18 - "Bot-Detection Test Guide — measure exposure, don't chase “Human”"
Cohesion: 0.29
Nodes (6): 1. Sites (comparison order), 2. Procedure — Test A/B/C matrix, 3. Signal table (fill from your runs), 4. Reading the results, 5. Fix applied from these measurements (2026-09-19), Bot-Detection Test Guide — measure exposure, don't chase “Human”

### Community 19 - "runs.py"
Cohesion: 0.12
Nodes (9): get_orchestrator(), cancel(), download(), get_one(), list_all(), start_export(), start_scrape(), start_skills() (+1 more)

### Community 20 - "Hardening Controls"
Cohesion: 0.05
Nodes (42): Broken Access Control, Broken Authentication, Cross-Site Scripting (XSS), Data Classification, Dependency Audit Triage, Destructive Operations on Derived Paths, File Upload Safety, Hardening Patterns (+34 more)

### Community 21 - "upsert_jobs"
Cohesion: 0.14
Nodes (16): 5.4 Repository / DAO (data-access encapsulation), `db.py` — Layer 4, repository, count_jobs(), fetch_all_jobs(), get_session(), _resolve_url(), upsert_jobs(), get_stats() (+8 more)

### Community 23 - "test_web.py"
Cohesion: 0.09
Nodes (15): default_export_runner(), default_scrape_runner(), default_skills_runner(), render_skills_text(), RunRecord, test_default_export_runner_writes_files(), test_default_scrape_runner_failure_restores_settings(), test_default_scrape_runner_full_params() (+7 more)

### Community 24 - "agent-skills"
Cohesion: 0.08
Nodes (23): codemode, environment, timeout, type, LOG_LEVEL, SKILLS_CACHE_DIR, SKILLS_SYNC_INTERVAL, headers (+15 more)

### Community 25 - "build_mcp"
Cohesion: 0.13
Nodes (7): build_mcp(), RunNotCancellable, _payload(), test_app_without_optional_deps(), test_mcp_read_tools(), _tool(), _tools()

### Community 26 - "Web Control Plane — Spec + Guide"
Cohesion: 0.15
Nodes (12): Architecture (FastAPI bigger-applications shape), Boundaries, Contract (every action has a cancel twin), Evidence (verify-before-claim), Key-skills scan, MCP tools (curated) + harness wiring, Objective, Run logs (+4 more)

### Community 27 - "Orchestrator"
Cohesion: 0.13
Nodes (18): Orchestrator, RunNotFound, _blocking(), _failing(), _instant(), _run(), test_cancel_running_scrape_via_api(), test_dependency_override_injects_orchestrator() (+10 more)

### Community 28 - "Agent Skills (OpenCode)"
Cohesion: 0.33
Nodes (5): Agent Skills (OpenCode), Core Rules, Execution Model, graphify, Intent → Skill Mapping

### Community 29 - "scrape_site"
Cohesion: 0.22
Nodes (3): _dismiss_flipkart_login(), Product, scrape_site()

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

### Community 43 - "FakePage"
Cohesion: 0.09
Nodes (17): enrich_job(), FakePage, make_job(), test_check_bot_wall_clean_and_blocked(), test_enrich_job_empty_apply_url_falls_back_to_job_url(), test_enrich_job_ignores_unknown_detail_keys(), test_enrich_job_merges_detail(), test_enrich_job_timeout_returns_original() (+9 more)

### Community 44 - "CI/CD and Automation"
Cohesion: 0.08
Nodes (23): Automation Beyond CI, Basic CI Pipeline, Build Cop Role, CI/CD and Automation, CI Optimization, Common Rationalizations, Dependabot / Renovate, Deployment Strategies (+15 more)

### Community 45 - "Constraint-Driven Development"
Cohesion: 0.08
Nodes (22): Adapting it, Contract, Floor guard: reference implementation, Reference (Node, ~stack-agnostic patterns), Common Rationalizations, Constraint-Driven Development, Escalation Path, Loading Constraints (+14 more)

### Community 46 - "Deprecation and Migration"
Cohesion: 0.08
Nodes (23): Adapter Pattern, Code Is a Liability, Common Rationalizations, Compulsory vs Advisory Deprecation, Core Principles, Database Schema Migrations (Expand/Contract), Deprecation and Migration, Deprecation Planning Starts at Design Time (+15 more)

### Community 47 - "crud.py"
Cohesion: 0.15
Nodes (3): get_engine(), load_frame(), Base

### Community 48 - "Documentation and ADRs"
Cohesion: 0.09
Nodes (22): ADR Lifecycle, ADR Template, API Documentation, Architecture Decision Records (ADRs), Changelog Maintenance, Common Rationalizations, Document Known Gotchas, Documentation and ADRs (+14 more)

### Community 49 - "Incremental Implementation"
Cohesion: 0.09
Nodes (22): Common Rationalizations, Contract-First Slicing, Implementation Rules, Increment Checklist, Incremental Implementation, Overview, Red Flags, Risk-First Slicing (+14 more)

### Community 50 - "run_skills_scan"
Cohesion: 0.14
Nodes (13): run_skills_scan(), submit_searchbar(), with_page_param(), test_run_skills_scan_cap_breaks_page_loop(), test_run_skills_scan_close_failure_swallowed(), test_run_skills_scan_search_error_continues(), test_submit_searchbar_absent_bar_raises(), test_submit_searchbar_drives_bar_inputs() (+5 more)

### Community 51 - "Code Simplification"
Cohesion: 0.09
Nodes (21): 1. Preserve Behavior Exactly, 2. Follow Project Conventions, 3. Prefer Clarity Over Cleverness, 4. Maintain Balance, 5. Scope to What Changed, Code Simplification, Common Rationalizations, Language-Specific Guidance (+13 more)

### Community 52 - "Debugging and Error Recovery"
Cohesion: 0.09
Nodes (21): Build Failure Triage, Common Rationalizations, Debugging and Error Recovery, Error-Specific Patterns, Instrumentation Guidelines, Overview, Red Flags, Runtime Error Triage (+13 more)

### Community 53 - "test_stealth.py"
Cohesion: 0.21
Nodes (15): _extension_args(), fake_playwright(), test_extension_args_headed_load(), test_extension_args_missing_dir(), test_extension_args_skipped_when_headless(), test_extension_args_unset_dir(), test_human_pause_zero_is_instant(), test_launch_chromium_headed_with_ubol() (+7 more)

### Community 54 - "FakeContext"
Cohesion: 0.15
Nodes (5): FakeContext, test_run_scrape_stop_during_enrich_keeps_partial(), _stop(), test_run_skills_scan_stop_before_first_title(), test_run_skills_scan_stop_mid_pass_keeps_partial()

### Community 55 - "Interview Me"
Cohesion: 0.11
Nodes (18): Common Rationalizations, Example, Interaction with Other Skills, Interview Me, Loading Constraints, Output, Overview, Red Flags (+10 more)

### Community 56 - "Planning and Task Breakdown"
Cohesion: 0.11
Nodes (18): Common Rationalizations, Output Files, Overview, Parallelization Opportunities, Plan Document Template, Planning and Task Breakdown, Red Flags, See Also (+10 more)

### Community 57 - "Full Code Explanation — Secure Naukri.com Jobs Collector"
Cohesion: 0.14
Nodes (14): 11. Knowledge graph + living docs, 12. Fair use (binding), 1. Project structure (where everything lives), 5.1 Layered architecture (the backbone), 5.2 ETL / pipeline pattern, 5.3 Modular monolith, CLI-first (no server, no microservices), 5. Architecture patterns, 7. Module-by-module explanation (+6 more)

### Community 58 - "Security Checklist"
Cohesion: 0.11
Nodes (17): AI / LLM Security, Authentication, Authorization, CORS Configuration, Data Protection, Dependency Security, Destructive Path Operations, Error Handling (+9 more)

### Community 59 - "ReOrder: Keep Your Regulars Ordering Direct"
Cohesion: 0.11
Nodes (17): Example 1: Vague Early-Stage Concept (Full 3-Phase Session), Example 2: Feature Idea Within an Existing Product (Codebase-Aware), Example 3: Process/Workflow Idea (Non-Product), Ideation Session Examples, Key Assumptions to Validate, MVP Scope, Not Doing (and Why), Open Questions (+9 more)

### Community 60 - "Idea Refine"
Cohesion: 0.11
Nodes (17): Anti-patterns to Avoid, Common Rationalizations, Detailed Instructions, How It Works, Idea Refine, Output, Overview, Phase 1: Understand & Expand (Divergent) (+9 more)

### Community 61 - "stealth_browser.py"
Cohesion: 0.23
Nodes (3): main(), probe(), main()

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

### Community 66 - "FakeRoute"
Cohesion: 0.25
Nodes (4): FakeRoute, _handler(), test_blocker_aborts_trackers_pixels_and_continues_rest(), test_blocker_disabled_registers_nothing()

### Community 67 - "Testing Patterns Reference (JavaScript/TypeScript)"
Cohesion: 0.14
Nodes (13): API / Integration Testing, Common Assertions, E2E Testing (Playwright), Mock at Boundaries Only, Mock Functions, Mock Modules, Mocking Patterns, React/Component Testing (+5 more)

### Community 68 - "Spec-Driven Development"
Cohesion: 0.14
Nodes (13): Common Rationalizations, Keeping the Spec Alive, Overview, Phase 0: Scope Check, Phase 1: Specify, Phase 2: Plan, Phase 3: Tasks, Phase 4: Implement (+5 more)

### Community 69 - "Source-Driven Development"
Cohesion: 0.15
Nodes (12): Common Rationalizations, Overview, Red Flags, Retrieval Safety: Treat Fetched Content as Data, Source-Driven Development, Step 1: Detect Stack and Versions, Step 2: Fetch Official Documentation, Step 3: Implement Following Documented Patterns (+4 more)

### Community 70 - "fresh_db"
Cohesion: 0.20
Nodes (7): 10. Testing architecture (why 100% is feasible), 1. Practice progression (manual, in order), 2. Automated suite (this repo), 3. Live practice runs (this repo, Chrome-only stack), 4. Live e-commerce test (Amazon.in + Flipkart), Testing Guide — practice progression + automated suite, fresh_db()

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

### Community 75 - "build_skills_report"
Cohesion: 0.40
Nodes (4): build_skills_report(), test_build_skills_report_counts_postings_once(), test_build_skills_report_empty(), test_build_skills_report_unknown_company()

### Community 76 - "jobs.py"
Cohesion: 0.19
Nodes (6): get_job(), JobNotFound, list_jobs(), get_one(), list_all(), JobsPage

### Community 78 - "9. Mermaid diagrams (detail)"
Cohesion: 0.29
Nodes (7): 9.1 Full data-flow (browser → DB → files), 9.2 Class / data-model diagram, 9.3 Database ER, 9.4 Module dependency graph, 9.5 Browser-launch decision flow, 9.6 Bot-wall / politeness state, 9. Mermaid diagrams (detail)

### Community 80 - "conftest.py"
Cohesion: 0.12
Nodes (4): FakeBrowserType, FakeKeyboard, FakeMouse, test_human_scroll_mouse_failure_falls_back()

## Knowledge Gaps
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Job` connect `Job` to `Module responsibility matrix`, `test_scraper.py`, `src/main.py`, `LinkedIn Jobs Expansion — Deep Research`, `build_skills_report`, `FakePage`, `jobs.py`, `2. Module reference`, `crud.py`, `conftest.py`, `schemas.py`, `run_skills_scan`, `upsert_jobs`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `FakePage` (e.g. with `10. Testing architecture (why 100% is feasible)` and `This repo's map (from `GRAPH_REPORT.md`)`) actually correct?**
  _`FakePage` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `Module responsibility matrix` be split into smaller, more focused modules?**
  _Cohesion score 0.13257575757575757 - nodes in this community are weakly interconnected._
- **Why does `FakePage` connect `FakePage` to `Module responsibility matrix`, `test_scraper.py`, `fresh_db`, `LinkedIn Jobs Expansion — Deep Research`, `conftest.py`, `run_skills_scan`, `test_stealth.py`, `FakeContext`, `test_web.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `Job` (e.g. with `6. Design patterns — GoF catalog (with file:line evidence)` and ``db.py` — Layer 4, repository`) actually correct?**
  _`Job` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Should `Job` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Why does `Orchestrator` connect `Orchestrator` to `web/main.py`, `ops.py`, `runs.py`, `BusyError`, `test_web.py`, `build_mcp`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._