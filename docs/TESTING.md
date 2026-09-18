# Testing Guide — practice progression + automated suite

> Rule: **never develop against Naukri directly.** Build and prove the
> engineering on purpose-built sandboxes first (they exist for exactly this),
> then run the real collector headful and polite.

## 1. Practice progression (manual, in order)

```
Books to Scrape ──► Quotes to Scrape ──► Scrape This Site ──► WebScraper.io
  static HTML          JS / AJAX / login     forms / frames /     e-commerce /
  1000-book            infinite scroll /     tables / AJAX        pagination
  pagination           delayed / CSRF                             variants
       │                      │                       │                  │
       └──────────────┴───────────────┴──────────────────┴────► Scrapify / TestingURL
                                                              modern JS, lazy-load,
                                                              rate-limit scenarios
                                                                          │
                                                                          ▼
                                                                       Naukri
                                                              (headful, capped, polite)
```

| # | Site | What you prove | Pass criteria |
|---|---|---|---|
| 1 | [Books to Scrape](https://books.toscrape.com/) | Selectors, pagination, Pydantic→SQLite | Exactly **1000/1000** books |
| 2 | Books, 2nd run | Dedupe/upsert | **0 new** on re-run |
| 3 | [Quotes JS variant](https://quotes.toscrape.com/js/) | Rendered-DOM waits | All quotes incl. JS-only |
| 4 | Quotes delayed/scroll variants | Wait + termination condition | Complete set, loop exits |
| 5 | Quotes login | Session/cookies persist | Auth-only page extracted |
| 6 | [Scrape This Site](https://www.scrapethissite.com/) | Tables, AJAX, frames | Correct rows per scenario |
| 7 | [HTTPBin](https://httpbin.org/) + TestingURL | Failure taxonomy | See table below |

**Failure taxonomy** (mirror in your retry/block logic):

| Signal | Meaning | Correct behaviour |
|---|---|---|
| 200 | OK | process |
| 301/302 | redirect | follow (login flows) |
| 400/404 | client/not-found | skip, log, continue |
| 403 / CAPTCHA | wall | **stop + manual solve**, never retry-loop |
| 429 | rate-limited | back off / stop per site rules |
| 500/502, timeout | transient | controlled retry (max 3, exponential), then abort page |

## 2. Automated suite (this repo)
```bash
source .venv/bin/activate
pytest                  # full suite; fails below 100% coverage by design
pytest --no-cov -q      # fast run without the coverage gate
pytest tests/test_parser.py --no-cov -q   # one module
```

## 3. Live practice runs (this repo, Chrome-only stack)

```bash
.venv/bin/python scripts/practice_tests.py          # full Tests 1-7 live
.venv/bin/python scripts/practice_tests.py --quick  # 3-page smoke
```

Measured 2026-09-19, Chromium + uBO Lite, headed — **ALL GREEN 7/7**
(`output/practice/report.json`, gitignored):

| Test | Result |
|---|---|
| T1 extraction | 20/20 books p1 with title+price |
| T2 pagination | **1000/1000** books, 50 pages |
| T3 dedupe | run1 +1000, run2 **+0** |
| T4 JS rendering | 10/10 quotes (`/js/`) with authors |
| T5 infinite scroll | settled at 100 quotes, clean termination |
| T6 login/session | `admin/admin` → Logout, session held |
| T7 failures | 200 process · 404 skip · 500 retried-x3-abort · timeout 3-attempts-abort · 429 observed-stop |

Live testing caught one REAL bug: Playwright raises its **own**
`TimeoutError`, not the builtin — tenacity caught the wrong class, so
retries silently never fired. Fixed in `src/naukri_scraper.py`
(`_TRANSIENT` tuple) + regression test. This is exactly why the numbered
tests run against live sandboxes, not just fakes.

- **93 tests, 100% statement + branch coverage** (`pyproject.toml` enforces
  `--cov-fail-under=100`).
- No real browser or network: `tests/conftest.py` provides `FakePage`,
  `FakeContext`, fake browser types, and a `fresh_db` fixture (isolated tmp
  SQLite per test). Tenacity paths are exercised through `goto_plan`
  scripts; the one ~6s test is the 3-attempt backoff proof.
- Conventions: one test module per source module; fakes live only in
  `conftest.py`; `monkeypatch` (auto-reverted) for `SETTINGS`/time/network.

## 4. Test matrix (automated ↔ manual)

| Scenario | Automated test | Manual sandbox |
|---|---|---|
| Static HTML / selectors | `test_parser.py` | Books #1 |
| Pagination | fake `listing_queue` pages | Books 1000-count |
| Duplicate detection | `test_db.py` upsert | Books 2nd run |
| Honeypot filtering | trap fixtures (`#`, js:, hidden, nested) | — (Naukri-specific) |
| Validation gate | `test_models.py`, `coerce` drop | — |
| JS rendering / waits | `wait_for_selector` branches | Quotes JS/delayed |
| Infinite scroll | `human_scroll` rounds | Quotes scroll |
| Login/session | persistent profile design | Quotes login |
| HTTP errors / retry | `_safe_goto` 3-attempt | HTTPBin |
| Rate limiting | politeness delays, caps | TestingURL |
| Bot-wall pause | `handle_possible_block` ×3 paths | Bot-detection suite |
| Engine guard | non-chromium BROWSER rejected | `test_stealth.py` |
| Export | csv/xlsx + location filter | `stats`/`export` cmds |
