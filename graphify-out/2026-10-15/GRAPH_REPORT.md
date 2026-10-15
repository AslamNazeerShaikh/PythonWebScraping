# Graph Report - PythonWebScraping  (2026-10-15)

## Corpus Check
- 36 files · ~24,337 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 529 nodes · 1166 edges · 25 communities (19 shown, 6 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 227 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `52d3d13a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_scraper.py
- main.py
- test_stealth.py
- test_log_scheduler.py
- Module responsibility matrix
- test_parser.py
- test_main.py
- config.py
- practice_tests.py
- LinkedIn Jobs Expansion — Deep Research
- raw_card
- Full Code Explanation — Secure Naukri.com Jobs Collector
- Job
- FakeContext
- Project Document — Secure Naukri.com Jobs Collector
- Secure Naukri.com Jobs Collector
- conftest.py
- Bot-Detection Test Guide — measure exposure, don't chase “Human”
- Testing Guide — practice progression + automated suite
- FakeMouse
- test_check_bot_wall_evaluate_failure_is_safe
- agent-skills
- AGENTS.md
- OpenCode Setup (v2) — plugins, skills, MCP servers

## God Nodes (most connected - your core abstractions)
1. `FakePage` - 41 edges
2. `Job` - 39 edges
3. `Module responsibility matrix` - 39 edges
4. `2. Module reference` - 29 edges
5. `FakeContext` - 28 edges
6. `upsert_jobs()` - 25 edges
7. `launch_context()` - 24 edges
8. `do_scrape()` - 23 edges
9. `run_scrape()` - 23 edges
10. `make_job()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `5.3 Modular monolith, CLI-first (no server, no microservices)` --references--> `do_scrape()`  [INFERRED]
  docs/CODE_EXPLANATION.md → src/main.py
- ``config.py` — Layer 0, env-driven settings` --references--> `scrape()`  [INFERRED]
  docs/CODE_EXPLANATION.md → src/main.py
- `6. R2 joeyism/linkedin_scraper — deep dive (stack twin)` --references--> `Job`  [INFERRED]
  docs/LINKEDIN_RESEARCH.md → src/models.py
- `3c. Job-domain (career) skills — pipeline-adjacent, not scraping` --references--> `ScrapeRun`  [INFERRED]
  docs/LINKEDIN_RESEARCH.md → src/models.py
- ``stealth_browser.py` — Layer 1, Chromium launcher` --references--> `launch_context()`  [INFERRED]
  docs/CODE_EXPLANATION.md → src/stealth_browser.py

## Import Cycles
- None detected.

## Communities (25 total, 6 thin omitted)

### Community 0 - "test_scraper.py"
Cohesion: 0.10
Nodes (21): FakePage, make_job(), test_stats_command(), test_build_search_url_encodes_params(), test_check_bot_wall_clean_and_blocked(), test_enrich_job_empty_apply_url_falls_back_to_job_url(), test_enrich_job_ignores_unknown_detail_keys(), test_enrich_job_merges_detail() (+13 more)

### Community 1 - "main.py"
Cohesion: 0.07
Nodes (31): 2. Start point (how the app boots), 3. Endpoints (CLI commands — this app has no HTTP server), 5.4 Repository / DAO (data-access encapsulation), `db.py` — Layer 4, repository, `main.py` — shell, front door, command, count_jobs(), fetch_all_jobs() (+23 more)

### Community 2 - "test_stealth.py"
Cohesion: 0.10
Nodes (23): _extension_args(), _launch_chromium(), launch_context(), launch_playwright(), _maybe_block_ads(), fake_playwright(), FakeRoute, _handler() (+15 more)

### Community 3 - "test_log_scheduler.py"
Cohesion: 0.12
Nodes (7): setup_logging(), _FakeSched, test_run_scheduled_handles_interrupt(), _factory(), test_run_scheduled_handles_system_exit(), _factory(), test_setup_logging_levels()

### Community 4 - "Module responsibility matrix"
Cohesion: 0.11
Nodes (22): 4. Code style (the conventions used everywhere), 5.5 Other architectural idioms, 9.1b Live network trace — measured session on naukri.com (2026-09-19), Module responsibility matrix, `naukri_scraper.py` — Layer 2-live, the pipeline core, 2. Module reference, 5. Test matrix (automated ↔ manual), Settings (+14 more)

### Community 5 - "test_parser.py"
Cohesion: 0.12
Nodes (16): `parser.py` — Layer 2-offline, BS4 twin, _card_text(), _is_trap(), parse_detail_html(), parse_search_html(), _anchor(), test_card_text_none_card(), test_parse_detail_external_apply_wins_over_traps() (+8 more)

### Community 6 - "test_main.py"
Cohesion: 0.10
Nodes (6): _FakePW, test_do_scrape_empty_returns_zero(), test_do_scrape_found_persists_and_snapshots(), test_ensure_env_default_base_no_copy(), test_ensure_env_first_run_copies_example(), _wire_pipeline()

### Community 7 - "config.py"
Cohesion: 0.08
Nodes (16): _get(), _get_bool(), _get_float(), _get_int(), export_jobs(), load_frame(), test_get_bool_variants(), test_get_float_valid_and_invalid() (+8 more)

### Community 8 - "practice_tests.py"
Cohesion: 0.08
Nodes (11): main(), probe(), _dismiss_flipkart_login(), main(), Product, scrape_site(), crawl_books(), _get_with_retry() (+3 more)

### Community 9 - "LinkedIn Jobs Expansion — Deep Research"
Cohesion: 0.11
Nodes (16): 10. Fair-use note (extends README §5 to LinkedIn), 1. Link index (everything in one place), 2. awesome-agent-skills (S1) — how the catalog is organized, 3. Skills relevant to THIS project (checked hyperlink by hyperlink), 3a. Directly usable — browser automation / scraping, 3b. Usable as services (API, not browser) — discovery / enrichment, 3c. Job-domain (career) skills — pipeline-adjacent, not scraping, 4. awesome-agent-skills-mcp (S2/S3) — evaluation for this repo (+8 more)

### Community 10 - "raw_card"
Cohesion: 0.25
Nodes (10): raw_card(), test_coerce_job_valid_and_dropped(), test_normalize_raw_camel_and_snake_shapes(), test_run_scrape_cap_breaks_next_page_loop(), test_run_scrape_close_failure_swallowed(), test_run_scrape_full_flow(), test_run_scrape_no_enrich_and_cap(), test_run_scrape_search_error_continues() (+2 more)

### Community 12 - "Full Code Explanation — Secure Naukri.com Jobs Collector"
Cohesion: 0.09
Nodes (22): 11. Knowledge graph + living docs, 12. Fair use (binding), 1. Project structure (where everything lives), 5.1 Layered architecture (the backbone), 5.2 ETL / pipeline pattern, 5.3 Modular monolith, CLI-first (no server, no microservices), 5. Architecture patterns, 7. Module-by-module explanation (+14 more)

### Community 13 - "Job"
Cohesion: 0.12
Nodes (14): 10. Testing architecture (why 100% is feasible), 6. Design patterns — GoF catalog (with file:line evidence), `models.py` — Layers 3+4, the data contract, Non-GoF / idiomatic patterns used, Job, JobRow, fresh_db(), test_job_rejects_short_title_and_id() (+6 more)

### Community 15 - "Project Document — Secure Naukri.com Jobs Collector"
Cohesion: 0.09
Nodes (20): Artifacts (`graphify-out/`, committed), Graphify — queryable knowledge graph of this repo, Repo wiring, This repo's map (from `GRAPH_REPORT.md`), Usage (no API key needed for code), 1. How it works (pipeline), 3. Configuration (`.env`, see `.env.example`), 4. Commands (+12 more)

### Community 16 - "Secure Naukri.com Jobs Collector"
Cohesion: 0.20
Nodes (9): 1. Setup (one time), 2. Usage, 2b. Docs, knowledge graph & testing phase, 3. Architecture (your proposed stack, as built), 4. Files, 5. Fair-use note, Playwright (bundled Chromium) + uBlock Origin Lite | Pydantic + SQLite | Typer + Rich | personal use, Secure Naukri.com Jobs Collector (+1 more)

### Community 18 - "Bot-Detection Test Guide — measure exposure, don't chase “Human”"
Cohesion: 0.29
Nodes (6): 1. Sites (comparison order), 2. Procedure — Test A/B/C matrix, 3. Signal table (fill from your runs), 4. Reading the results, 5. Fix applied from these measurements (2026-09-19), Bot-Detection Test Guide — measure exposure, don't chase “Human”

### Community 19 - "Testing Guide — practice progression + automated suite"
Cohesion: 0.33
Nodes (5): 1. Practice progression (manual, in order), 2. Automated suite (this repo), 3. Live practice runs (this repo, Chrome-only stack), 4. Live e-commerce test (Amazon.in + Flipkart), Testing Guide — practice progression + automated suite

### Community 24 - "agent-skills"
Cohesion: 0.10
Nodes (20): codemode, environment, timeout, type, LOG_LEVEL, SKILLS_CACHE_DIR, SKILLS_SYNC_INTERVAL, headers (+12 more)

### Community 30 - "OpenCode Setup (v2) — plugins, skills, MCP servers"
Cohesion: 0.29
Nodes (6): 1. Config file — `.opencode/opencode.json`, 2. Plugin — `.opencode/plugins/graphify.js`, 3. MCP servers, 4. Skills — `.opencode/skills/`, 5. Verify (run after any change here), OpenCode Setup (v2) — plugins, skills, MCP servers

## Knowledge Gaps
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Job` connect `Job` to `test_scraper.py`, `main.py`, `Module responsibility matrix`, `LinkedIn Jobs Expansion — Deep Research`, `raw_card`, `Project Document — Secure Naukri.com Jobs Collector`, `conftest.py`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `FakePage` (e.g. with `10. Testing architecture (why 100% is feasible)` and `This repo's map (from `GRAPH_REPORT.md`)`) actually correct?**
  _`FakePage` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_scraper.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10227272727272728 - nodes in this community are weakly interconnected._
- **Why does `Module responsibility matrix` connect `Module responsibility matrix` to `main.py`, `test_stealth.py`, `test_log_scheduler.py`, `test_parser.py`, `config.py`, `Full Code Explanation — Secure Naukri.com Jobs Collector`, `Job`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `Job` (e.g. with `6. Design patterns — GoF catalog (with file:line evidence)` and ``db.py` — Layer 4, repository`) actually correct?**
  _`Job` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06606990622335891 - nodes in this community are weakly interconnected._
- **Why does `2. Module reference` connect `Module responsibility matrix` to `main.py`, `test_stealth.py`, `test_log_scheduler.py`, `test_parser.py`, `config.py`, `Job`, `Project Document — Secure Naukri.com Jobs Collector`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._