# Graph Report - PythonWebScraping  (2026-10-25)

## Corpus Check
- 120 files · ~167,368 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .example 1)

## Summary
- 2232 nodes · 4107 edges · 119 communities (111 shown, 8 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 477 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5d0f5466`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- validate-coverage-ledger.cjs
- Job
- validate-findings.cjs
- run_skills_scan
- src/main.py
- test_parser.py
- test_main.py
- config.py
- test_db.py
- LinkedIn Jobs Expansion — Deep Research
- AI, LLM, and Agent Hunting
- orchestrator.py
- setup_logging
- confirmed
- Project Document — Secure Naukri.com Jobs Collector
- Jobs Collector
- crud.py
- Bot-Detection Test Guide — measure exposure, don't chase “Human”
- jobs.py
- Hardening Controls
- db.py
- api_collect_jobs
- Orchestrator
- agent-skills
- ops.py
- Web Control Plane — Spec + Guide
- RunRecord
- Agent Skills (OpenCode)
- nkapi.py
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
- test_export.py
- CI/CD and Automation
- Constraint-Driven Development
- Deprecation and Migration
- should_exclude_frontend_job
- Documentation and ADRs
- Incremental Implementation
- Security Audit
- Code Simplification
- Debugging and Error Recovery
- default_collect_runner
- FakeContext
- Interview Me
- Planning and Task Breakdown
- FakePage
- Security Checklist
- ReOrder: Keep Your Regulars Ordering Direct
- Idea Refine
- scrape_site
- Accessibility Checklist
- Doubt-Driven Development
- Process
- Using Agent Skills
- conftest.py
- Testing Patterns Reference (JavaScript/TypeScript)
- Spec-Driven Development
- Source-Driven Development
- Client-Side and Browser Hunting
- Refinement & Evaluation Criteria
- The Standing Checklist
- Observability Checklist
- Ideation Frameworks Reference
- validate-findings.test.cjs
- Cloud and Deployment Hunting
- test_scraper.py
- test_check_bot_wall_swallows_evaluate_errors
- test_web.py
- handle_possible_block
- practice_tests.py
- Data Isolation and Lifecycle Hunting
- idea-refine.sh
- test_email_collector.py
- Desktop, Mobile, and Local IPC Hunting
- 5. Test matrix (automated ↔ manual)
- export_jobs
- Memory Safety, Binary, and Kernel Hunting
- Protocols, RPC, and Messaging Hunting
- 4. Code style (the conventions used everywhere)
- Resource Exhaustion and Availability Hunting
- HTTP-Protocol and Authentication Hunting
- Vulnerability Hunting
- Supply Chain and Release Hunting
- test_stealth.py
- Daily Lanes Runbook — fresh apply-links Excel, every morning
- ATTACK-CLASSES.md
- Phase 6: Produce target-neutral reports from final records
- Spec: LinkedIn Recruiter Email Collector
- Phase 2: Core collector
- 9. Mermaid diagrams (detail)
- linkedin_email_scraper.py
- validate-coverage-ledger.test.cjs
- EmailContact
- no_pauses
- naukri_scraper.py
- launch_context
- runlog.py
- upsert_jobs
- collectUnitErrors
- _wire_browser
- RunOut
- preflightJsonText
- is_external_apply
- _expand_show_more
- build_content_search_url
- NkApiError
- _snippet_around

## God Nodes (most connected - your core abstractions)
1. `FakePage` - 83 edges
2. `Orchestrator` - 53 edges
3. `FakeContext` - 53 edges
4. `Job` - 52 edges
5. `upsert_jobs()` - 45 edges
6. `make_job()` - 41 edges
7. `Module responsibility matrix` - 38 edges
8. `RunRecord` - 37 edges
9. `run_scrape()` - 35 edges
10. `launch_context()` - 34 edges

## Surprising Connections (you probably didn't know these)
- `5.3 Modular monolith, CLI-first (no server, no microservices)` --references--> `do_scrape()`  [INFERRED]
  docs/CODE_EXPLANATION.md → src/main.py
- `6. R2 joeyism/linkedin_scraper — deep dive (stack twin)` --references--> `Job`  [INFERRED]
  docs/LINKEDIN_RESEARCH.md → src/models.py
- `3c. Job-domain (career) skills — pipeline-adjacent, not scraping` --references--> `ScrapeRun`  [INFERRED]
  docs/LINKEDIN_RESEARCH.md → src/models.py
- `Testing Strategy` --references--> `EmailContact`  [INFERRED]
  docs/SPEC-linkedin-email-collector.md → src/models.py
- ``stealth_browser.py` — Layer 1, Chromium launcher` --references--> `launch_context()`  [INFERRED]
  docs/CODE_EXPLANATION.md → src/stealth_browser.py

## Import Cycles
- None detected.

## Communities (119 total, 8 thin omitted)

### Community 0 - "validate-coverage-ledger.cjs"
Cohesion: 0.12
Nodes (23): ATTEMPT_FIELDS, ATTEMPT_STATUSES, createErrorList(), escapeUnsafeDiagnosticCharacters(), fs, hasOwn(), hasValidSemanticFields(), hasValidUnicodeScalarValues() (+15 more)

### Community 1 - "Job"
Cohesion: 0.21
Nodes (9): 6. Design patterns — GoF catalog (with file:line evidence), `models.py` — Layers 3+4, the data contract, Non-GoF / idiomatic patterns used, Job, JobRow, test_jobrow_from_job_empty_apply_falls_back_to_url(), test_jobrow_round_trip(), test_jobrow_to_job_empty_skills() (+1 more)

### Community 2 - "validate-findings.cjs"
Cohesion: 0.11
Nodes (37): canonicalKey(), append(), encode(), codePointLength(), collect(), collectDataLimitErrors(), collectFindingSemanticErrors(), collectSchemaErrors() (+29 more)

### Community 3 - "run_skills_scan"
Cohesion: 0.12
Nodes (17): build_slug_search_url(), run_skills_scan(), submit_searchbar(), _detail_skills(), test_build_slug_search_url_mirrors_manual(), test_run_skills_scan_cap_breaks_page_loop(), test_run_skills_scan_close_failure_swallowed(), test_run_skills_scan_full_flow() (+9 more)

### Community 4 - "src/main.py"
Cohesion: 0.12
Nodes (14): 3. Endpoints (CLI commands — this app has no HTTP server), `config.py` — Layer 0, env-driven settings, Success Criteria, command, collect_emails(), do_collect_emails(), _ensure_env(), export() (+6 more)

### Community 5 - "test_parser.py"
Cohesion: 0.10
Nodes (21): 7. Module-by-module explanation, `export.py` — Layer 5, Pandas snapshots, `log.py` — one-call logging, `parser.py` — Layer 2-offline, BS4 twin, `scheduler.py` — Layer 6, cron, `stealth_browser.py` — Layer 1, Chromium launcher, _card_text(), _is_trap() (+13 more)

### Community 6 - "test_main.py"
Cohesion: 0.08
Nodes (13): _FakePW, test_collect_emails_defaults_to_settings_domains(), test_collect_emails_empty_result_returns_zero(), test_collect_emails_upserts_exports_and_reports(), test_do_scrape_empty_returns_zero(), test_do_scrape_found_persists_and_snapshots(), test_ensure_env_default_base_no_copy(), test_ensure_env_first_run_copies_example() (+5 more)

### Community 7 - "config.py"
Cohesion: 0.12
Nodes (9): _get(), _get_bool(), _get_float(), _get_int(), test_get_bool_variants(), test_get_float_valid_and_invalid(), test_get_int_valid_and_invalid(), test_get_returns_default_when_unset() (+1 more)

### Community 8 - "test_db.py"
Cohesion: 0.15
Nodes (17): 11. Email collector — decision record (2026-10-23), count_emails(), get_session(), upsert_emails(), EmailRow, Phase 1: Foundation (data contract), Todo — LinkedIn Recruiter Email Collector (from tasks/plan.md, spec docs/SPEC-linkedin-email-collector.md), _contact() (+9 more)

### Community 9 - "LinkedIn Jobs Expansion — Deep Research"
Cohesion: 0.11
Nodes (17): 10. Fair-use note (extends README §5 to LinkedIn), 1. Link index (everything in one place), 2. awesome-agent-skills (S1) — how the catalog is organized, 3. Skills relevant to THIS project (checked hyperlink by hyperlink), 3a. Directly usable — browser automation / scraping, 3b. Usable as services (API, not browser) — discovery / enrichment, 3c. Job-domain (career) skills — pipeline-adjacent, not scraping, 4. awesome-agent-skills-mcp (S2/S3) — evaluation for this repo (+9 more)

### Community 10 - "AI, LLM, and Agent Hunting"
Cohesion: 0.20
Nodes (9): AI, LLM, and Agent Hunting, Context, retrieval, and memory attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), MCP and sub-agent trust classes (subagent_type: `general`), Output and disclosure attack classes (subagent_type: `general`), Tool and action attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+1 more)

### Community 12 - "orchestrator.py"
Cohesion: 0.08
Nodes (6): get_orchestrator(), ApiError, _mount_scalar(), build_mcp(), RunNotCancellable, RunNotFound

### Community 13 - "setup_logging"
Cohesion: 0.12
Nodes (8): setup_logging(), _FakeSched, test_run_scheduled_handles_interrupt(), _factory(), test_run_scheduled_handles_system_exit(), _factory(), test_setup_logging_levels(), test_setup_logging_preserves_file_handlers()

### Community 14 - "confirmed"
Cohesion: 0.24
Nodes (16): Structured hunter result, Cost budget, Coverage and prior runs, Full audit planning, Run profiles and scope, confirmed(), evidence(), needsValidation() (+8 more)

### Community 15 - "Project Document — Secure Naukri.com Jobs Collector"
Cohesion: 0.09
Nodes (19): Artifacts (`graphify-out/`, committed), Graphify — queryable knowledge graph of this repo, Repo wiring, Usage (no API key needed for code), 1. How it works (pipeline), 3. Configuration (`.env`, see `.env.example`), 4. Commands, 5. Data model (+11 more)

### Community 16 - "Jobs Collector"
Cohesion: 0.17
Nodes (11): API & MCP sketch, Architecture, Configuration, Contributing, Docs, Fair use, Jobs Collector, Quickstart (+3 more)

### Community 17 - "crud.py"
Cohesion: 0.12
Nodes (14): `db.py` — Layer 4, repository, count_jobs(), fetch_all_jobs(), get_engine(), _resolve_url(), get_stats(), list_tables(), table_rows() (+6 more)

### Community 18 - "Bot-Detection Test Guide — measure exposure, don't chase “Human”"
Cohesion: 0.29
Nodes (6): 1. Sites (comparison order), 2. Procedure — Test A/B/C matrix, 3. Signal table (fill from your runs), 4. Reading the results, 5. Fix applied from these measurements (2026-09-19), Bot-Detection Test Guide — measure exposure, don't chase “Human”

### Community 19 - "jobs.py"
Cohesion: 0.19
Nodes (6): get_job(), JobNotFound, list_jobs(), get_one(), list_all(), JobsPage

### Community 20 - "Hardening Controls"
Cohesion: 0.05
Nodes (42): Broken Access Control, Broken Authentication, Cross-Site Scripting (XSS), Data Classification, Dependency Audit Triage, Destructive Operations on Derived Paths, File Upload Safety, Hardening Patterns (+34 more)

### Community 22 - "api_collect_jobs"
Cohesion: 0.15
Nodes (22): api_collect_jobs(), api_scan_skills(), _api_job(), _api_params(), _down(), _Resp, test_api_collect_jobs_drops_external_apply_rows(), test_api_collect_jobs_drops_unwanted_rows() (+14 more)

### Community 23 - "Orchestrator"
Cohesion: 0.12
Nodes (22): create_app(), Orchestrator, _blocking(), _failing(), _instant(), _run(), test_app_without_optional_deps(), test_cancel_running_scrape_via_api() (+14 more)

### Community 24 - "agent-skills"
Cohesion: 0.10
Nodes (20): codemode, environment, timeout, type, LOG_LEVEL, SKILLS_CACHE_DIR, SKILLS_SYNC_INTERVAL, headers (+12 more)

### Community 25 - "ops.py"
Cohesion: 0.10
Nodes (13): db_table(), db_tables(), health(), log_tail(), logs(), stats(), DbTable, DbTablePage (+5 more)

### Community 26 - "Web Control Plane — Spec + Guide"
Cohesion: 0.15
Nodes (12): Architecture (FastAPI bigger-applications shape), Boundaries, Contract (every action has a cancel twin), Evidence (verify-before-claim), Key-skills scan (API fast path + browser fallback), MCP tools (curated) + optional harness wiring, Objective, Run logs (+4 more)

### Community 27 - "RunRecord"
Cohesion: 0.10
Nodes (6): BusyError, RunRecord, start_collect(), test_run_events_timeline_capped(), test_run_history_evicts_oldest(), test_start_and_finish_success()

### Community 28 - "Agent Skills (OpenCode)"
Cohesion: 0.33
Nodes (5): Agent Skills (OpenCode), Core Rules, Execution Model, graphify, Intent → Skill Mapping

### Community 29 - "nkapi.py"
Cohesion: 0.21
Nodes (5): fetch_search_page(), generate_nkparam(), _public_key(), _read_der(), test_generate_nkparam_shape()

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

### Community 43 - "test_export.py"
Cohesion: 0.06
Nodes (46): Boundaries, Code style, G1 — relevance (kills mixed / unrelated results), G2 — pure frontend, G3 — external apply (company-portal redirect), G4 — duplicates, Gate definitions (the contract), Objective (+38 more)

### Community 44 - "CI/CD and Automation"
Cohesion: 0.08
Nodes (23): Automation Beyond CI, Basic CI Pipeline, Build Cop Role, CI/CD and Automation, CI Optimization, Common Rationalizations, Dependabot / Renovate, Deployment Strategies (+15 more)

### Community 45 - "Constraint-Driven Development"
Cohesion: 0.08
Nodes (22): Adapting it, Contract, Floor guard: reference implementation, Reference (Node, ~stack-agnostic patterns), Common Rationalizations, Constraint-Driven Development, Escalation Path, Loading Constraints (+14 more)

### Community 46 - "Deprecation and Migration"
Cohesion: 0.08
Nodes (23): Adapter Pattern, Code Is a Liability, Common Rationalizations, Compulsory vs Advisory Deprecation, Core Principles, Database Schema Migrations (Expand/Contract), Deprecation and Migration, Deprecation Planning Starts at Design Time (+15 more)

### Community 47 - "should_exclude_frontend_job"
Cohesion: 0.14
Nodes (11): Testing Strategy, _external_apply_url(), _keep_wanted(), _gate_blob(), job_should_exclude_unwanted(), should_exclude_frontend_job(), should_exclude_irrelevant_job(), test_should_exclude_frontend_job_keeps_hybrids() (+3 more)

### Community 48 - "Documentation and ADRs"
Cohesion: 0.09
Nodes (22): ADR Lifecycle, ADR Template, API Documentation, Architecture Decision Records (ADRs), Changelog Maintenance, Common Rationalizations, Document Known Gotchas, Documentation and ADRs (+14 more)

### Community 49 - "Incremental Implementation"
Cohesion: 0.09
Nodes (22): Common Rationalizations, Contract-First Slicing, Implementation Rules, Increment Checklist, Incremental Implementation, Overview, Red Flags, Risk-First Slicing (+14 more)

### Community 50 - "Security Audit"
Cohesion: 0.14
Nodes (14): Anti-patterns, Core principles, Full audit setup, Full audit workflow, Operating modes, Platform terminology, Recommend the smallest effective source fix, Require a boundary and result (+6 more)

### Community 51 - "Code Simplification"
Cohesion: 0.09
Nodes (21): 1. Preserve Behavior Exactly, 2. Follow Project Conventions, 3. Prefer Clarity Over Cleverness, 4. Maintain Balance, 5. Scope to What Changed, Code Simplification, Common Rationalizations, Language-Specific Guidance (+13 more)

### Community 52 - "Debugging and Error Recovery"
Cohesion: 0.09
Nodes (21): Build Failure Triage, Common Rationalizations, Debugging and Error Recovery, Error-Specific Patterns, Instrumentation Guidelines, Overview, Red Flags, Runtime Error Triage (+13 more)

### Community 53 - "default_collect_runner"
Cohesion: 0.18
Nodes (5): company_mode(), browser_scan_skills(), default_collect_runner(), default_skills_runner(), render_skills_text()

### Community 54 - "FakeContext"
Cohesion: 0.15
Nodes (16): run_scrape(), FakeContext, raw_card(), test_run_scrape_cap_breaks_next_page_loop(), test_run_scrape_close_failure_swallowed(), test_run_scrape_excludes_java_revealed_by_enrichment(), test_run_scrape_full_flow(), test_run_scrape_no_enrich_and_cap() (+8 more)

### Community 55 - "Interview Me"
Cohesion: 0.11
Nodes (18): Common Rationalizations, Example, Interaction with Other Skills, Interview Me, Loading Constraints, Output, Overview, Red Flags (+10 more)

### Community 56 - "Planning and Task Breakdown"
Cohesion: 0.11
Nodes (18): Common Rationalizations, Output Files, Overview, Parallelization Opportunities, Plan Document Template, Planning and Task Breakdown, Red Flags, See Also (+10 more)

### Community 57 - "FakePage"
Cohesion: 0.09
Nodes (12): This repo's map (from `GRAPH_REPORT.md`), run_collect(), FakePage, test_run_collect_fallback_aborted_by_bot_wall(), test_run_collect_fallback_to_all_time(), test_run_collect_gives_up_when_login_never_completes(), test_run_collect_happy_path_scrolls_and_dedupes(), test_run_collect_logs_in_manually_then_proceeds() (+4 more)

### Community 58 - "Security Checklist"
Cohesion: 0.11
Nodes (17): AI / LLM Security, Authentication, Authorization, CORS Configuration, Data Protection, Dependency Security, Destructive Path Operations, Error Handling (+9 more)

### Community 59 - "ReOrder: Keep Your Regulars Ordering Direct"
Cohesion: 0.11
Nodes (17): Example 1: Vague Early-Stage Concept (Full 3-Phase Session), Example 2: Feature Idea Within an Existing Product (Codebase-Aware), Example 3: Process/Workflow Idea (Non-Product), Ideation Session Examples, Key Assumptions to Validate, MVP Scope, Not Doing (and Why), Open Questions (+9 more)

### Community 60 - "Idea Refine"
Cohesion: 0.11
Nodes (17): Anti-patterns to Avoid, Common Rationalizations, Detailed Instructions, How It Works, Idea Refine, Output, Overview, Phase 1: Understand & Expand (Divergent) (+9 more)

### Community 61 - "scrape_site"
Cohesion: 0.22
Nodes (3): _dismiss_flipkart_login(), Product, scrape_site()

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

### Community 66 - "conftest.py"
Cohesion: 0.09
Nodes (7): 10. Testing architecture (why 100% is feasible), 4. Live e-commerce test (Amazon.in + Flipkart), FakeBrowserType, FakeKeyboard, FakeMouse, fresh_db(), test_human_scroll_mouse_failure_falls_back()

### Community 67 - "Testing Patterns Reference (JavaScript/TypeScript)"
Cohesion: 0.14
Nodes (13): API / Integration Testing, Common Assertions, E2E Testing (Playwright), Mock at Boundaries Only, Mock Functions, Mock Modules, Mocking Patterns, React/Component Testing (+5 more)

### Community 68 - "Spec-Driven Development"
Cohesion: 0.14
Nodes (13): Common Rationalizations, Keeping the Spec Alive, Overview, Phase 0: Scope Check, Phase 1: Specify, Phase 2: Plan, Phase 3: Tasks, Phase 4: Implement (+5 more)

### Community 69 - "Source-Driven Development"
Cohesion: 0.15
Nodes (12): Common Rationalizations, Overview, Red Flags, Retrieval Safety: Treat Fetched Content as Data, Source-Driven Development, Step 1: Detect Stack and Versions, Step 2: Fetch Official Documentation, Step 3: Implement Following Documented Patterns (+4 more)

### Community 70 - "Client-Side and Browser Hunting"
Cohesion: 0.20
Nodes (10): Client-Side and Browser Hunting, Core discipline (include in every agent prompt for this domain), Cross-origin messaging and network attack classes (subagent_type: `general`), Cross-site information leak classes (subagent_type: `general`), DOM and object-state attack classes (subagent_type: `general`), Service-worker and browser-storage attack classes (subagent_type: `general`), UI-redress and navigation attack classes (subagent_type: `general`), Universal moves (apply across the above) (+2 more)

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

### Community 75 - "validate-findings.test.cjs"
Cohesion: 0.09
Nodes (13): LIMITS, assert, errorsFor(), fs, {
  LIMITS,
  collect,
  collectSchemaErrors,
  validateDocument,
}, os, path, rejectMutation() (+5 more)

### Community 76 - "Cloud and Deployment Hunting"
Cohesion: 0.20
Nodes (10): Cloud and Deployment Hunting, Configuration and secret lifecycle attack classes (subagent_type: `general`), Container and orchestration attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Ingress, network, and control-plane attack classes (subagent_type: `general`), Managed storage, events, and edge attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+2 more)

### Community 77 - "test_scraper.py"
Cohesion: 0.08
Nodes (32): _keep(), build_skills_report(), enrich_job(), job_should_exclude(), should_exclude_java_job(), make_job(), test_upsert_empty_apply_url_falls_back(), test_build_skills_report_counts_postings_once() (+24 more)

### Community 79 - "test_web.py"
Cohesion: 0.07
Nodes (15): Flag, api_job_to_raw(), default_export_runner(), CollectRequest, ExportRequest, _isolated_logs(), _payload(), test_api_job_to_raw_mapping() (+7 more)

### Community 80 - "handle_possible_block"
Cohesion: 0.08
Nodes (16): 9.1b Live network trace — measured session on naukri.com (2026-09-19), check_bot_wall(), extract_listing_cards(), _first_match(), handle_possible_block(), _pick_option(), scrape_search_page(), test_check_bot_wall_clean_and_blocked() (+8 more)

### Community 81 - "practice_tests.py"
Cohesion: 0.11
Nodes (8): main(), probe(), main(), crawl_books(), _get_with_retry(), main(), Reporter, store_books()

### Community 82 - "Data Isolation and Lifecycle Hunting"
Cohesion: 0.20
Nodes (9): Core discipline (include in every agent prompt for this domain), Data Isolation and Lifecycle Hunting, Deletion, revocation, and lifecycle attack classes (subagent_type: `general`), Derived-data and disclosure attack classes (subagent_type: `general`), Export, backup, restore, and migration attack classes (subagent_type: `general`), Tenant and object-isolation attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+1 more)

### Community 84 - "test_email_collector.py"
Cohesion: 0.20
Nodes (12): _contacts_from_cards(), extract_emails(), test_contacts_from_cards_drops_unrelated_posts(), test_contacts_from_cards_maps_fields_and_snippet(), test_contacts_from_cards_skips_cards_without_email(), test_contacts_from_cards_snippet_window_is_bounded(), test_contacts_from_cards_tolerates_missing_fields(), test_contacts_from_cards_uses_urn_as_post_id() (+4 more)

### Community 85 - "Desktop, Mobile, and Local IPC Hunting"
Cohesion: 0.20
Nodes (10): Application-state and device-lifecycle attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Deep-link, callback, and navigation attack classes (subagent_type: `general`), Desktop, Mobile, and Local IPC Hunting, Local IPC and exported-component attack classes (subagent_type: `general`), Privileged-helper and local-file attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+2 more)

### Community 86 - "5. Test matrix (automated ↔ manual)"
Cohesion: 0.29
Nodes (5): 1. Practice progression (manual, in order), 2. Automated suite (this repo), 3. Live practice runs (this repo, Chrome-only stack), 5. Test matrix (automated ↔ manual), Testing Guide — practice progression + automated suite

### Community 87 - "export_jobs"
Cohesion: 0.40
Nodes (3): export_jobs(), _hyperlink_titles(), test_export_excel_hyperlinks()

### Community 88 - "Memory Safety, Binary, and Kernel Hunting"
Cohesion: 0.20
Nodes (10): Binary loading and runtime attack classes (subagent_type: `general`), Bounds, integer, and representation attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), FFI and ABI attack classes (subagent_type: `general`), Kernel and privileged-interface attack classes (subagent_type: `general`), Lifetime, type, and concurrency attack classes (subagent_type: `general`), Memory Safety, Binary, and Kernel Hunting, Universal moves (apply across the above) (+2 more)

### Community 89 - "Protocols, RPC, and Messaging Hunting"
Cohesion: 0.20
Nodes (9): Broker and queue isolation attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Framing, schema, and interpretation attack classes (subagent_type: `general`), Protocols, RPC, and Messaging Hunting, Replay, ordering, and transaction attack classes (subagent_type: `general`), RPC identity and authorization attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+1 more)

### Community 90 - "4. Code style (the conventions used everywhere)"
Cohesion: 0.11
Nodes (17): 11. Knowledge graph + living docs, 12. Fair use (binding), 1. Project structure (where everything lives), 4. Code style (the conventions used everywhere), 5.1 Layered architecture (the backbone), 5.2 ETL / pipeline pattern, 5.3 Modular monolith, CLI-first (no server, no microservices), 5.5 Other architectural idioms (+9 more)

### Community 91 - "Resource Exhaustion and Availability Hunting"
Cohesion: 0.20
Nodes (9): Computational amplification attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Failure and recovery attack classes (subagent_type: `general`), Quota and scheduling attack classes (subagent_type: `general`), Resource accumulation attack classes (subagent_type: `general`), Resource Exhaustion and Availability Hunting, Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+1 more)

### Community 92 - "HTTP-Protocol and Authentication Hunting"
Cohesion: 0.18
Nodes (10): API-key and mTLS attack classes (subagent_type: `general`), Browser-session attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Federated-identity attack classes (subagent_type: `general`), HTTP framing and cache attack classes (subagent_type: `general`), HTTP-Protocol and Authentication Hunting, MFA, passkey, and account-transition attack classes (subagent_type: `general`), Universal moves (apply across the above) (+2 more)

### Community 93 - "Vulnerability Hunting"
Cohesion: 0.22
Nodes (9): Core hunting method — include in every hunter prompt, Core validation rules — include in every hunter prompt, Coverage-critic waves, Local validation boundaries, Parent consolidation and ledger update, Phase 2: Run coverage-led hunting waves, Promotion procedure — copy this promotion procedure verbatim into every hunter prompt, Required hunter prompt (+1 more)

### Community 94 - "Supply Chain and Release Hunting"
Cohesion: 0.22
Nodes (8): CI and automation attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Dependency and build-input attack classes (subagent_type: `general`), Release and update attack classes (subagent_type: `general`), Supply Chain and Release Hunting, Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here), When to use this file

### Community 95 - "test_stealth.py"
Cohesion: 0.14
Nodes (18): _extension_args(), fake_playwright(), FakeRoute, _handler(), test_blocker_aborts_trackers_pixels_and_continues_rest(), test_blocker_disabled_registers_nothing(), test_extension_args_headed_load(), test_extension_args_missing_dir() (+10 more)

### Community 96 - "Daily Lanes Runbook — fresh apply-links Excel, every morning"
Cohesion: 0.20
Nodes (9): 0. Start the server (once per day), 1. The two lanes (exact criteria — do not improvise), 1b. Pure-Java exclusion (always on), 2. Collect (API path, ~25s per lane, no browser), 3. Export the Excel (titles are real hyperlinks), 4. Sanity checks (2 minutes), 5. Changing the recipe, Daily Lanes Runbook — fresh apply-links Excel, every morning (+1 more)

### Community 97 - "ATTACK-CLASSES.md"
Cohesion: 0.14
Nodes (7): Attack Classes, Attack classes — choose and split based on Phase 1, Architecture summary and companion selection, Deterministic coverage ledger, Phase 1: Map the source and plan coverage, Prior-run input, Reconnaissance

### Community 98 - "Phase 6: Produce target-neutral reports from final records"
Cohesion: 0.50
Nodes (4): `FINDINGS-DETAIL.md`, `NEEDS-VALIDATION.md`, Phase 6: Produce target-neutral reports from final records, `REPORT.md`

### Community 99 - "Spec: LinkedIn Recruiter Email Collector"
Cohesion: 0.12
Nodes (15): Boundaries, Code Style, Commands, Data contract, Decisions already made (clarification round, 2026-10-23), Design, Fair use (extends LINKEDIN_RESEARCH §10), Objective (+7 more)

### Community 100 - "Phase 2: Core collector"
Cohesion: 0.17
Nodes (11): Architecture Decisions, Checkpoint: Complete, Checkpoint: Core, Checkpoint: Foundation, Implementation Plan: LinkedIn Recruiter Email Collector, Open Questions, Overview, Phase 2: Core collector (+3 more)

### Community 101 - "9. Mermaid diagrams (detail)"
Cohesion: 0.29
Nodes (7): 9.1 Full data-flow (browser → DB → files), 9.2 Class / data-model diagram, 9.3 Database ER, 9.4 Module dependency graph, 9.5 Browser-launch decision flow, 9.6 Bot-wall / politeness state, 9. Mermaid diagrams (detail)

### Community 102 - "linkedin_email_scraper.py"
Cohesion: 0.15
Nodes (10): Implementation note (2026-10-23), _check_bot_wall(), _on_login_wall(), _prompt_manual_login(), _ensure_signed_in(), _wait_for_login(), test_on_login_wall_detects_auth_redirect(), test_wait_for_login_gives_up_after_grace() (+2 more)

### Community 103 - "validate-coverage-ledger.test.cjs"
Cohesion: 0.11
Nodes (16): canonicalCoverageId(), encodeCanonicalRef(), LIMITS, archivedAttempt(), assert, fs, {
  LIMITS,
  canonicalCoverageId,
  encodeCanonicalRef,
  isSafeAgentId,
  isSafeRelativePath,
  preflightJsonText,
  validateDocument,
}, localCheck() (+8 more)

### Community 104 - "EmailContact"
Cohesion: 0.12
Nodes (9): EmailContact, test_email_contact_defaults_are_empty(), test_email_contact_normalises_email_and_snippet(), test_email_contact_rejects_malformed_email(), test_email_contact_snippet_capped(), test_emailrow_round_trip(), test_job_rejects_short_title_and_id(), test_job_title_squeezed() (+1 more)

### Community 106 - "naukri_scraper.py"
Cohesion: 0.13
Nodes (6): slugify_keywords(), human_pause(), api_pause(), test_slugify_matches_manual_search(), test_human_pause_zero_is_instant(), test_api_pause_uses_jobspy_window()

### Community 107 - "launch_context"
Cohesion: 0.18
Nodes (6): _login_wait(), main(), _launch_chromium(), launch_context(), launch_playwright(), _maybe_block_ads()

### Community 108 - "runlog.py"
Cohesion: 0.15
Nodes (9): _target(), attached_run_log(), list_log_files(), log_dir(), LogNotFound, read_log_file(), run_log_path(), test_read_log_file_rejects_bad_names() (+1 more)

### Community 109 - "upsert_jobs"
Cohesion: 0.15
Nodes (15): 2. Start point (how the app boots), 5.4 Repository / DAO (data-access encapsulation), `main.py` — shell, front door, Module responsibility matrix, 2. Module reference, Settings, init_db(), record_run() (+7 more)

### Community 110 - "collectUnitErrors"
Cohesion: 0.34
Nodes (16): collectUnitErrors(), isCanonicalRef(), isObject(), isOwnedArtifactPath(), isSafeAgentId(), isSafeRelativePath(), isVisibleText(), requireEmptyArray() (+8 more)

### Community 111 - "_wire_browser"
Cohesion: 0.24
Nodes (10): _FakePW, _force_browser_fallback(), test_default_scrape_runner_failure_restores_settings(), test_default_scrape_runner_full_params(), test_default_scrape_runner_immediate_stop(), test_default_skills_runner_empty(), test_default_skills_runner_full(), test_skills_runner_postings_mode() (+2 more)

### Community 112 - "RunOut"
Cohesion: 0.12
Nodes (10): cancel(), download(), get_one(), list_all(), start_export(), start_scrape(), start_skills(), RunOut (+2 more)

### Community 113 - "preflightJsonText"
Cohesion: 0.40
Nodes (11): JsonStructureError, preflightJsonText(), beginContainer(), beginString(), beginValue(), closeContainer(), countValue(), currentContainer() (+3 more)

### Community 114 - "is_external_apply"
Cohesion: 0.29
Nodes (5): 1c. Lane-quality gates (always on — irrelevant / frontend / portal / dupes), Lane collection → Excel with hyperlinks, fresh_cutoff(), is_external_apply(), test_is_external_apply_signals()

### Community 115 - "_expand_show_more"
Cohesion: 0.33
Nodes (4): Implementation update (2026-10-25), _expand_show_more(), _scroll_pass(), test_expand_show_more_swallows_errors()

### Community 116 - "build_content_search_url"
Cohesion: 0.40
Nodes (4): build_content_search_url(), test_build_content_search_url_all_time(), test_build_content_search_url_rejects_unknown_facet(), test_build_content_search_url_shape()

## Knowledge Gaps
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `confirmed()` connect `confirmed` to `ATTACK-CLASSES.md`, `Client-Side and Browser Hunting`, `AI, LLM, and Agent Hunting`, `validate-findings.test.cjs`, `Cloud and Deployment Hunting`, `Data Isolation and Lifecycle Hunting`, `Security Audit`, `Desktop, Mobile, and Local IPC Hunting`, `Memory Safety, Binary, and Kernel Hunting`, `Protocols, RPC, and Messaging Hunting`, `Resource Exhaustion and Availability Hunting`, `HTTP-Protocol and Authentication Hunting`, `Vulnerability Hunting`, `Supply Chain and Release Hunting`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `FakePage` (e.g. with `10. Testing architecture (why 100% is feasible)` and `This repo's map (from `GRAPH_REPORT.md`)`) actually correct?**
  _`FakePage` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `validate-coverage-ledger.cjs` be split into smaller, more focused modules?**
  _Cohesion score 0.11666666666666667 - nodes in this community are weakly interconnected._
- **Why does `Attack classes — choose and split based on Phase 1` connect `ATTACK-CLASSES.md` to `handle_possible_block`, `confirmed`?**
  _High betweenness centrality (0.142) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `Orchestrator` (e.g. with `get_orchestrator()` and `health()`) actually correct?**
  _`Orchestrator` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `validate-findings.cjs` be split into smaller, more focused modules?**
  _Cohesion score 0.10609756097560975 - nodes in this community are weakly interconnected._
- **Why does `FakePage` connect `FakePage` to `conftest.py`, `run_skills_scan`, `linkedin_email_scraper.py`, `LinkedIn Jobs Expansion — Deep Research`, `test_scraper.py`, `test_web.py`, `handle_possible_block`, `_wire_browser`, `test_email_collector.py`, `FakeContext`, `5. Test matrix (automated ↔ manual)`, `test_stealth.py`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._