# Graph Report - PythonWebScraping  (2026-09-19)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 364 nodes · 737 edges · 12 communities
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 24 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `25993dee`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_scraper.py
- Job
- FakeContext
- main.py
- launch_context
- test_parser.py
- test_main.py
- config.py
- practice_tests.py
- test_export.py

## God Nodes (most connected - your core abstractions)
1. `FakePage` - 38 edges
2. `Job` - 31 edges
3. `FakeContext` - 26 edges
4. `make_job()` - 20 edges
5. `run_scrape()` - 17 edges
6. `upsert_jobs()` - 17 edges
7. `launch_context()` - 17 edges
8. `do_scrape()` - 16 edges
9. `JobRow` - 15 edges
10. `enrich_job()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `test_coerce_job_valid_and_dropped()` --uses--> `Job`  [INFERRED]
  tests/test_scraper.py → src/models.py
- `test_ensure_env_default_base_no_copy()` --calls--> `_ensure_env()`  [EXTRACTED]
  tests/test_main.py → src/main.py
- `test_ensure_env_first_run_copies_example()` --calls--> `_ensure_env()`  [EXTRACTED]
  tests/test_main.py → src/main.py
- `make_job()` --calls--> `Job`  [EXTRACTED]
  tests/conftest.py → src/models.py
- `test_job_rejects_short_title_and_id()` --calls--> `Job`  [EXTRACTED]
  tests/test_models.py → src/models.py

## Import Cycles
- None detected.

## Communities (12 total, 0 thin omitted)

### Community 0 - "test_scraper.py"
Cohesion: 0.06
Nodes (59): Page, build_search_url(), check_bot_wall(), coerce_job(), enrich_job(), handle_possible_block(), human_scroll(), is_relevant() (+51 more)

### Community 1 - "Job"
Cohesion: 0.06
Nodes (50): DeclarativeBase, field_validator, Session, count_jobs(), fetch_all_jobs(), get_engine(), get_session(), SQLite access via SQLAlchemy — engine, sessions, and upsert logic. Design… (+42 more)

### Community 2 - "FakeContext"
Cohesion: 0.07
Nodes (33): Exception, fixture, _extension_args(), Build ``--load-extension`` args for uBOL (headed mode only). Headless-shell…, fake_playwright(), FakeBrowserType, FakeContext, FakeMouse (+25 more)

### Community 3 - "main.py"
Cohesion: 0.07
Nodes (39): command, init_db(), Create ``jobs`` / ``scrape_runs`` tables if they don't exist (idempotent)., Logging setup — one call at startup, standard library only. We deliberately use…, Configure root logging to stdout. Args: level: Level name such as…, setup_logging(), do_scrape(), _ensure_env() (+31 more)

### Community 4 - "launch_context"
Cohesion: 0.09
Nodes (29): Playwright, main(), probe(), Path, Live bot-detection probe — implements docs/BOT_DETECTION.md Test B/C. Uses the…, Run the full probe; returns the results dict (also saved as JSON)., _dismiss_flipkart_login(), main() (+21 more)

### Community 5 - "test_parser.py"
Cohesion: 0.15
Nodes (23): _card_text(), _is_trap(), parse_detail_html(), parse_search_html(), Layer 2 (extraction, offline twin): BeautifulSoup + lxml over saved HTML.…, Parse a saved Naukri JOB page into a detail fragment. Args: html: Full job-page…, Decide whether an anchor is a honeypot/placeholder trap (skip it). A link is a…, # NOTE: BeautifulSoup (the document root) subclasses Tag, so the loop (+15 more)

### Community 6 - "test_main.py"
Cohesion: 0.10
Nodes (9): _FakePW, Tests for src.main — startup setup, pipeline wiring, all 5 commands., sync_playwright() stand-in (context manager yielding a fake handle)., test_do_scrape_empty_returns_zero(), test_do_scrape_found_persists_and_snapshots(), test_ensure_env_default_base_no_copy(), test_ensure_env_first_run_copies_example(), test_stats_command() (+1 more)

### Community 7 - "config.py"
Cohesion: 0.14
Nodes (17): _get(), _get_bool(), _get_float(), _get_int(), Central configuration — every tunable lives here, loaded from `.env`.…, Return stripped env var ``name`` or ``default`` when unset., Return env var ``name`` parsed as :class:`int`, else ``default``., Return env var ``name`` parsed as :class:`float`, else ``default``. (+9 more)

### Community 8 - "practice_tests.py"
Cohesion: 0.17
Nodes (12): retry, crawl_books(), _get_with_retry(), main(), Path, Live practice suite — implements docs/TESTING.md Tests 1-7 on sandboxes. Runs…, # NOTE: this Chromium makes page.goto() THROW on HTTP error, Collects (name, passed, detail) rows and prints the final report. (+4 more)

### Community 9 - "test_export.py"
Cohesion: 0.24
Nodes (12): DataFrame, export_jobs(), load_frame(), Path, Load jobs from SQLite into a :class:`~pandas.DataFrame`. Args: location:…, Export the current DB snapshot to CSV or Excel. Args: fmt: ``"csv"`` (default)…, Tests for src.export — Pandas frames, filters, CSV/Excel snapshots., _seed() (+4 more)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Job` connect `Job` to `test_scraper.py`, `FakeContext`, `main.py`?**
  _High betweenness centrality (0.150) - this node is a cross-community bridge._
- **Why does `parse_search_html()` connect `test_parser.py` to `main.py`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Why does `launch_context()` connect `launch_context` to `practice_tests.py`, `FakeContext`, `main.py`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `Job` (e.g. with `fetch_all_jobs()` and `upsert_jobs()`) actually correct?**
  _`Job` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_scraper.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05859969558599695 - nodes in this community are weakly interconnected._
- **Should `Job` be split into smaller, more focused modules?**
  _Cohesion score 0.0633879781420765 - nodes in this community are weakly interconnected._
- **Should `FakeContext` be split into smaller, more focused modules?**
  _Cohesion score 0.06823529411764706 - nodes in this community are weakly interconnected._