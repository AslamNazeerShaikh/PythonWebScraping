# Graph Report - PythonWebScraping  (2026-10-15)

## Corpus Check
- 45 files · ~31,611 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 708 nodes · 1639 edges · 33 communities (30 shown, 3 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 279 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a324bd9b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- FakePage
- Module responsibility matrix
- launch_context
- test_log_scheduler.py
- main.py
- test_parser.py
- test_main.py
- config.py
- naukri_scraper.py
- LinkedIn Jobs Expansion — Deep Research
- FakeContext
- create_app
- Job
- app.py
- Full Code Explanation — Secure Naukri.com Jobs Collector
- Secure Naukri.com Jobs Collector
- 4. Code style (the conventions used everywhere)
- Bot-Detection Test Guide — measure exposure, don't chase “Human”
- 5. Test matrix (automated ↔ manual)
- human_scroll
- handle_possible_block
- _instant
- test_web.py
- agent-skills
- Orchestrator
- Web Control Plane — Spec + Guide
- build_mcp
- AGENTS.md
- RunRecord
- OpenCode Setup (v2) — plugins, skills, MCP servers
- scrape_search_page

## God Nodes (most connected - your core abstractions)
1. `FakePage` - 47 edges
2. `Job` - 46 edges
3. `Module responsibility matrix` - 39 edges
4. `create_app()` - 38 edges
5. `upsert_jobs()` - 34 edges
6. `FakeContext` - 32 edges
7. `Orchestrator` - 30 edges
8. `run_scrape()` - 29 edges
9. `2. Module reference` - 29 edges
10. `make_job()` - 28 edges

## Surprising Connections (you probably didn't know these)
- `5.3 Modular monolith, CLI-first (no server, no microservices)` --references--> `do_scrape()`  [INFERRED]
  docs/CODE_EXPLANATION.md → src/main.py
- `6. R2 joeyism/linkedin_scraper — deep dive (stack twin)` --references--> `Job`  [INFERRED]
  docs/LINKEDIN_RESEARCH.md → src/models.py
- `3c. Job-domain (career) skills — pipeline-adjacent, not scraping` --references--> `ScrapeRun`  [INFERRED]
  docs/LINKEDIN_RESEARCH.md → src/models.py
- ``stealth_browser.py` — Layer 1, Chromium launcher` --references--> `launch_context()`  [INFERRED]
  docs/CODE_EXPLANATION.md → src/stealth_browser.py
- `4. Code style (the conventions used everywhere)` --references--> `_resolve_url()`  [INFERRED]
  docs/CODE_EXPLANATION.md → src/db.py

## Import Cycles
- None detected.

## Communities (33 total, 3 thin omitted)

### Community 0 - "FakePage"
Cohesion: 0.16
Nodes (12): enrich_job(), FakePage, test_enrich_job_empty_apply_url_falls_back_to_job_url(), test_enrich_job_ignores_unknown_detail_keys(), test_enrich_job_merges_detail(), test_enrich_job_timeout_returns_original(), test_enrich_job_unexpected_error_returns_original(), test_enrich_job_validation_failure_returns_original() (+4 more)

### Community 1 - "Module responsibility matrix"
Cohesion: 0.06
Nodes (42): 2. Start point (how the app boots), 5.4 Repository / DAO (data-access encapsulation), `db.py` — Layer 4, repository, `main.py` — shell, front door, Module responsibility matrix, 2. Module reference, Settings, count_jobs() (+34 more)

### Community 2 - "launch_context"
Cohesion: 0.10
Nodes (22): _extension_args(), _launch_chromium(), launch_context(), launch_playwright(), _maybe_block_ads(), fake_playwright(), FakeRoute, _handler() (+14 more)

### Community 3 - "test_log_scheduler.py"
Cohesion: 0.12
Nodes (7): setup_logging(), _FakeSched, test_run_scheduled_handles_interrupt(), _factory(), test_run_scheduled_handles_system_exit(), _factory(), test_setup_logging_levels()

### Community 4 - "main.py"
Cohesion: 0.09
Nodes (17): 3. Endpoints (CLI commands — this app has no HTTP server), `config.py` — Layer 0, env-driven settings, `naukri_scraper.py` — Layer 2-live, the pipeline core, command, _ensure_env(), export(), parse(), schedule() (+9 more)

### Community 5 - "test_parser.py"
Cohesion: 0.10
Nodes (21): 7. Module-by-module explanation, `export.py` — Layer 5, Pandas snapshots, `log.py` — one-call logging, `parser.py` — Layer 2-offline, BS4 twin, `scheduler.py` — Layer 6, cron, `stealth_browser.py` — Layer 1, Chromium launcher, _card_text(), _is_trap() (+13 more)

### Community 6 - "test_main.py"
Cohesion: 0.12
Nodes (4): _FakePW, test_do_scrape_empty_returns_zero(), test_do_scrape_found_persists_and_snapshots(), _wire_pipeline()

### Community 7 - "config.py"
Cohesion: 0.13
Nodes (9): _get(), _get_bool(), _get_float(), _get_int(), test_get_bool_variants(), test_get_float_valid_and_invalid(), test_get_int_valid_and_invalid(), test_get_returns_default_when_unset() (+1 more)

### Community 8 - "naukri_scraper.py"
Cohesion: 0.07
Nodes (13): main(), probe(), _dismiss_flipkart_login(), main(), Product, scrape_site(), crawl_books(), _get_with_retry() (+5 more)

### Community 9 - "LinkedIn Jobs Expansion — Deep Research"
Cohesion: 0.12
Nodes (16): 10. Fair-use note (extends README §5 to LinkedIn), 1. Link index (everything in one place), 2. awesome-agent-skills (S1) — how the catalog is organized, 3. Skills relevant to THIS project (checked hyperlink by hyperlink), 3a. Directly usable — browser automation / scraping, 3b. Usable as services (API, not browser) — discovery / enrichment, 3c. Job-domain (career) skills — pipeline-adjacent, not scraping, 4. awesome-agent-skills-mcp (S2/S3) — evaluation for this repo (+8 more)

### Community 10 - "FakeContext"
Cohesion: 0.13
Nodes (13): run_scrape(), FakeContext, raw_card(), test_coerce_job_valid_and_dropped(), test_normalize_raw_camel_and_snake_shapes(), test_run_scrape_cap_breaks_next_page_loop(), test_run_scrape_close_failure_swallowed(), test_run_scrape_full_flow() (+5 more)

### Community 12 - "create_app"
Cohesion: 0.08
Nodes (19): create_app(), health(), job_detail(), jobs(), run_cancel(), run_detail(), runs(), scrape() (+11 more)

### Community 13 - "Job"
Cohesion: 0.12
Nodes (13): 10. Testing architecture (why 100% is feasible), 6. Design patterns — GoF catalog (with file:line evidence), `models.py` — Layers 3+4, the data contract, Non-GoF / idiomatic patterns used, Job, fresh_db(), test_job_rejects_short_title_and_id(), test_job_title_squeezed() (+5 more)

### Community 14 - "app.py"
Cohesion: 0.14
Nodes (4): JobNotFound, ApiError, BusyError, RunNotCancellable

### Community 15 - "Full Code Explanation — Secure Naukri.com Jobs Collector"
Cohesion: 0.05
Nodes (37): 11. Knowledge graph + living docs, 12. Fair use (binding), 1. Project structure (where everything lives), 5.1 Layered architecture (the backbone), 5.2 ETL / pipeline pattern, 5.3 Modular monolith, CLI-first (no server, no microservices), 5.5 Other architectural idioms, 5. Architecture patterns (+29 more)

### Community 16 - "Secure Naukri.com Jobs Collector"
Cohesion: 0.20
Nodes (9): 1. Setup (one time), 2. Usage, 2b. Docs, knowledge graph & testing phase, 3. Architecture (your proposed stack, as built), 4. Files, 5. Fair-use note, Playwright (bundled Chromium) + uBlock Origin Lite | Pydantic + SQLite | Typer + Rich | personal use, Secure Naukri.com Jobs Collector (+1 more)

### Community 17 - "4. Code style (the conventions used everywhere)"
Cohesion: 0.17
Nodes (6): 4. Code style (the conventions used everywhere), build_search_url(), is_relevant(), FakeBrowserType, test_build_search_url_encodes_params(), test_is_relevant()

### Community 18 - "Bot-Detection Test Guide — measure exposure, don't chase “Human”"
Cohesion: 0.29
Nodes (6): 1. Sites (comparison order), 2. Procedure — Test A/B/C matrix, 3. Signal table (fill from your runs), 4. Reading the results, 5. Fix applied from these measurements (2026-09-19), Bot-Detection Test Guide — measure exposure, don't chase “Human”

### Community 19 - "5. Test matrix (automated ↔ manual)"
Cohesion: 0.25
Nodes (6): 1. Practice progression (manual, in order), 2. Automated suite (this repo), 3. Live practice runs (this repo, Chrome-only stack), 4. Live e-commerce test (Amazon.in + Flipkart), 5. Test matrix (automated ↔ manual), Testing Guide — practice progression + automated suite

### Community 20 - "human_scroll"
Cohesion: 0.20
Nodes (4): human_scroll(), FakeMouse, test_human_scroll_mouse_failure_falls_back(), test_human_scroll_wheels_and_wiggles()

### Community 21 - "handle_possible_block"
Cohesion: 0.15
Nodes (8): 9.1b Live network trace — measured session on naukri.com (2026-09-19), 9. Recommended LinkedIn plan for this repo, check_bot_wall(), handle_possible_block(), test_check_bot_wall_clean_and_blocked(), test_check_bot_wall_evaluate_failure_is_safe(), test_handle_block_noop_never_prompts(), test_handle_block_prompts_then_continues()

### Community 22 - "_instant"
Cohesion: 0.15
Nodes (11): RunNotFound, _blocking(), _failing(), _instant(), _run(), test_cancel_running_scrape_via_api(), test_export_download_pending_and_missing(), test_export_download_states() (+3 more)

### Community 23 - "test_web.py"
Cohesion: 0.14
Nodes (7): default_scrape_runner(), _FakePW, test_default_scrape_runner_failure_restores_settings(), test_default_scrape_runner_full_params(), test_default_scrape_runner_immediate_stop(), _tune_web(), _wire_browser()

### Community 24 - "agent-skills"
Cohesion: 0.10
Nodes (20): codemode, environment, timeout, type, LOG_LEVEL, SKILLS_CACHE_DIR, SKILLS_SYNC_INTERVAL, headers (+12 more)

### Community 25 - "Orchestrator"
Cohesion: 0.17
Nodes (4): Orchestrator, test_run_history_evicts_oldest(), test_scrape_lock_and_cancel_flow(), test_start_and_finish_success()

### Community 26 - "Web Control Plane — Spec + Guide"
Cohesion: 0.15
Nodes (10): Architecture, Boundaries, Contract (every action has a cancel twin), Evidence (verify-before-claim), MCP tools (curated), Objective, Sources (source-driven-development), UI (+2 more)

### Community 27 - "build_mcp"
Cohesion: 0.20
Nodes (7): build_mcp(), _payload(), test_app_without_optional_deps(), test_mcp_read_tools(), test_mcp_start_and_cancel(), _tool(), _tools()

### Community 29 - "RunRecord"
Cohesion: 0.25
Nodes (3): default_export_runner(), RunRecord, test_default_export_runner_writes_files()

### Community 30 - "OpenCode Setup (v2) — plugins, skills, MCP servers"
Cohesion: 0.29
Nodes (6): 1. Config file — `.opencode/opencode.json`, 2. Plugin — `.opencode/plugins/graphify.js`, 3. MCP servers, 4. Skills — `.opencode/skills/`, 5. Verify (run after any change here), OpenCode Setup (v2) — plugins, skills, MCP servers

### Community 31 - "scrape_search_page"
Cohesion: 0.40
Nodes (4): scrape_search_page(), test_scrape_search_page_debug_save_failure_swallowed(), test_scrape_search_page_empty_saves_debug(), test_scrape_search_page_returns_cards()

## Knowledge Gaps
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Job` connect `Job` to `FakePage`, `Module responsibility matrix`, `launch_context`, `main.py`, `naukri_scraper.py`, `LinkedIn Jobs Expansion — Deep Research`, `FakeContext`, `create_app`, `app.py`, `Full Code Explanation — Secure Naukri.com Jobs Collector`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `FakePage` (e.g. with `10. Testing architecture (why 100% is feasible)` and `This repo's map (from `GRAPH_REPORT.md`)`) actually correct?**
  _`FakePage` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `Module responsibility matrix` be split into smaller, more focused modules?**
  _Cohesion score 0.057946069994262765 - nodes in this community are weakly interconnected._
- **Why does `Module responsibility matrix` connect `Module responsibility matrix` to `FakePage`, `launch_context`, `test_log_scheduler.py`, `main.py`, `test_parser.py`, `naukri_scraper.py`, `FakeContext`, `Job`, `Full Code Explanation — Secure Naukri.com Jobs Collector`, `4. Code style (the conventions used everywhere)`, `human_scroll`, `handle_possible_block`, `scrape_search_page`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `Job` (e.g. with `6. Design patterns — GoF catalog (with file:line evidence)` and ``db.py` — Layer 4, repository`) actually correct?**
  _`Job` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Should `launch_context` be split into smaller, more focused modules?**
  _Cohesion score 0.09743589743589744 - nodes in this community are weakly interconnected._
- **Why does `2. Module reference` connect `Module responsibility matrix` to `FakePage`, `launch_context`, `test_log_scheduler.py`, `main.py`, `test_parser.py`, `naukri_scraper.py`, `FakeContext`, `Job`, `Full Code Explanation — Secure Naukri.com Jobs Collector`, `4. Code style (the conventions used everywhere)`, `scrape_search_page`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._