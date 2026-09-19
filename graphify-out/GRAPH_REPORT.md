# Graph Report - PythonWebScraping  (2026-09-19)

## Corpus Check
- 44 files · ~31,397 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 509 nodes · 865 edges · 30 communities (22 shown, 6 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 24 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `843a282a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_scraper.py
- main.py
- FakeContext
- test_log_scheduler.py
- practice_ecommerce.py
- test_parser.py
- test_main.py
- test_config.py
- practice_tests.py
- test_export.py
- Full Code Explanation — Secure Naukri.com Jobs Collector
- Job
- What You Must Do When Invoked
- Project Document — Secure Naukri.com Jobs Collector
- Secure Naukri.com Jobs Collector
- graphify reference: extra exports and benchmark
- Bot-Detection Test Guide — measure exposure, don't chase “Human”
- Testing Guide — practice progression + automated suite
- graphify reference: query, path, explain
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- opencode.json
- graphify.js
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- AGENTS.md
- extraction-spec.md

## God Nodes (most connected - your core abstractions)
1. `FakePage` - 38 edges
2. `Job` - 31 edges
3. `FakeContext` - 26 edges
4. `make_job()` - 20 edges
5. `upsert_jobs()` - 17 edges
6. `run_scrape()` - 17 edges
7. `launch_context()` - 17 edges
8. `do_scrape()` - 16 edges
9. `JobRow` - 15 edges
10. `enrich_job()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `test_ensure_env_default_base_no_copy()` --calls--> `_ensure_env()`  [EXTRACTED]
  tests/test_main.py → src/main.py
- `test_ensure_env_first_run_copies_example()` --calls--> `_ensure_env()`  [EXTRACTED]
  tests/test_main.py → src/main.py
- `test_coerce_job_valid_and_dropped()` --uses--> `Job`  [INFERRED]
  tests/test_scraper.py → src/models.py
- `main()` --calls--> `launch_context()`  [EXTRACTED]
  scripts/practice_ecommerce.py → src/stealth_browser.py
- `main()` --calls--> `launch_context()`  [EXTRACTED]
  scripts/practice_tests.py → src/stealth_browser.py

## Import Cycles
- None detected.

## Communities (30 total, 6 thin omitted)

### Community 0 - "test_scraper.py"
Cohesion: 0.05
Nodes (63): Page, build_search_url(), check_bot_wall(), coerce_job(), enrich_job(), handle_possible_block(), human_scroll(), is_relevant() (+55 more)

### Community 1 - "main.py"
Cohesion: 0.06
Nodes (58): command, DeclarativeBase, Session, Central configuration — every tunable lives here, loaded from `.env`.…, All runtime settings. Grouped by concern; see `.env.example`., Settings, count_jobs(), fetch_all_jobs() (+50 more)

### Community 2 - "FakeContext"
Cohesion: 0.05
Nodes (49): Exception, fixture, Playwright, main(), probe(), Path, Live bot-detection probe — implements docs/BOT_DETECTION.md Test B/C. Uses the…, Run the full probe; returns the results dict (also saved as JSON). (+41 more)

### Community 3 - "test_log_scheduler.py"
Cohesion: 0.15
Nodes (11): Logging setup — one call at startup, standard library only. We deliberately use…, Configure root logging to stdout. Args: level: Level name such as…, setup_logging(), _FakeSched, Tests for src.log and src.scheduler., BlockingScheduler stand-in — records jobs, scriptable start()., test_run_scheduled_handles_interrupt(), _factory() (+3 more)

### Community 4 - "practice_ecommerce.py"
Cohesion: 0.18
Nodes (13): _dismiss_flipkart_login(), main(), Product, BaseModel, Path, E-commerce practice test — a few products from Amazon.in + Flipkart. Scope…, Close Flipkart's login modal when present (normal dismiss, not a wall)., Scrape one search page; returns a result dict (blocked or products). (+5 more)

### Community 5 - "test_parser.py"
Cohesion: 0.15
Nodes (23): _card_text(), _is_trap(), parse_detail_html(), parse_search_html(), Layer 2 (extraction, offline twin): BeautifulSoup + lxml over saved HTML.…, Parse a saved Naukri JOB page into a detail fragment. Args: html: Full job-page…, Decide whether an anchor is a honeypot/placeholder trap (skip it). A link is a…, # NOTE: BeautifulSoup (the document root) subclasses Tag, so the loop (+15 more)

### Community 6 - "test_main.py"
Cohesion: 0.10
Nodes (9): _FakePW, Tests for src.main — startup setup, pipeline wiring, all 5 commands., sync_playwright() stand-in (context manager yielding a fake handle)., test_do_scrape_empty_returns_zero(), test_do_scrape_found_persists_and_snapshots(), test_ensure_env_default_base_no_copy(), test_ensure_env_first_run_copies_example(), test_stats_command() (+1 more)

### Community 7 - "test_config.py"
Cohesion: 0.16
Nodes (14): _get(), _get_bool(), _get_float(), _get_int(), Return stripped env var ``name`` or ``default`` when unset., Return env var ``name`` parsed as :class:`int`, else ``default``., Return env var ``name`` parsed as :class:`float`, else ``default``., Return env var ``name`` parsed as flag (1/true/yes/y), else ``default``. (+6 more)

### Community 8 - "practice_tests.py"
Cohesion: 0.17
Nodes (12): retry, crawl_books(), _get_with_retry(), main(), Path, Live practice suite — implements docs/TESTING.md Tests 1-7 on sandboxes. Runs…, # NOTE: this Chromium makes page.goto() THROW on HTTP error, Collects (name, passed, detail) rows and prints the final report. (+4 more)

### Community 9 - "test_export.py"
Cohesion: 0.24
Nodes (12): DataFrame, export_jobs(), load_frame(), Path, Load jobs from SQLite into a :class:`~pandas.DataFrame`. Args: location:…, Export the current DB snapshot to CSV or Excel. Args: fmt: ``"csv"`` (default)…, Tests for src.export — Pandas frames, filters, CSV/Excel snapshots., _seed() (+4 more)

### Community 12 - "Full Code Explanation — Secure Naukri.com Jobs Collector"
Cohesion: 0.05
Nodes (36): 10. Testing architecture (why 100% is feasible), 11. Knowledge graph + living docs, 12. Fair use (binding), 1. Project structure (where everything lives), 2. Start point (how the app boots), 3. Endpoints (CLI commands — this app has no HTTP server), 4. Code style (the conventions used everywhere), 5.1 Layered architecture (the backbone) (+28 more)

### Community 13 - "Job"
Cohesion: 0.13
Nodes (19): field_validator, Job, JobRow, BaseModel, Build a new ORM row from a validated :class:`Job`., Convert a DB row back into a validated :class:`Job`., One validated job record. Attributes: job_id: Stable Naukri numeric id parsed…, Canonicalise URLs: trim whitespace, drop tracking query params. (+11 more)

### Community 14 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 15 - "Project Document — Secure Naukri.com Jobs Collector"
Cohesion: 0.12
Nodes (14): Artifacts (`graphify-out/`, committed), Graphify — queryable knowledge graph of this repo, Repo wiring, This repo's map (from `GRAPH_REPORT.md`), Usage (no API key needed for code), 1. How it works (pipeline), 2. Module reference, 3. Configuration (`.env`, see `.env.example`) (+6 more)

### Community 16 - "Secure Naukri.com Jobs Collector"
Cohesion: 0.20
Nodes (9): 1. Setup (one time), 2. Usage, 2b. Docs, knowledge graph & testing phase, 3. Architecture (your proposed stack, as built), 4. Files, 5. Fair-use note, Playwright + Chrome + uBlock Origin Lite | Pydantic + SQLite | Typer + Rich | personal use, Secure Naukri.com Jobs Collector (+1 more)

### Community 17 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 18 - "Bot-Detection Test Guide — measure exposure, don't chase “Human”"
Cohesion: 0.29
Nodes (6): 1. Sites (comparison order), 2. Procedure — Test A/B/C matrix, 3. Signal table (fill from your runs), 4. Reading the results, 5. Fix applied from these measurements (2026-09-19), Bot-Detection Test Guide — measure exposure, don't chase “Human”

### Community 19 - "Testing Guide — practice progression + automated suite"
Cohesion: 0.29
Nodes (6): 1. Practice progression (manual, in order), 2. Automated suite (this repo), 3. Live practice runs (this repo, Chrome-only stack), 4. Live e-commerce test (Amazon.in + Flipkart), 5. Test matrix (automated ↔ manual), Testing Guide — practice progression + automated suite

### Community 20 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 21 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 22 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 23 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **103 isolated node(s):** `$schema`, `plugin`, `Usage`, `What graphify is for`, `Step 0 - GitHub repos and multi-path merge (only if a URL or several paths)` (+98 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 275 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Job` connect `Job` to `test_scraper.py`, `main.py`, `FakeContext`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `parse_search_html()` connect `test_parser.py` to `main.py`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `launch_context()` connect `FakeContext` to `practice_tests.py`, `main.py`, `practice_ecommerce.py`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `Job` (e.g. with `fetch_all_jobs()` and `upsert_jobs()`) actually correct?**
  _`Job` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `upsert_jobs()` (e.g. with `Job` and `JobRow`) actually correct?**
  _`upsert_jobs()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `plugin`, `Usage` to the rest of the system?**
  _103 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_scraper.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05468215994531784 - nodes in this community are weakly interconnected._