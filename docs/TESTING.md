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

- **98 tests, 100% statement + branch coverage** (`pyproject.toml` enforces
  `--cov-fail-under=100`).
- No real browser or network: `tests/conftest.py` provides `FakePage`,
  `FakeContext`, fake browser types, and a `fresh_db` fixture (isolated tmp
  SQLite per test). Tenacity paths are exercised through `goto_plan`
  scripts; the one ~6s test is the 3-attempt backoff proof.
- Conventions: one test module per source module; fakes live only in
  `conftest.py`; `monkeypatch` (auto-reverted) for `SETTINGS`/time/network.

## 3. Test matrix (automated ↔ manual)

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
| Engine fallback | firefox-fail → chromium | `BOT_DETECTION.md` matrix |
| Export | csv/xlsx + location filter | `stats`/`export` cmds |
