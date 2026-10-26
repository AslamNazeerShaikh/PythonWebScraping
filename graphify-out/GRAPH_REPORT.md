# Graph Report - PythonWebScraping  (2026-10-26)

## Corpus Check
- 124 files · ~176,560 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .example 1)

## Summary
- 2434 nodes · 4640 edges · 121 communities (115 shown, 6 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 515 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cf53697b`
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
- db.py
- setup_logging
- confirmed
- Project Document — Secure Naukri.com Jobs Collector
- Jobs Collector
- naukri_scraper.py
- conftest.py
- build_mcp
- Hardening Controls
- parse_domain_targets
- schemas.py
- create_app
- agent-skills
- orchestrator.py
- Web Control Plane — Spec + Guide
- scrape_site
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
- test_scraper.py
- Security Checklist
- ReOrder: Keep Your Regulars Ordering Direct
- Idea Refine
- launch_context
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
- run_scrape
- linkedin_email_scraper.py
- test_web.py
- 4. Code style (the conventions used everywhere)
- practice_tests.py
- Data Isolation and Lifecycle Hunting
- idea-refine.sh
- test_email_collector.py
- Desktop, Mobile, and Local IPC Hunting
- Testing Guide — practice progression + automated suite
- FakePage
- Memory Safety, Binary, and Kernel Hunting
- Protocols, RPC, and Messaging Hunting
- Full Code Explanation — Secure Naukri.com Jobs Collector
- Resource Exhaustion and Availability Hunting
- HTTP-Protocol and Authentication Hunting
- Vulnerability Hunting
- Supply Chain and Release Hunting
- export.py
- Daily Lanes Runbook — fresh apply-links Excel, every morning
- ATTACK-CLASSES.md
- Phase 6: Produce target-neutral reports from final records
- Spec: LinkedIn Recruiter Email Collector
- Task List
- 9. Mermaid diagrams (detail)
- _on_login_wall
- _FakeSched
- EmailContact
- _click_next_page
- build_slug_search_url
- load_frame
- FakeLocator
- upsert_jobs
- collectUnitErrors
- _maybe_block_ads
- Orchestrator
- preflightJsonText
- Conventional Commits
- _BrokenPage
- build_skills_report
- FakeBrowserType
- Page
- load_email_frame
- human_pause

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

## Communities (121 total, 6 thin omitted)

### Community 0 - "validate-coverage-ledger.cjs"
Cohesion: 0.12
Nodes (22): ATTEMPT_FIELDS, ATTEMPT_STATUSES, createErrorList(), fs, hasOwn(), hasValidSemanticFields(), hasValidUnicodeScalarValues(), hasVisibleProse() (+14 more)

### Community 1 - "Job"
Cohesion: 0.12
Nodes (16): 6. Design patterns — GoF catalog (with file:line evidence), `models.py` — Layers 3+4, the data contract, Non-GoF / idiomatic patterns used, Job, JobRow, fresh_db(), test_email_contact_defaults_are_empty(), test_email_contact_normalises_email_and_snippet() (+8 more)

### Community 2 - "validate-findings.cjs"
Cohesion: 0.10
Nodes (40): canonicalKey(), append(), encode(), codePointLength(), collect(), collectDataLimitErrors(), collectFindingSemanticErrors(), collectSchemaErrors() (+32 more)

### Community 3 - "run_skills_scan"
Cohesion: 0.14
Nodes (14): run_skills_scan(), submit_searchbar(), test_run_skills_scan_cap_breaks_page_loop(), test_run_skills_scan_close_failure_swallowed(), test_run_skills_scan_search_error_continues(), test_run_skills_scan_stop_mid_pass_keeps_partial(), test_run_skills_scan_stops_when_next_page_is_absent(), test_run_skills_scan_zero_pages_returns_empty_report() (+6 more)

### Community 4 - "src/main.py"
Cohesion: 0.11
Nodes (15): `config.py` — Layer 0, env-driven settings, `main.py` — shell, front door, Success Criteria, command, collect_emails(), _ensure_env(), export(), export_emails_cmd() (+7 more)

### Community 5 - "test_parser.py"
Cohesion: 0.13
Nodes (15): `parser.py` — Layer 2-offline, BS4 twin, _card_text(), _is_trap(), parse_detail_html(), _anchor(), test_card_text_none_card(), test_parse_detail_external_apply_wins_over_traps(), test_parse_detail_internal_apply_keeps_canonical() (+7 more)

### Community 6 - "test_main.py"
Cohesion: 0.07
Nodes (17): _FakePW, test_collect_emails_checkpoint_skips_empty_and_duplicate_batches(), test_collect_emails_csv_end_to_end_writes_clean_deduped_workbook(), test_collect_emails_defaults_to_settings_domains(), test_collect_emails_empty_result_returns_zero(), test_collect_emails_reads_csv_targets_in_order(), test_collect_emails_upserts_exports_and_reports(), test_do_scrape_empty_returns_zero() (+9 more)

### Community 7 - "config.py"
Cohesion: 0.11
Nodes (11): _get(), _get_bool(), _get_float(), _get_int(), Settings, test_get_bool_variants(), test_get_float_valid_and_invalid(), test_get_int_valid_and_invalid() (+3 more)

### Community 8 - "upsert_emails"
Cohesion: 0.14
Nodes (20): 11. Email collector — decision record (2026-10-23), count_emails(), get_engine(), get_session(), _resolve_url(), upsert_emails(), do_collect_emails(), EmailRow (+12 more)

### Community 9 - "LinkedIn Jobs Expansion — Deep Research"
Cohesion: 0.12
Nodes (16): 10. Fair-use note (extends README §5 to LinkedIn), 1. Link index (everything in one place), 2. awesome-agent-skills (S1) — how the catalog is organized, 3. Skills relevant to THIS project (checked hyperlink by hyperlink), 3a. Directly usable — browser automation / scraping, 3b. Usable as services (API, not browser) — discovery / enrichment, 3c. Job-domain (career) skills — pipeline-adjacent, not scraping, 4. awesome-agent-skills-mcp (S2/S3) — evaluation for this repo (+8 more)

### Community 10 - "AI, LLM, and Agent Hunting"
Cohesion: 0.20
Nodes (9): AI, LLM, and Agent Hunting, Context, retrieval, and memory attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), MCP and sub-agent trust classes (subagent_type: `general`), Output and disclosure attack classes (subagent_type: `general`), Tool and action attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+1 more)

### Community 12 - "db.py"
Cohesion: 0.12
Nodes (7): Base, get_job(), JobNotFound, list_jobs(), get_one(), list_all(), test_list_jobs_filters_and_paginates()

### Community 13 - "setup_logging"
Cohesion: 0.14
Nodes (5): setup_logging(), company_mode(), browser_scan_skills(), test_setup_logging_levels(), test_setup_logging_preserves_file_handlers()

### Community 14 - "confirmed"
Cohesion: 0.24
Nodes (16): Structured hunter result, Cost budget, Coverage and prior runs, Full audit planning, Run profiles and scope, confirmed(), evidence(), needsValidation() (+8 more)

### Community 15 - "Project Document — Secure Naukri.com Jobs Collector"
Cohesion: 0.09
Nodes (20): Artifacts (`graphify-out/`, committed), Graphify — queryable knowledge graph of this repo, Repo wiring, This repo's map (from `GRAPH_REPORT.md`), Usage (no API key needed for code), 1. How it works (pipeline), 3. Configuration (`.env`, see `.env.example`), 4. Commands (+12 more)

### Community 16 - "Jobs Collector"
Cohesion: 0.08
Nodes (24): 1. Sites (comparison order), 2. Procedure — Test A/B/C matrix, 3. Signal table (fill from your runs), 4. Reading the results, 5. Fix applied from these measurements (2026-09-19), 6.1 BotD source checks vs our implementation, 6.2 Critical finding — the init script was inert, 6.3 CrowdSec — network/application layer (+16 more)

### Community 17 - "naukri_scraper.py"
Cohesion: 0.09
Nodes (15): _keep(), _first_match(), job_should_exclude(), _pick_option(), should_exclude_java_job(), slugify_keywords(), test_job_should_exclude_wraps_job(), test_pick_option_exact_substring_and_miss() (+7 more)

### Community 18 - "conftest.py"
Cohesion: 0.11
Nodes (4): FakeKeyboard, FakeMouse, FakeRoute, test_human_scroll_mouse_failure_falls_back()

### Community 19 - "build_mcp"
Cohesion: 0.14
Nodes (10): get_stats(), build_mcp(), collector_stats(), _payload(), test_app_without_optional_deps(), test_get_stats_empty_and_seeded(), test_mcp_read_tools(), test_mcp_start_and_cancel() (+2 more)

### Community 20 - "Hardening Controls"
Cohesion: 0.05
Nodes (42): Broken Access Control, Broken Authentication, Cross-Site Scripting (XSS), Data Classification, Dependency Audit Triage, Destructive Operations on Derived Paths, File Upload Safety, Hardening Patterns (+34 more)

### Community 21 - "parse_domain_targets"
Cohesion: 0.13
Nodes (22): _clean_cell(), _domain(), DomainTarget, _embedded(), _flatten_row(), _neighbour_target(), parse_domain_targets(), test_bare_domains_use_default_target() (+14 more)

### Community 22 - "schemas.py"
Cohesion: 0.10
Nodes (15): Flag, 5. Code map, CollectRequest, DbTable, DbTablePage, ExportRequest, HealthOut, JobsPage (+7 more)

### Community 23 - "create_app"
Cohesion: 0.09
Nodes (20): create_app(), _mount_scalar(), RunNotFound, _blocking(), _failing(), _instant(), _run(), _isolated_logs() (+12 more)

### Community 24 - "agent-skills"
Cohesion: 0.10
Nodes (20): codemode, environment, timeout, type, LOG_LEVEL, SKILLS_CACHE_DIR, SKILLS_SYNC_INTERVAL, headers (+12 more)

### Community 25 - "orchestrator.py"
Cohesion: 0.05
Nodes (21): list_tables(), table_rows(), get_orchestrator(), ApiError, TableNotFound, db_table(), db_tables(), log_tail() (+13 more)

### Community 26 - "Web Control Plane — Spec + Guide"
Cohesion: 0.08
Nodes (20): 1. Goal, 2. Search URL shape, 3. DOM map (verified live 2026-10-26), 6. Gating and counting rules, 7. Verification snapshot (2026-10-26), 8. Test coverage, Home page, Job detail page (+12 more)

### Community 27 - "scrape_site"
Cohesion: 0.22
Nodes (3): _dismiss_flipkart_login(), Product, scrape_site()

### Community 28 - "Agent Skills (OpenCode)"
Cohesion: 0.33
Nodes (5): Agent Skills (OpenCode), Core Rules, Execution Model, graphify, Intent → Skill Mapping

### Community 29 - "nkapi.py"
Cohesion: 0.13
Nodes (8): api_pause(), fetch_search_page(), generate_nkparam(), NkApiError, _public_key(), _read_der(), test_api_pause_uses_jobspy_window(), test_generate_nkparam_shape()

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
Cohesion: 0.11
Nodes (27): export_jobs(), _hyperlink_titles(), make_job(), _seed(), _seed_backdated(), _seed_emails(), _seed_java(), _seed_search_locations() (+19 more)

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
Cohesion: 0.11
Nodes (16): 1c. Lane-quality gates (always on — irrelevant / frontend / portal / dupes), Testing Strategy, Lane collection → Excel with hyperlinks, _external_apply_url(), fresh_cutoff(), _keep_wanted(), _gate_blob(), job_should_exclude_unwanted() (+8 more)

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
Nodes (22): 1. Preserve Behavior Exactly, 2. Follow Project Conventions, 3. Prefer Clarity Over Cleverness, 4. Maintain Balance, 5. Scope to What Changed, Code Simplification, Common Rationalizations, Language-Specific Guidance (+14 more)

### Community 52 - "Debugging and Error Recovery"
Cohesion: 0.09
Nodes (21): Build Failure Triage, Common Rationalizations, Debugging and Error Recovery, Error-Specific Patterns, Instrumentation Guidelines, Overview, Red Flags, Runtime Error Triage (+13 more)

### Community 53 - "Spec: Lane Job-Quality Gates (irrelevant · pure-frontend · external-apply · dedupe)"
Cohesion: 0.12
Nodes (15): Boundaries, Code style, G1 — relevance (kills mixed / unrelated results), G2 — pure frontend, G3 — external apply (company-portal redirect), G4 — duplicates, Gate definitions (the contract), Objective (+7 more)

### Community 54 - "FakeContext"
Cohesion: 0.10
Nodes (16): 4. Live e-commerce test (Amazon.in + Flipkart), run_collect(), FakeContext, _sequence(), test_run_collect_continues_after_one_domain_and_respects_wall(), test_run_collect_defaults_from_settings(), test_run_collect_happy_path_content_only_and_dedupes(), test_run_collect_rejects_unknown_facet() (+8 more)

### Community 55 - "Interview Me"
Cohesion: 0.11
Nodes (18): Common Rationalizations, Example, Interaction with Other Skills, Interview Me, Loading Constraints, Output, Overview, Red Flags (+10 more)

### Community 56 - "Planning and Task Breakdown"
Cohesion: 0.11
Nodes (18): Common Rationalizations, Output Files, Overview, Parallelization Opportunities, Plan Document Template, Planning and Task Breakdown, Red Flags, See Also (+10 more)

### Community 57 - "test_scraper.py"
Cohesion: 0.08
Nodes (20): enrich_job(), test_build_search_url_encodes_params(), test_check_bot_wall_clean_and_blocked(), test_check_bot_wall_evaluate_failure_is_safe(), test_enrich_job_empty_apply_url_falls_back_to_job_url(), test_enrich_job_ignores_unknown_detail_keys(), test_enrich_job_merges_detail(), test_enrich_job_timeout_returns_original() (+12 more)

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
Cohesion: 0.15
Nodes (7): `stealth_browser.py` — Layer 1, Chromium launcher, main(), probe(), main(), _login_wait(), main(), launch_context()

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
Cohesion: 0.16
Nodes (19): _extension_args(), _launch_chromium(), fake_playwright(), _handler(), test_blocker_aborts_trackers_pixels_and_continues_rest(), test_blocker_disabled_registers_nothing(), test_extension_args_headed_load(), test_extension_args_missing_dir() (+11 more)

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

### Community 77 - "run_scrape"
Cohesion: 0.15
Nodes (20): run_scrape(), raw_card(), test_coerce_job_valid_and_dropped(), test_normalize_raw_camel_and_snake_shapes(), test_run_scrape_cap_breaks_next_page_loop(), test_run_scrape_close_failure_swallowed(), test_run_scrape_excludes_java_revealed_by_enrichment(), test_run_scrape_full_flow() (+12 more)

### Community 78 - "linkedin_email_scraper.py"
Cohesion: 0.10
Nodes (15): _body_text(), _check_bot_wall(), _results_ui_ready(), _snippet_around(), _submit_search(), _wait_for_results(), test_body_text_returns_visible_text_and_swallows_errors(), test_check_bot_wall_detects_captcha_and_search_pause() (+7 more)

### Community 79 - "test_web.py"
Cohesion: 0.06
Nodes (42): api_collect_jobs(), api_job_to_raw(), api_scan_skills(), default_export_runner(), default_skills_runner(), render_skills_text(), RunRecord, _api_job() (+34 more)

### Community 80 - "4. Code style (the conventions used everywhere)"
Cohesion: 0.23
Nodes (9): 4. Code style (the conventions used everywhere), 9.1b Live network trace — measured session on naukri.com (2026-09-19), `naukri_scraper.py` — Layer 2-live, the pipeline core, 5. Test matrix (automated ↔ manual), check_bot_wall(), extract_listing_cards(), handle_possible_block(), human_scroll() (+1 more)

### Community 81 - "practice_tests.py"
Cohesion: 0.16
Nodes (5): crawl_books(), _get_with_retry(), main(), Reporter, store_books()

### Community 82 - "Data Isolation and Lifecycle Hunting"
Cohesion: 0.20
Nodes (9): Core discipline (include in every agent prompt for this domain), Data Isolation and Lifecycle Hunting, Deletion, revocation, and lifecycle attack classes (subagent_type: `general`), Derived-data and disclosure attack classes (subagent_type: `general`), Export, backup, restore, and migration attack classes (subagent_type: `general`), Tenant and object-isolation attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+1 more)

### Community 84 - "test_email_collector.py"
Cohesion: 0.11
Nodes (20): build_all_search_url(), build_content_search_url(), _contacts_from_cards(), extract_emails(), no_pauses(), test_build_all_search_url_shape(), test_build_content_search_url_all_time(), test_build_content_search_url_rejects_unknown_facet() (+12 more)

### Community 85 - "Desktop, Mobile, and Local IPC Hunting"
Cohesion: 0.20
Nodes (10): Application-state and device-lifecycle attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Deep-link, callback, and navigation attack classes (subagent_type: `general`), Desktop, Mobile, and Local IPC Hunting, Local IPC and exported-component attack classes (subagent_type: `general`), Privileged-helper and local-file attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+2 more)

### Community 86 - "Testing Guide — practice progression + automated suite"
Cohesion: 0.40
Nodes (4): 1. Practice progression (manual, in order), 2. Automated suite (this repo), 3. Live practice runs (this repo, Chrome-only stack), Testing Guide — practice progression + automated suite

### Community 87 - "FakePage"
Cohesion: 0.09
Nodes (18): _open_feed(), _open_posts_view(), _wheel_feed(), FakePage, test_open_feed_handles_non_transient_navigation_error(), test_open_feed_logs_in_then_tolerates_reopen_error(), test_open_feed_stops_if_bounced_back_to_wall_after_login(), test_open_feed_stops_when_login_never_completes() (+10 more)

### Community 88 - "Memory Safety, Binary, and Kernel Hunting"
Cohesion: 0.20
Nodes (10): Binary loading and runtime attack classes (subagent_type: `general`), Bounds, integer, and representation attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), FFI and ABI attack classes (subagent_type: `general`), Kernel and privileged-interface attack classes (subagent_type: `general`), Lifetime, type, and concurrency attack classes (subagent_type: `general`), Memory Safety, Binary, and Kernel Hunting, Universal moves (apply across the above) (+2 more)

### Community 89 - "Protocols, RPC, and Messaging Hunting"
Cohesion: 0.20
Nodes (9): Broker and queue isolation attack classes (subagent_type: `general`), Core discipline (include in every agent prompt for this domain), Framing, schema, and interpretation attack classes (subagent_type: `general`), Protocols, RPC, and Messaging Hunting, Replay, ordering, and transaction attack classes (subagent_type: `general`), RPC identity and authorization attack classes (subagent_type: `general`), Universal moves (apply across the above), Validation rules (apply before reporting ANY finding here) (+1 more)

### Community 90 - "Full Code Explanation — Secure Naukri.com Jobs Collector"
Cohesion: 0.14
Nodes (14): 11. Knowledge graph + living docs, 12. Fair use (binding), 1. Project structure (where everything lives), 5.1 Layered architecture (the backbone), 5.2 ETL / pipeline pattern, 5.3 Modular monolith, CLI-first (no server, no microservices), 5.5 Other architectural idioms, 5. Architecture patterns (+6 more)

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

### Community 95 - "export.py"
Cohesion: 0.15
Nodes (11): _email_domain(), _latest_email_frame(), _naive_timestamp(), _posted_timestamp(), test_email_domain_and_naive_timestamp_helpers(), test_latest_email_frame_empty_input_returns_empty(), test_posted_timestamp_fallbacks_never_raise(), test_posted_timestamp_handles_missing_reference_and_timezone() (+3 more)

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
Cohesion: 0.11
Nodes (17): Boundaries, Code Style, Commands, Data contract, Decisions already made (clarification round, 2026-10-23), Design, Fair use (extends LINKEDIN_RESEARCH §10), Implementation update (2026-10-25) (+9 more)

### Community 100 - "Task List"
Cohesion: 0.20
Nodes (9): Checkpoint: Complete, Checkpoint: Core, Checkpoint: Foundation, Implementation Plan: LinkedIn Recruiter Email Collector, Open Questions, Overview, Phase 3: CLI + polish, Risks and Mitigations (+1 more)

### Community 101 - "9. Mermaid diagrams (detail)"
Cohesion: 0.29
Nodes (7): 9.1 Full data-flow (browser → DB → files), 9.2 Class / data-model diagram, 9.3 Database ER, 9.4 Module dependency graph, 9.5 Browser-launch decision flow, 9.6 Bot-wall / politeness state, 9. Mermaid diagrams (detail)

### Community 102 - "_on_login_wall"
Cohesion: 0.20
Nodes (7): Implementation note (2026-10-23), _on_login_wall(), _wait_for_login(), test_on_login_wall_detects_auth_redirect(), test_wait_for_login_gives_up_after_grace(), test_wait_for_login_true_when_already_signed_in(), test_wait_for_login_waits_until_wall_clears()

### Community 103 - "_FakeSched"
Cohesion: 0.25
Nodes (5): _FakeSched, test_run_scheduled_handles_interrupt(), _factory(), test_run_scheduled_handles_system_exit(), _factory()

### Community 104 - "EmailContact"
Cohesion: 0.10
Nodes (11): _collect_view(), EmailContact, Todo — LinkedIn Recruiter Email Collector (from tasks/plan.md, spec docs/SPEC-linkedin-email-collector.md), test_collect_view_breaks_on_empty_feed_and_zero_rounds(), test_collect_view_growth_without_checkpoint_and_final_extract(), test_collect_view_reaches_target_after_scroll(), _fake_extract(), test_collect_view_stops_after_three_stalls() (+3 more)

### Community 105 - "_click_next_page"
Cohesion: 0.25
Nodes (6): _click_next_page(), _list_state(), test_click_next_page_and_list_state_survive_detached_dom(), test_click_next_page_returns_false_without_enabled_control(), test_click_next_page_times_out_when_range_never_changes(), test_click_next_page_waits_for_range_change()

### Community 106 - "build_slug_search_url"
Cohesion: 0.22
Nodes (7): 9. Recommended LinkedIn plan for this repo, 4. Pagination bug and fix (2026-10-26), Key-skills scan (API fast path + browser fallback), build_slug_search_url(), test_build_slug_search_url_empty_location_falls_back_to_india(), test_build_slug_search_url_mirrors_manual(), test_build_slug_search_url_multi_location_uses_first_city_in_path()

### Community 107 - "load_frame"
Cohesion: 0.24
Nodes (7): _dedupe(), load_frame(), _seed_quality_gates(), test_load_frame_drops_unwanted_rows_by_default(), test_load_frame_empty_db_with_filter(), test_load_frame_exclude_unwanted_false_keeps_raw_pool(), test_load_frame_external_apply_dropped_only_under_gates()

### Community 109 - "upsert_jobs"
Cohesion: 0.11
Nodes (24): 2. Start point (how the app boots), 3. Endpoints (CLI commands — this app has no HTTP server), 5.4 Repository / DAO (data-access encapsulation), `db.py` — Layer 4, repository, Module responsibility matrix, 2. Module reference, count_jobs(), fetch_all_jobs() (+16 more)

### Community 110 - "collectUnitErrors"
Cohesion: 0.25
Nodes (20): canonicalCoverageId(), collectUnitErrors(), encodeCanonicalRef(), escapeUnsafeDiagnosticCharacters(), isCanonicalRef(), isObject(), isOwnedArtifactPath(), isSafeAgentId() (+12 more)

### Community 112 - "Orchestrator"
Cohesion: 0.08
Nodes (16): health(), BusyError, Orchestrator, cancel(), download(), get_one(), list_all(), start_collect() (+8 more)

### Community 113 - "preflightJsonText"
Cohesion: 0.40
Nodes (11): JsonStructureError, preflightJsonText(), beginContainer(), beginString(), beginValue(), closeContainer(), countValue(), currentContainer() (+3 more)

### Community 114 - "Conventional Commits"
Cohesion: 0.33
Nodes (5): Conventional Commits, Examples, Format, Rules, Types

### Community 115 - "_BrokenPage"
Cohesion: 0.16
Nodes (9): _expand_show_more(), _extract_fresh(), _BrokenPage, test_expand_show_more_clicks_and_waits(), test_expand_show_more_swallows_errors(), test_extract_fresh_dedupes_and_updates_email_set(), test_extract_fresh_survives_extractor_error_without_hook(), evaluate() (+1 more)

### Community 116 - "build_skills_report"
Cohesion: 0.40
Nodes (4): build_skills_report(), test_build_skills_report_counts_postings_once(), test_build_skills_report_empty(), test_build_skills_report_unknown_company()

### Community 118 - "Page"
Cohesion: 0.11
Nodes (14): _apply_content_filters(), _click_filter_button(), _count_posts(), _scroll_to_bottom(), _select_filter_radio(), _show_filter_results(), test_apply_content_filters_happy_path_applies_sort_and_date(), test_apply_content_filters_radio_and_show_results_failures() (+6 more)

### Community 119 - "load_email_frame"
Cohesion: 0.18
Nodes (11): export_emails(), load_email_frame(), _persist(), Phase 2: Core collector, _seed_mixed_emails(), test_email_export_domain_falls_back_to_keyword(), test_email_export_drops_other_domains_and_keeps_latest_post(), test_email_export_ignores_rows_without_any_domain() (+3 more)

### Community 120 - "human_pause"
Cohesion: 0.25
Nodes (5): 10. Testing architecture (why 100% is feasible), _prompt_manual_login(), human_pause(), Architecture Decisions, test_prompt_manual_login_enter_and_eof()

## Knowledge Gaps
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Attack classes — choose and split based on Phase 1` connect `ATTACK-CLASSES.md` to `build_slug_search_url`, `Code Simplification`, `confirmed`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `FakePage` (e.g. with `10. Testing architecture (why 100% is feasible)` and `This repo's map (from `GRAPH_REPORT.md`)`) actually correct?**
  _`FakePage` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `validate-coverage-ledger.cjs` be split into smaller, more focused modules?**
  _Cohesion score 0.12318840579710146 - nodes in this community are weakly interconnected._
- **Why does `confirmed()` connect `confirmed` to `ATTACK-CLASSES.md`, `Client-Side and Browser Hunting`, `AI, LLM, and Agent Hunting`, `validate-findings.test.cjs`, `Cloud and Deployment Hunting`, `Data Isolation and Lifecycle Hunting`, `Security Audit`, `Desktop, Mobile, and Local IPC Hunting`, `Memory Safety, Binary, and Kernel Hunting`, `Protocols, RPC, and Messaging Hunting`, `Resource Exhaustion and Availability Hunting`, `HTTP-Protocol and Authentication Hunting`, `Vulnerability Hunting`, `Supply Chain and Release Hunting`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `FakeContext` (e.g. with `4. Code style (the conventions used everywhere)` and `4. Live e-commerce test (Amazon.in + Flipkart)`) actually correct?**
  _`FakeContext` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `Job` be split into smaller, more focused modules?**
  _Cohesion score 0.12258064516129032 - nodes in this community are weakly interconnected._
- **Why does `FakePage` connect `FakePage` to `run_skills_scan`, `LinkedIn Jobs Expansion — Deep Research`, `Project Document — Secure Naukri.com Jobs Collector`, `naukri_scraper.py`, `conftest.py`, `FakeContext`, `test_scraper.py`, `test_stealth.py`, `run_scrape`, `linkedin_email_scraper.py`, `test_web.py`, `4. Code style (the conventions used everywhere)`, `test_email_collector.py`, `_on_login_wall`, `EmailContact`, `_click_next_page`, `build_slug_search_url`, `FakeLocator`, `_BrokenPage`, `Page`, `human_pause`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._