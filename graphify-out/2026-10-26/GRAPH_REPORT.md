# Graph Report - PythonWebScraping  (2026-10-26)

## Corpus Check
- 126 files · ~179,697 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .example 1)

## Summary
- 2463 nodes · 4672 edges · 136 communities (129 shown, 7 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 517 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fa95b489`
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
- upsert_emails
- LinkedIn Jobs Expansion — Deep Research
- AI, LLM, and Agent Hunting
- test_web.py
- setup_logging
- confirmed
- Project Document — Secure Naukri.com Jobs Collector
- Jobs Collector
- export.py
- ops.py
- api_collect_jobs
- Hardening Controls
- parse_domain_targets
- runlog.py
- create_app
- agent-skills
- ApiError
- Spec — Naukri key-skills scan
- _on_login_wall
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
- Spec: Lane Job-Quality Gates (irrelevant · pure-frontend · external-apply · dedupe)
- FakeContext
- Interview Me
- Planning and Task Breakdown
- handle_possible_block
- Security Checklist
- ReOrder: Keep Your Regulars Ordering Direct
- Idea Refine
- 5. Test matrix (automated ↔ manual)
- Accessibility Checklist
- Doubt-Driven Development
- Process
- Using Agent Skills
- test_stealth.py
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
- linkedin_email_scraper.py
- orchestrator.py
- Page
- practice_tests.py
- Data Isolation and Lifecycle Hunting
- idea-refine.sh
- test_email_collector.py
- Desktop, Mobile, and Local IPC Hunting
- naukri_scraper.py
- collectUnitErrors
- Memory Safety, Binary, and Kernel Hunting
- Protocols, RPC, and Messaging Hunting
- Full Code Explanation — Secure Naukri.com Jobs Collector
- Resource Exhaustion and Availability Hunting
- HTTP-Protocol and Authentication Hunting
- Vulnerability Hunting
- Supply Chain and Release Hunting
- _posted_timestamp
- Daily Lanes Runbook — fresh apply-links Excel, every morning
- ATTACK-CLASSES.md
- Phase 6: Produce target-neutral reports from final records
- Spec: LinkedIn Recruiter Email Collector
- Task List
- table_rows
- FakePage
- web/main.py
- EmailContact
- _click_next_page
- run_scrape
- Naukri market snapshot — C#/.NET (2026-10-26)
- Module responsibility matrix
- upsert_jobs
- preflightJsonText
- stealth_browser.py
- Orchestrator
- jobs.py
- Conventional Commits
- _BrokenPage
- make_job
- Web Control Plane — Spec + Guide
- _apply_content_filters
- load_email_frame
- human_pause
- Tokei — count your code, quickly
- The Simplification Process
- launch_context
- Bot-Detection Test Guide — measure exposure, don't chase “Human”
- is_external_apply
- build_skills_report
- no_pauses
- build_slug_search_url
- Graphify — queryable knowledge graph of this repo
- 9. External repo survey (5 repos, verified Oct 2026)
- CollectRequest
- Gate definitions (the contract)
- 4. Method and data quality
- _prompt_manual_login

## God Nodes (most connected - your core abstractions)
1. `FakePage` - 129 edges
2. `FakeContext` - 59 edges
3. `Orchestrator` - 53 edges
4. `Job` - 52 edges
5. `EmailContact` - 50 edges
6. `upsert_jobs()` - 46 edges
7. `make_job()` - 42 edges
8. `Module responsibility matrix` - 42 edges
9. `RunRecord` - 37 edges
10. `run_scrape()` - 35 edges

## Surprising Connections (you probably didn't know these)
- `G4 — duplicates` --references--> `load_frame()`  [INFERRED]
  docs/SPEC-lane-job-quality-gates.md → src/export.py
- `Implementation update (2026-10-25)` --references--> `_expand_show_more()`  [INFERRED]
  docs/SPEC-linkedin-email-collector.md → src/linkedin_email_scraper.py
- `5.3 Modular monolith, CLI-first (no server, no microservices)` --references--> `do_scrape()`  [INFERRED]
  docs/CODE_EXPLANATION.md → src/main.py
- `6. R2 joeyism/linkedin_scraper — deep dive (stack twin)` --references--> `Job`  [INFERRED]
  docs/LINKEDIN_RESEARCH.md → src/models.py
- `3c. Job-domain (career) skills — pipeline-adjacent, not scraping` --references--> `ScrapeRun`  [INFERRED]
  docs/LINKEDIN_RESEARCH.md → src/models.py

## Import Cycles
- None detected.

## Communities (136 total, 7 thin omitted)

### Community 0 - "validate-coverage-ledger.cjs"
Cohesion: 0.12
Nodes (22): ATTEMPT_FIELDS, ATTEMPT_STATUSES, createErrorList(), fs, hasOwn(), hasValidSemanticFields(), hasValidUnicodeScalarValues(), hasVisibleProse() (+14 more)

### Community 1 - "Job"
Cohesion: 0.11
Nodes (17): 4. Code style (the conventions used everywhere), 5.5 Other architectural idioms, 6. Design patterns — GoF catalog (with file:line evidence), `models.py` — Layers 3+4, the data contract, `naukri_scraper.py` — Layer 2-live, the pipeline core, Non-GoF / idiomatic patterns used, 2. Module reference, Job (+9 more)

### Community 2 - "validate-findings.cjs"
Cohesion: 0.10
Nodes (40): canonicalKey(), append(), encode(), codePointLength(), collect(), collectDataLimitErrors(), collectFindingSemanticErrors(), collectSchemaErrors() (+32 more)

### Community 3 - "run_skills_scan"
Cohesion: 0.11
Nodes (17): run_skills_scan(), _stop(), test_run_skills_scan_cap_breaks_page_loop(), test_run_skills_scan_close_failure_swallowed(), test_run_skills_scan_full_flow(), test_run_skills_scan_search_error_continues(), test_run_skills_scan_stop_before_first_title(), test_run_skills_scan_stop_mid_pass_keeps_partial() (+9 more)

### Community 4 - "src/main.py"
Cohesion: 0.13
Nodes (13): 3. Endpoints (CLI commands — this app has no HTTP server), `config.py` — Layer 0, env-driven settings, Success Criteria, command, collect_emails(), _ensure_env(), export(), export_emails_cmd() (+5 more)

### Community 5 - "test_parser.py"
Cohesion: 0.13
Nodes (16): `parser.py` — Layer 2-offline, BS4 twin, _card_text(), _is_trap(), parse_detail_html(), parse_search_html(), _anchor(), test_card_text_none_card(), test_parse_detail_external_apply_wins_over_traps() (+8 more)

### Community 6 - "test_main.py"
Cohesion: 0.07
Nodes (17): _FakePW, test_collect_emails_checkpoint_skips_empty_and_duplicate_batches(), test_collect_emails_csv_end_to_end_writes_clean_deduped_workbook(), test_collect_emails_defaults_to_settings_domains(), test_collect_emails_empty_result_returns_zero(), test_collect_emails_reads_csv_targets_in_order(), test_collect_emails_upserts_exports_and_reports(), test_do_scrape_empty_returns_zero() (+9 more)

### Community 7 - "config.py"
Cohesion: 0.13
Nodes (9): _get(), _get_bool(), _get_float(), _get_int(), test_get_bool_variants(), test_get_float_valid_and_invalid(), test_get_int_valid_and_invalid(), test_get_returns_default_when_unset() (+1 more)

### Community 8 - "upsert_emails"
Cohesion: 0.15
Nodes (17): 11. Email collector — decision record (2026-10-23), count_emails(), get_session(), upsert_emails(), EmailRow, Phase 1: Foundation (data contract), Todo — LinkedIn Recruiter Email Collector (from tasks/plan.md, spec docs/SPEC-linkedin-email-collector.md), _contact() (+9 more)

### Community 9 - "LinkedIn Jobs Expansion — Deep Research"
Cohesion: 0.12
Nodes (16): 10. Fair-use note (extends README §5 to LinkedIn), 1. Link index (everything in one place), 2. awesome-agent-skills (S1) — how the catalog is organized, 3. Skills relevant to THIS project (checked hyperlink by hyperlink), 3a. Directly usable — browser automation / scraping, 3b. Usable as services (API, not browser) — discovery / enrichment, 3c. Job-domain (career) skills — pipeline-adjacent, not scraping, 4. awesome-agent-skills-mcp (S2/S3) — evaluation for this repo (+8 more)

### Community 10 - "AI, LLM, and Agent Hunting"
Cohesion: 0.20
Nodes (9): AI, LLM, and Agent Hunting, Context, retrieval, and memory attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), MCP and sub-agent trust classes (subagent_type: `general`), Output and disclosure attack classes (subagent_type: `general`), Tool and action attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+1 more)

### Community 12 - "test_web.py"
Cohesion: 0.06
Nodes (13): build_mcp(), api_job_to_raw(), RunNotCancellable, _FakePW, _isolated_logs(), _payload(), test_api_job_to_raw_mapping(), test_app_without_optional_deps() (+5 more)

### Community 13 - "setup_logging"
Cohesion: 0.15
Nodes (8): setup_logging(), _FakeSched, test_run_scheduled_handles_interrupt(), _factory(), test_run_scheduled_handles_system_exit(), _factory(), test_setup_logging_levels(), test_setup_logging_preserves_file_handlers()

### Community 14 - "confirmed"
Cohesion: 0.24
Nodes (17): Structured hunter result, Cost budget, Coverage and prior runs, Full audit planning, Full audit workflow, Run profiles and scope, confirmed(), evidence() (+9 more)

### Community 15 - "Project Document — Secure Naukri.com Jobs Collector"
Cohesion: 0.25
Nodes (8): 1. How it works (pipeline), 3. Configuration (`.env`, see `.env.example`), 4. Commands, 5. Data model, 6. Known environment notes (verified), 7. Fair use, 8. Knowledge graph (Graphify), Project Document — Secure Naukri.com Jobs Collector

### Community 16 - "Jobs Collector"
Cohesion: 0.14
Nodes (14): API & MCP sketch, Architecture, C#/.NET market snapshot (2026-10-26), Codebase stats (tokei), Configuration, Contributing, Docs, Fair use (+6 more)

### Community 17 - "export.py"
Cohesion: 0.15
Nodes (6): get_engine(), _resolve_url(), Base, JobRow, ScrapeRun, test_resolve_url_relative_absolute_and_server()

### Community 18 - "ops.py"
Cohesion: 0.13
Nodes (9): get_stats(), stats(), DbTable, DbTablePage, HealthOut, LogFile, SkillTop, StatsOut (+1 more)

### Community 19 - "api_collect_jobs"
Cohesion: 0.16
Nodes (22): api_collect_jobs(), api_scan_skills(), _api_job(), _api_params(), _down(), _Resp, test_api_collect_jobs_drops_external_apply_rows(), test_api_collect_jobs_drops_unwanted_rows() (+14 more)

### Community 20 - "Hardening Controls"
Cohesion: 0.05
Nodes (42): Broken Access Control, Broken Authentication, Cross-Site Scripting (XSS), Data Classification, Dependency Audit Triage, Destructive Operations on Derived Paths, File Upload Safety, Hardening Patterns (+34 more)

### Community 21 - "parse_domain_targets"
Cohesion: 0.13
Nodes (21): _clean_cell(), _domain(), DomainTarget, _embedded(), _flatten_row(), _neighbour_target(), parse_domain_targets(), test_bare_domains_use_default_target() (+13 more)

### Community 22 - "runlog.py"
Cohesion: 0.16
Nodes (9): _target(), attached_run_log(), list_log_files(), log_dir(), LogNotFound, read_log_file(), run_log_path(), test_read_log_file_rejects_bad_names() (+1 more)

### Community 23 - "create_app"
Cohesion: 0.11
Nodes (17): create_app(), RunNotFound, _blocking(), _failing(), _instant(), _run(), test_cancel_running_scrape_via_api(), test_collect_api_busy_and_validation() (+9 more)

### Community 24 - "agent-skills"
Cohesion: 0.10
Nodes (20): codemode, environment, timeout, type, LOG_LEVEL, SKILLS_CACHE_DIR, SKILLS_SYNC_INTERVAL, headers (+12 more)

### Community 25 - "ApiError"
Cohesion: 0.20
Nodes (5): get_job(), JobNotFound, ApiError, TableNotFound, test_get_job_found_and_missing()

### Community 26 - "Spec — Naukri key-skills scan"
Cohesion: 0.18
Nodes (11): 1. Goal, 2. Search URL shape, 3. DOM map (verified live 2026-10-26), 6. Gating and counting rules, 7. Verification snapshot (2026-10-26), 8. Test coverage, 9. Related market analysis, Home page (+3 more)

### Community 27 - "_on_login_wall"
Cohesion: 0.20
Nodes (7): Implementation note (2026-10-23), _on_login_wall(), _wait_for_login(), test_on_login_wall_detects_auth_redirect(), test_wait_for_login_gives_up_after_grace(), test_wait_for_login_true_when_already_signed_in(), test_wait_for_login_waits_until_wall_clears()

### Community 28 - "Agent Skills (OpenCode)"
Cohesion: 0.33
Nodes (5): Agent Skills (OpenCode), Core Rules, Execution Model, graphify, Intent → Skill Mapping

### Community 29 - "nkapi.py"
Cohesion: 0.16
Nodes (6): fetch_search_page(), generate_nkparam(), NkApiError, _public_key(), _read_der(), test_generate_nkparam_shape()

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
Cohesion: 0.10
Nodes (31): export_jobs(), _hyperlink_titles(), load_frame(), _seed(), _seed_backdated(), _seed_emails(), _seed_java(), _seed_quality_gates() (+23 more)

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
Cohesion: 0.15
Nodes (13): Anti-patterns, Core principles, Full audit setup, Operating modes, Platform terminology, Recommend the smallest effective source fix, Require a boundary and result, Respect source visibility (+5 more)

### Community 51 - "Code Simplification"
Cohesion: 0.12
Nodes (16): 1. Preserve Behavior Exactly, 2. Follow Project Conventions, 3. Prefer Clarity Over Cleverness, 4. Maintain Balance, 5. Scope to What Changed, Code Simplification, Common Rationalizations, Language-Specific Guidance (+8 more)

### Community 52 - "Debugging and Error Recovery"
Cohesion: 0.09
Nodes (21): Build Failure Triage, Common Rationalizations, Debugging and Error Recovery, Error-Specific Patterns, Instrumentation Guidelines, Overview, Red Flags, Runtime Error Triage (+13 more)

### Community 53 - "Spec: Lane Job-Quality Gates (irrelevant · pure-frontend · external-apply · dedupe)"
Cohesion: 0.18
Nodes (10): Boundaries, Code style, Objective, Open Questions, Project Structure (files touched), Run plan (after implementation, same session), Spec: Lane Job-Quality Gates (irrelevant · pure-frontend · external-apply · dedupe), Success Criteria (+2 more)

### Community 54 - "FakeContext"
Cohesion: 0.10
Nodes (16): 4. Live e-commerce test (Amazon.in + Flipkart), run_collect(), FakeContext, _sequence(), test_run_collect_continues_after_one_domain_and_respects_wall(), test_run_collect_defaults_from_settings(), test_run_collect_happy_path_content_only_and_dedupes(), test_run_collect_rejects_unknown_facet() (+8 more)

### Community 55 - "Interview Me"
Cohesion: 0.11
Nodes (18): Common Rationalizations, Example, Interaction with Other Skills, Interview Me, Loading Constraints, Output, Overview, Red Flags (+10 more)

### Community 56 - "Planning and Task Breakdown"
Cohesion: 0.11
Nodes (18): Common Rationalizations, Output Files, Overview, Parallelization Opportunities, Plan Document Template, Planning and Task Breakdown, Red Flags, See Also (+10 more)

### Community 57 - "handle_possible_block"
Cohesion: 0.10
Nodes (15): 9.1 Full data-flow (browser → DB → files), 9.1b Live network trace — measured session on naukri.com (2026-09-19), 9.2 Class / data-model diagram, 9.3 Database ER, 9.4 Module dependency graph, 9.5 Browser-launch decision flow, 9.6 Bot-wall / politeness state, 9. Mermaid diagrams (detail) (+7 more)

### Community 58 - "Security Checklist"
Cohesion: 0.11
Nodes (17): AI / LLM Security, Authentication, Authorization, CORS Configuration, Data Protection, Dependency Security, Destructive Path Operations, Error Handling (+9 more)

### Community 59 - "ReOrder: Keep Your Regulars Ordering Direct"
Cohesion: 0.11
Nodes (17): Example 1: Vague Early-Stage Concept (Full 3-Phase Session), Example 2: Feature Idea Within an Existing Product (Codebase-Aware), Example 3: Process/Workflow Idea (Non-Product), Ideation Session Examples, Key Assumptions to Validate, MVP Scope, Not Doing (and Why), Open Questions (+9 more)

### Community 60 - "Idea Refine"
Cohesion: 0.11
Nodes (17): Anti-patterns to Avoid, Common Rationalizations, Detailed Instructions, How It Works, Idea Refine, Output, Overview, Phase 1: Understand & Expand (Divergent) (+9 more)

### Community 61 - "5. Test matrix (automated ↔ manual)"
Cohesion: 0.12
Nodes (8): 1. Practice progression (manual, in order), 2. Automated suite (this repo), 3. Live practice runs (this repo, Chrome-only stack), 5. Test matrix (automated ↔ manual), Testing Guide — practice progression + automated suite, _dismiss_flipkart_login(), Product, scrape_site()

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

### Community 66 - "test_stealth.py"
Cohesion: 0.06
Nodes (23): _extension_args(), fake_playwright(), FakeBrowserType, FakeKeyboard, FakeLocator, FakeMouse, FakeRoute, _handler() (+15 more)

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
Cohesion: 0.06
Nodes (23): LIMITS, archivedAttempt(), assert, fs, {
  LIMITS,
  canonicalCoverageId,
  encodeCanonicalRef,
  isSafeAgentId,
  isSafeRelativePath,
  preflightJsonText,
  validateDocument,
}, localCheck(), os, path (+15 more)

### Community 76 - "Cloud and Deployment Hunting"
Cohesion: 0.20
Nodes (10): Cloud and Deployment Hunting, Configuration and secret lifecycle attack classes (subagent_type: `general`), Container and orchestration attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Ingress, network, and control-plane attack classes (subagent_type: `general`), Managed storage, events, and edge attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+2 more)

### Community 77 - "test_scraper.py"
Cohesion: 0.11
Nodes (17): _keep(), should_exclude_java_job(), test_build_search_url_encodes_params(), test_coerce_job_valid_and_dropped(), test_normalize_raw_camel_and_snake_shapes(), test_safe_goto_retries_playwright_timeout_error(), test_safe_goto_retries_then_reraises(), test_safe_goto_success() (+9 more)

### Community 78 - "linkedin_email_scraper.py"
Cohesion: 0.10
Nodes (15): _body_text(), _check_bot_wall(), _results_ui_ready(), _snippet_around(), _submit_search(), _wait_for_results(), test_body_text_returns_visible_text_and_swallows_errors(), test_check_bot_wall_detects_captcha_and_search_pause() (+7 more)

### Community 79 - "orchestrator.py"
Cohesion: 0.12
Nodes (18): company_mode(), browser_scan_skills(), default_export_runner(), default_skills_runner(), render_skills_text(), RunRecord, _force_browser_fallback(), test_default_export_runner_writes_files() (+10 more)

### Community 80 - "Page"
Cohesion: 0.13
Nodes (14): _collect_view(), _count_posts(), _scroll_to_bottom(), _wheel_feed(), test_collect_view_breaks_on_empty_feed_and_zero_rounds(), test_collect_view_growth_without_checkpoint_and_final_extract(), test_collect_view_reaches_target_after_scroll(), test_collect_view_stops_after_three_stalls() (+6 more)

### Community 81 - "practice_tests.py"
Cohesion: 0.16
Nodes (5): crawl_books(), _get_with_retry(), main(), Reporter, store_books()

### Community 82 - "Data Isolation and Lifecycle Hunting"
Cohesion: 0.20
Nodes (9): Core discipline (include in every agent prompt for this domain), Data Isolation and Lifecycle Hunting, Deletion, revocation, and lifecycle attack classes (subagent_type: `general`), Derived-data and disclosure attack classes (subagent_type: `general`), Export, backup, restore, and migration attack classes (subagent_type: `general`), Tenant and object-isolation attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+1 more)

### Community 84 - "test_email_collector.py"
Cohesion: 0.13
Nodes (19): build_all_search_url(), build_content_search_url(), _contacts_from_cards(), extract_emails(), test_build_all_search_url_shape(), test_build_content_search_url_all_time(), test_build_content_search_url_rejects_unknown_facet(), test_build_content_search_url_shape() (+11 more)

### Community 85 - "Desktop, Mobile, and Local IPC Hunting"
Cohesion: 0.20
Nodes (10): Application-state and device-lifecycle attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Deep-link, callback, and navigation attack classes (subagent_type: `general`), Desktop, Mobile, and Local IPC Hunting, Local IPC and exported-component attack classes (subagent_type: `general`), Privileged-helper and local-file attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+2 more)

### Community 86 - "naukri_scraper.py"
Cohesion: 0.15
Nodes (9): extract_listing_cards(), _first_match(), human_scroll(), _list_state(), _pick_option(), submit_searchbar(), test_human_scroll_mouse_failure_falls_back(), test_human_scroll_wheels_and_wiggles() (+1 more)

### Community 87 - "collectUnitErrors"
Cohesion: 0.25
Nodes (20): canonicalCoverageId(), collectUnitErrors(), encodeCanonicalRef(), escapeUnsafeDiagnosticCharacters(), isCanonicalRef(), isObject(), isOwnedArtifactPath(), isSafeAgentId() (+12 more)

### Community 88 - "Memory Safety, Binary, and Kernel Hunting"
Cohesion: 0.18
Nodes (10): Binary loading and runtime attack classes (subagent_type: `general`), Bounds, integer, and representation attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), FFI and ABI attack classes (subagent_type: `general`), Kernel and privileged-interface attack classes (subagent_type: `general`), Lifetime, type, and concurrency attack classes (subagent_type: `general`), Memory Safety, Binary, and Kernel Hunting, Universal moves (apply across the above) (+2 more)

### Community 89 - "Protocols, RPC, and Messaging Hunting"
Cohesion: 0.20
Nodes (9): Broker and queue isolation attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Framing, schema, and interpretation attack classes (subagent_type: `general`), Protocols, RPC, and Messaging Hunting, Replay, ordering, and transaction attack classes (subagent_type: `general`), RPC identity and authorization attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+1 more)

### Community 90 - "Full Code Explanation — Secure Naukri.com Jobs Collector"
Cohesion: 0.22
Nodes (7): 10. Testing architecture (why 100% is feasible), 11. Knowledge graph + living docs, 12. Fair use (binding), 1. Project structure (where everything lives), 8. Dependencies (why each exists), Full Code Explanation — Secure Naukri.com Jobs Collector, fresh_db()

### Community 91 - "Resource Exhaustion and Availability Hunting"
Cohesion: 0.20
Nodes (9): Computational amplification attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Failure and recovery attack classes (subagent_type: `general`), Quota and scheduling attack classes (subagent_type: `general`), Resource accumulation attack classes (subagent_type: `general`), Resource Exhaustion and Availability Hunting, Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+1 more)

### Community 92 - "HTTP-Protocol and Authentication Hunting"
Cohesion: 0.20
Nodes (10): API-key and mTLS attack classes (subagent_type: `general`), Browser-session attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Federated-identity attack classes (subagent_type: `general`), HTTP framing and cache attack classes (subagent_type: `general`), HTTP-Protocol and Authentication Hunting, MFA, passkey, and account-transition attack classes (subagent_type: `general`), Universal moves (apply across the above) (+2 more)

### Community 93 - "Vulnerability Hunting"
Cohesion: 0.22
Nodes (9): Core hunting method — include in every hunter prompt, Core validation rules — include in every hunter prompt, Coverage-critic waves, Local validation boundaries, Parent consolidation and ledger update, Phase 2: Run coverage-led hunting waves, Promotion procedure — copy this promotion procedure verbatim into every hunter prompt, Required hunter prompt (+1 more)

### Community 94 - "Supply Chain and Release Hunting"
Cohesion: 0.22
Nodes (8): CI and automation attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Dependency and build-input attack classes (subagent_type: `general`), Release and update attack classes (subagent_type: `general`), Supply Chain and Release Hunting, Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here), When to use this file

### Community 95 - "_posted_timestamp"
Cohesion: 0.15
Nodes (11): _email_domain(), _latest_email_frame(), _naive_timestamp(), _posted_timestamp(), test_email_domain_and_naive_timestamp_helpers(), test_latest_email_frame_empty_input_returns_empty(), test_posted_timestamp_fallbacks_never_raise(), test_posted_timestamp_handles_missing_reference_and_timezone() (+3 more)

### Community 96 - "Daily Lanes Runbook — fresh apply-links Excel, every morning"
Cohesion: 0.20
Nodes (9): 0. Start the server (once per day), 1. The two lanes (exact criteria — do not improvise), 1b. Pure-Java exclusion (always on), 2. Collect (API path, ~25s per lane, no browser), 3. Export the Excel (titles are real hyperlinks), 4. Sanity checks (2 minutes), 5. Changing the recipe, Daily Lanes Runbook — fresh apply-links Excel, every morning (+1 more)

### Community 97 - "ATTACK-CLASSES.md"
Cohesion: 0.15
Nodes (5): Architecture summary and companion selection, Deterministic coverage ledger, Phase 1: Map the source and plan coverage, Prior-run input, Reconnaissance

### Community 98 - "Phase 6: Produce target-neutral reports from final records"
Cohesion: 0.50
Nodes (4): `FINDINGS-DETAIL.md`, `NEEDS-VALIDATION.md`, Phase 6: Produce target-neutral reports from final records, `REPORT.md`

### Community 99 - "Spec: LinkedIn Recruiter Email Collector"
Cohesion: 0.11
Nodes (17): Boundaries, Code Style, Commands, Data contract, Decisions already made (clarification round, 2026-10-23), Design, Fair use (extends LINKEDIN_RESEARCH §10), Implementation update (2026-10-25) (+9 more)

### Community 100 - "Task List"
Cohesion: 0.18
Nodes (10): Architecture Decisions, Checkpoint: Complete, Checkpoint: Core, Checkpoint: Foundation, Implementation Plan: LinkedIn Recruiter Email Collector, Open Questions, Overview, Phase 3: CLI + polish (+2 more)

### Community 101 - "table_rows"
Cohesion: 0.12
Nodes (8): list_tables(), table_rows(), db_table(), db_tables(), health(), log_tail(), logs(), test_db_explorer_tables_and_rows()

### Community 102 - "FakePage"
Cohesion: 0.10
Nodes (14): _open_feed(), _open_posts_view(), FakePage, test_open_feed_handles_non_transient_navigation_error(), test_open_feed_logs_in_then_tolerates_reopen_error(), test_open_feed_stops_if_bounced_back_to_wall_after_login(), test_open_feed_stops_when_login_never_completes(), test_open_feed_stops_when_signed_out_and_noninteractive() (+6 more)

### Community 104 - "EmailContact"
Cohesion: 0.11
Nodes (10): EmailContact, _fake_extract(), test_email_contact_defaults_are_empty(), test_email_contact_normalises_email_and_snippet(), test_email_contact_rejects_malformed_email(), test_email_contact_snippet_capped(), test_emailrow_round_trip(), test_job_rejects_short_title_and_id() (+2 more)

### Community 105 - "_click_next_page"
Cohesion: 0.18
Nodes (8): 9. Recommended LinkedIn plan for this repo, 4. Pagination bug and fix (2026-10-26), Key-skills scan (API fast path + browser fallback), _click_next_page(), test_click_next_page_and_list_state_survive_detached_dom(), test_click_next_page_returns_false_without_enabled_control(), test_click_next_page_times_out_when_range_never_changes(), test_click_next_page_waits_for_range_change()

### Community 106 - "run_scrape"
Cohesion: 0.28
Nodes (13): run_scrape(), raw_card(), test_run_scrape_cap_breaks_next_page_loop(), test_run_scrape_close_failure_swallowed(), test_run_scrape_excludes_java_revealed_by_enrichment(), test_run_scrape_full_flow(), test_run_scrape_no_enrich_and_cap(), test_run_scrape_search_error_continues() (+5 more)

### Community 107 - "Naukri market snapshot — C#/.NET (2026-10-26)"
Cohesion: 0.18
Nodes (11): 1. Top 10 key skills, 2. Top 10 job titles, 3. What the .NET role market looks like, 5. Reproduce, 6. Artifacts, 7. Refresh log, Naukri market snapshot — C#/.NET (2026-10-26), Roles lens (+3 more)

### Community 108 - "Module responsibility matrix"
Cohesion: 0.17
Nodes (7): `main.py` — shell, front door, Module responsibility matrix, Settings, do_scrape(), _print_jobs(), run_scheduled(), test_config_log_dir_default()

### Community 109 - "upsert_jobs"
Cohesion: 0.10
Nodes (24): 2. Start point (how the app boots), 5.1 Layered architecture (the backbone), 5.2 ETL / pipeline pattern, 5.3 Modular monolith, CLI-first (no server, no microservices), 5.4 Repository / DAO (data-access encapsulation), 5. Architecture patterns, 7. Module-by-module explanation, `db.py` — Layer 4, repository (+16 more)

### Community 110 - "preflightJsonText"
Cohesion: 0.40
Nodes (11): JsonStructureError, preflightJsonText(), beginContainer(), beginString(), beginValue(), closeContainer(), countValue(), currentContainer() (+3 more)

### Community 111 - "stealth_browser.py"
Cohesion: 0.17
Nodes (5): main(), probe(), main(), _login_wait(), main()

### Community 112 - "Orchestrator"
Cohesion: 0.08
Nodes (16): BusyError, Orchestrator, cancel(), download(), get_one(), list_all(), start_collect(), start_export() (+8 more)

### Community 113 - "jobs.py"
Cohesion: 0.24
Nodes (4): list_jobs(), get_one(), list_all(), JobsPage

### Community 114 - "Conventional Commits"
Cohesion: 0.33
Nodes (5): Conventional Commits, Examples, Format, Rules, Types

### Community 115 - "_BrokenPage"
Cohesion: 0.13
Nodes (11): _expand_show_more(), _extract_fresh(), _show_filter_results(), _BrokenPage, test_expand_show_more_clicks_and_waits(), test_expand_show_more_swallows_errors(), test_extract_fresh_dedupes_and_updates_email_set(), test_extract_fresh_survives_extractor_error_without_hook() (+3 more)

### Community 116 - "make_job"
Cohesion: 0.15
Nodes (14): enrich_job(), job_should_exclude(), make_job(), test_enrich_job_empty_apply_url_falls_back_to_job_url(), test_enrich_job_ignores_unknown_detail_keys(), test_enrich_job_merges_detail(), test_enrich_job_timeout_returns_original(), test_enrich_job_unexpected_error_returns_original() (+6 more)

### Community 117 - "Web Control Plane — Spec + Guide"
Cohesion: 0.15
Nodes (11): Architecture (FastAPI bigger-applications shape), Boundaries, Contract (every action has a cancel twin), Evidence (verify-before-claim), MCP tools (curated) + optional harness wiring, Objective, Run logs, Sources (source-driven-development) (+3 more)

### Community 118 - "_apply_content_filters"
Cohesion: 0.17
Nodes (9): _apply_content_filters(), _click_filter_button(), _select_filter_radio(), test_apply_content_filters_happy_path_applies_sort_and_date(), test_apply_content_filters_radio_and_show_results_failures(), test_apply_content_filters_reports_missing_controls(), test_apply_content_filters_without_date(), test_click_filter_button_branches() (+1 more)

### Community 119 - "load_email_frame"
Cohesion: 0.18
Nodes (9): _dedupe(), load_email_frame(), _seed_mixed_emails(), test_email_export_domain_falls_back_to_keyword(), test_email_export_drops_other_domains_and_keeps_latest_post(), test_email_export_ignores_rows_without_any_domain(), test_email_export_limit_applies_after_dedupe(), test_email_export_returns_columns_when_all_rows_are_mismatched() (+1 more)

### Community 120 - "human_pause"
Cohesion: 0.33
Nodes (3): human_pause(), api_pause(), test_api_pause_uses_jobspy_window()

### Community 121 - "Tokei — count your code, quickly"
Cohesion: 0.22
Nodes (9): Basic usage, Common issue, Excluding folders, File statistics, Output formats, Reading stored output, Sorting output, Tokei — count your code, quickly (+1 more)

### Community 122 - "The Simplification Process"
Cohesion: 0.25
Nodes (8): Step 1: Understand Before Touching (Chesterton's Fence), Step 2: Identify Simplification Opportunities, Step 3: Apply Changes Incrementally, Step 4: Verify the Result, The Simplification Process, Attack Classes, Attack classes — choose and split based on Phase 1, url()

### Community 123 - "launch_context"
Cohesion: 0.16
Nodes (8): export_emails(), do_collect_emails(), _persist(), _launch_chromium(), launch_context(), launch_playwright(), _maybe_block_ads(), Phase 2: Core collector

### Community 124 - "Bot-Detection Test Guide — measure exposure, don't chase “Human”"
Cohesion: 0.17
Nodes (12): 1. Sites (comparison order), 2. Procedure — Test A/B/C matrix, 3. Signal table (fill from your runs), 4. Reading the results, 5. Fix applied from these measurements (2026-09-19), 6.1 BotD source checks vs our implementation, 6.2 Critical finding — the init script was inert, 6.3 CrowdSec — network/application layer (+4 more)

### Community 125 - "is_external_apply"
Cohesion: 0.25
Nodes (6): 1c. Lane-quality gates (always on — irrelevant / frontend / portal / dupes), 9.5 Traverser25/NopeRi (~88 stars, self-reports working Jul 2026), Lane collection → Excel with hyperlinks, fresh_cutoff(), is_external_apply(), test_is_external_apply_signals()

### Community 127 - "build_skills_report"
Cohesion: 0.25
Nodes (6): 5. Code map, build_skills_report(), SkillsRequest, test_build_skills_report_counts_postings_once(), test_build_skills_report_empty(), test_build_skills_report_unknown_company()

### Community 129 - "build_slug_search_url"
Cohesion: 0.25
Nodes (6): build_slug_search_url(), slugify_keywords(), test_build_slug_search_url_empty_location_falls_back_to_india(), test_build_slug_search_url_mirrors_manual(), test_build_slug_search_url_multi_location_uses_first_city_in_path(), test_slugify_matches_manual_search()

### Community 130 - "Graphify — queryable knowledge graph of this repo"
Cohesion: 0.29
Nodes (4): Artifacts (`graphify-out/`, committed), Graphify — queryable knowledge graph of this repo, Repo wiring, Usage (no API key needed for code)

### Community 131 - "9. External repo survey (5 repos, verified Oct 2026)"
Cohesion: 0.33
Nodes (6): 9.1 speedyapply/JobSpy (~4.5k stars, MIT, `pip install python-jobspy`), 9.2 lordzohar/Naukri-autoapply-bot (~61 stars, educational), 9.3 navchandar/Naukri (~93 stars, GPL-3.0), 9.4 ankitbaghel01/naukri_update (~83 stars, Node.js 18+, Windows), 9.6 Adoption map for our collector (read-side stays, write-side optional), 9. External repo survey (5 repos, verified Oct 2026)

### Community 132 - "CollectRequest"
Cohesion: 0.40
Nodes (4): Flag, CollectRequest, ExportRequest, test_collect_and_export_requests_gate_defaults()

### Community 133 - "Gate definitions (the contract)"
Cohesion: 0.40
Nodes (5): G1 — relevance (kills mixed / unrelated results), G2 — pure frontend, G3 — external apply (company-portal redirect), G4 — duplicates, Gate definitions (the contract)

### Community 134 - "4. Method and data quality"
Cohesion: 0.50
Nodes (4): 4. Method and data quality, Caveats, Roles lens, Skills lens

## Knowledge Gaps
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Attack classes — choose and split based on Phase 1` connect `The Simplification Process` to `_click_next_page`, `confirmed`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `FakePage` (e.g. with `10. Testing architecture (why 100% is feasible)` and `This repo's map (from `GRAPH_REPORT.md`)`) actually correct?**
  _`FakePage` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `validate-coverage-ledger.cjs` be split into smaller, more focused modules?**
  _Cohesion score 0.12318840579710146 - nodes in this community are weakly interconnected._
- **Why does `confirmed()` connect `confirmed` to `ATTACK-CLASSES.md`, `Client-Side and Browser Hunting`, `AI, LLM, and Agent Hunting`, `validate-findings.test.cjs`, `Cloud and Deployment Hunting`, `Data Isolation and Lifecycle Hunting`, `Security Audit`, `Desktop, Mobile, and Local IPC Hunting`, `Memory Safety, Binary, and Kernel Hunting`, `Protocols, RPC, and Messaging Hunting`, `The Simplification Process`, `Resource Exhaustion and Availability Hunting`, `HTTP-Protocol and Authentication Hunting`, `Vulnerability Hunting`, `Supply Chain and Release Hunting`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `FakeContext` (e.g. with `4. Code style (the conventions used everywhere)` and `4. Live e-commerce test (Amazon.in + Flipkart)`) actually correct?**
  _`FakeContext` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `Job` be split into smaller, more focused modules?**
  _Cohesion score 0.11491935483870967 - nodes in this community are weakly interconnected._
- **Why does `FakePage` connect `FakePage` to `run_skills_scan`, `LinkedIn Jobs Expansion — Deep Research`, `test_web.py`, `_on_login_wall`, `FakeContext`, `handle_possible_block`, `5. Test matrix (automated ↔ manual)`, `test_stealth.py`, `test_scraper.py`, `linkedin_email_scraper.py`, `orchestrator.py`, `Page`, `test_email_collector.py`, `naukri_scraper.py`, `Full Code Explanation — Secure Naukri.com Jobs Collector`, `_click_next_page`, `run_scrape`, `upsert_jobs`, `_BrokenPage`, `make_job`, `_apply_content_filters`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._