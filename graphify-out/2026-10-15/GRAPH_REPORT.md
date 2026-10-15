# Graph Report - PythonWebScraping  (2026-10-15)

## Corpus Check
- 52 files · ~34,062 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 785 nodes · 1828 edges · 32 communities (27 shown, 5 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 311 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6ff61840`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- FakePage
- Job
- FakeContext
- test_log_scheduler.py
- src/main.py
- test_parser.py
- test_main.py
- config.py
- practice_tests.py
- LinkedIn Jobs Expansion — Deep Research
- ops.py
- schemas.py
- runlog.py
- ApiError
- Full Code Explanation — Secure Naukri.com Jobs Collector
- Secure Naukri.com Jobs Collector
- web/main.py
- Bot-Detection Test Guide — measure exposure, don't chase “Human”
- RunOut
- create_app
- test_mcp_read_tools
- _instant
- test_web.py
- agent-skills
- Orchestrator
- Web Control Plane — Spec + Guide
- build_mcp
- AGENTS.md
- RunRecord
- OpenCode Setup (v2) — plugins, skills, MCP servers

## God Nodes (most connected - your core abstractions)
1. `FakePage` - 47 edges
2. `Job` - 46 edges
3. `Orchestrator` - 43 edges
4. `Module responsibility matrix` - 39 edges
5. `upsert_jobs()` - 35 edges
6. `FakeContext` - 32 edges
7. `run_scrape()` - 29 edges
8. `make_job()` - 29 edges
9. `2. Module reference` - 29 edges
10. `launch_context()` - 26 edges

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

## Communities (32 total, 5 thin omitted)

### Community 0 - "FakePage"
Cohesion: 0.06
Nodes (40): 9.1b Live network trace — measured session on naukri.com (2026-09-19), 5. Test matrix (automated ↔ manual), check_bot_wall(), enrich_job(), handle_possible_block(), human_scroll(), scrape_search_page(), FakePage (+32 more)

### Community 1 - "Job"
Cohesion: 0.05
Nodes (30): 6. Design patterns — GoF catalog (with file:line evidence), `models.py` — Layers 3+4, the data contract, Non-GoF / idiomatic patterns used, fetch_all_jobs(), Base, Job, JobRow, ScrapeRun (+22 more)

### Community 2 - "FakeContext"
Cohesion: 0.06
Nodes (25): _extension_args(), _launch_chromium(), launch_context(), launch_playwright(), _maybe_block_ads(), fake_playwright(), FakeBrowserType, FakeContext (+17 more)

### Community 3 - "test_log_scheduler.py"
Cohesion: 0.19
Nodes (6): _FakeSched, test_run_scheduled_handles_interrupt(), _factory(), test_run_scheduled_handles_system_exit(), _factory(), test_setup_logging_levels()

### Community 4 - "src/main.py"
Cohesion: 0.05
Nodes (45): 2. Start point (how the app boots), 3. Endpoints (CLI commands — this app has no HTTP server), 4. Code style (the conventions used everywhere), 5.4 Repository / DAO (data-access encapsulation), 7. Module-by-module explanation, `config.py` — Layer 0, env-driven settings, `db.py` — Layer 4, repository, `export.py` — Layer 5, Pandas snapshots (+37 more)

### Community 5 - "test_parser.py"
Cohesion: 0.12
Nodes (16): `parser.py` — Layer 2-offline, BS4 twin, _card_text(), _is_trap(), parse_detail_html(), parse_search_html(), _anchor(), test_card_text_none_card(), test_parse_detail_external_apply_wins_over_traps() (+8 more)

### Community 6 - "test_main.py"
Cohesion: 0.10
Nodes (7): _FakePW, test_do_scrape_empty_returns_zero(), test_do_scrape_found_persists_and_snapshots(), test_ensure_env_default_base_no_copy(), test_ensure_env_first_run_copies_example(), test_stats_command(), _wire_pipeline()

### Community 7 - "config.py"
Cohesion: 0.08
Nodes (17): _get(), _get_bool(), _get_float(), _get_int(), Settings, load_frame(), test_get_bool_variants(), test_get_float_valid_and_invalid() (+9 more)

### Community 8 - "practice_tests.py"
Cohesion: 0.07
Nodes (13): main(), probe(), _dismiss_flipkart_login(), main(), Product, scrape_site(), crawl_books(), _get_with_retry() (+5 more)

### Community 9 - "LinkedIn Jobs Expansion — Deep Research"
Cohesion: 0.11
Nodes (17): 10. Fair-use note (extends README §5 to LinkedIn), 1. Link index (everything in one place), 2. awesome-agent-skills (S1) — how the catalog is organized, 3. Skills relevant to THIS project (checked hyperlink by hyperlink), 3a. Directly usable — browser automation / scraping, 3b. Usable as services (API, not browser) — discovery / enrichment, 3c. Job-domain (career) skills — pipeline-adjacent, not scraping, 4. awesome-agent-skills-mcp (S2/S3) — evaluation for this repo (+9 more)

### Community 10 - "ops.py"
Cohesion: 0.12
Nodes (10): list_tables(), table_rows(), db_table(), db_tables(), health(), log_tail(), logs(), stats() (+2 more)

### Community 12 - "schemas.py"
Cohesion: 0.16
Nodes (7): DbTable, ExportRequest, HealthOut, LogFile, ScrapeRequest, StatsOut, TopItem

### Community 13 - "runlog.py"
Cohesion: 0.15
Nodes (9): _target(), attached_run_log(), list_log_files(), log_dir(), LogNotFound, read_log_file(), run_log_path(), test_read_log_file_rejects_bad_names() (+1 more)

### Community 15 - "Full Code Explanation — Secure Naukri.com Jobs Collector"
Cohesion: 0.04
Nodes (43): 10. Testing architecture (why 100% is feasible), 11. Knowledge graph + living docs, 12. Fair use (binding), 1. Project structure (where everything lives), 5.1 Layered architecture (the backbone), 5.2 ETL / pipeline pattern, 5.3 Modular monolith, CLI-first (no server, no microservices), 5.5 Other architectural idioms (+35 more)

### Community 16 - "Secure Naukri.com Jobs Collector"
Cohesion: 0.20
Nodes (9): 1. Setup (one time), 2. Usage, 2b. Docs, knowledge graph & testing phase, 3. Architecture (your proposed stack, as built), 4. Files, 5. Fair-use note, Playwright (bundled Chromium) + uBlock Origin Lite | Pydantic + SQLite | Typer + Rich | personal use, Secure Naukri.com Jobs Collector (+1 more)

### Community 18 - "Bot-Detection Test Guide — measure exposure, don't chase “Human”"
Cohesion: 0.29
Nodes (6): 1. Sites (comparison order), 2. Procedure — Test A/B/C matrix, 3. Signal table (fill from your runs), 4. Reading the results, 5. Fix applied from these measurements (2026-09-19), Bot-Detection Test Guide — measure exposure, don't chase “Human”

### Community 19 - "RunOut"
Cohesion: 0.17
Nodes (6): cancel(), download(), get_one(), list_all(), start_export(), RunOut

### Community 20 - "create_app"
Cohesion: 0.18
Nodes (4): create_app(), _isolated_logs(), test_export_download_states(), web_env()

### Community 21 - "test_mcp_read_tools"
Cohesion: 0.40
Nodes (5): _payload(), test_mcp_read_tools(), test_mcp_start_and_cancel(), _tool(), _tools()

### Community 22 - "_instant"
Cohesion: 0.17
Nodes (11): RunNotFound, _blocking(), _failing(), _instant(), _run(), test_cancel_running_scrape_via_api(), test_dependency_override_injects_orchestrator(), test_export_download_pending_and_missing() (+3 more)

### Community 23 - "test_web.py"
Cohesion: 0.14
Nodes (6): _FakePW, test_default_scrape_runner_failure_restores_settings(), test_default_scrape_runner_full_params(), test_default_scrape_runner_immediate_stop(), _tune_web(), _wire_browser()

### Community 24 - "agent-skills"
Cohesion: 0.08
Nodes (23): codemode, environment, timeout, type, LOG_LEVEL, SKILLS_CACHE_DIR, SKILLS_SYNC_INTERVAL, headers (+15 more)

### Community 25 - "Orchestrator"
Cohesion: 0.17
Nodes (4): Orchestrator, start_scrape(), test_run_history_evicts_oldest(), test_start_and_finish_success()

### Community 26 - "Web Control Plane — Spec + Guide"
Cohesion: 0.17
Nodes (9): Architecture (FastAPI bigger-applications shape), Boundaries, Contract (every action has a cancel twin), Evidence (verify-before-claim), Objective, Run logs, Sources (source-driven-development), UI (+1 more)

### Community 27 - "build_mcp"
Cohesion: 0.15
Nodes (8): MCP tools (curated) + harness wiring, get_stats(), build_mcp(), collector_stats(), BusyError, RunNotCancellable, test_app_without_optional_deps(), test_get_stats_empty_and_seeded()

### Community 29 - "RunRecord"
Cohesion: 0.27
Nodes (4): default_export_runner(), RunRecord, test_default_export_runner_writes_files(), test_run_events_timeline_capped()

### Community 30 - "OpenCode Setup (v2) — plugins, skills, MCP servers"
Cohesion: 0.29
Nodes (6): 1. Config file — `.opencode/opencode.json`, 2. Plugin — `.opencode/plugins/graphify.js`, 3. MCP servers, 4. Skills — `.opencode/skills/`, 5. Verify (run after any change here), OpenCode Setup (v2) — plugins, skills, MCP servers

## Knowledge Gaps
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Job` connect `Job` to `FakePage`, `FakeContext`, `src/main.py`, `LinkedIn Jobs Expansion — Deep Research`, `schemas.py`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `FakePage` (e.g. with `10. Testing architecture (why 100% is feasible)` and `This repo's map (from `GRAPH_REPORT.md`)`) actually correct?**
  _`FakePage` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `FakePage` be split into smaller, more focused modules?**
  _Cohesion score 0.06386946386946386 - nodes in this community are weakly interconnected._
- **Why does `2. Module reference` connect `src/main.py` to `FakePage`, `Job`, `FakeContext`, `test_parser.py`, `config.py`, `practice_tests.py`, `Full Code Explanation — Secure Naukri.com Jobs Collector`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `Job` (e.g. with `6. Design patterns — GoF catalog (with file:line evidence)` and ``db.py` — Layer 4, repository`) actually correct?**
  _`Job` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Should `Job` be split into smaller, more focused modules?**
  _Cohesion score 0.05468215994531784 - nodes in this community are weakly interconnected._
- **Why does `Module responsibility matrix` connect `src/main.py` to `FakePage`, `Job`, `FakeContext`, `test_parser.py`, `config.py`, `practice_tests.py`, `Full Code Explanation — Secure Naukri.com Jobs Collector`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._