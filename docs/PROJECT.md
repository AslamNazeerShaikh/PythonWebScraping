# Project Document — Secure Naukri.com Jobs Collector

> **Purpose.** Personal job-search assistant for a .NET developer (6+ yrs,
> ASP.NET Core / C# / Fullstack, Pune + Hyderabad) with little spare time:
> collect job apply links into a local database on a schedule, review a short
> list, apply fast.
>
> **Stack.** Python + Playwright (bundled Chromium, persistent context) + uBlock Origin Lite for collection;
> BeautifulSoup + lxml for offline parsing; Pydantic for validation;
> SQLAlchemy + SQLite for storage; Pandas + openpyxl for export; APScheduler
> for scheduling; tenacity for transient retries; Typer + Rich for the CLI;
> std `logging`; python-dotenv for config.
>
> **Non-goals.** No Selenium/Scrapy, no stealth-spoofing packages, no proxy
> rotation, no CAPTCHA solving. The collector is a polite, low-volume browser,
> not an evasion tool (see `BOT_DETECTION.md` for the philosophy).

---

## 1. How it works (pipeline)

```
Scheduler (APScheduler, `schedule --hours 8,20`)
        │  one polite pass per trigger, max_instances=1
        ▼
Browser (Playwright → bundled Chromium + uBO Lite)   stealth_browser.py
        │  persistent profile · genuine headed Chromium (no JS spoofing) · uBlock + fallback blocker
        │  human pauses/scrolls · manual-solve bot-wall handling
        ▼
Extraction — LIVE: in-page JS (computed-style honeypot guards)
             OFFLINE twin: BeautifulSoup + lxml  parser.py / naukri_scraper.py
        │  skips display:none · aria-hidden · href traps · 0-size · off-screen
        │  dedupes by /job-listings-<slug>-(<id>)
        ▼
Validation (Pydantic Job)                        models.py
        │  single contract; bad cards dropped with a named-field warning
        ▼
Persistence (SQLAlchemy → SQLite, jobs.db)       db.py
        │  upsert by job_id · first_seen/last_seen · scrape_runs audit log
        ├──► Pandas → CSV / Excel snapshots      export.py
        ├──► Skill scan → report + .txt          run_skills_scan / api_scan_skills
        └──► timestamped JSON/CSV snapshots      output/  (naukri_scraper.save_results)
CLI (Typer) · output (Rich) · retries (tenacity, transient-only) · logging
```

> **Market snapshot (2026-10-26).** `NAUKRI_MARKET_SNAPSHOT.md` records the
> current C#/.NET top 10 key skills and job titles, the employer-breadth
> correction and the data-quality caveats.

**Key invariants**

1. SQLite is the source of truth; every file export is a disposable snapshot.
2. `job_id` (Naukri numeric id) is the dedupe key end-to-end.
3. Retries cover transient network/timeouts only (max 3, exponential backoff).
   HTTP 403/429/CAPTCHA walls are never retried — the run pauses for a manual
   solve instead of hammering.
4. First run is headful (solve CAPTCHA / log in once); cookies persist in the
   profile, later runs succeed.
5. Skill scans are analysis-only: they aggregate Naukri's card key-skill
   chips and never write postings to SQLite.

## 2. Module reference

| Module | Responsibility | Key functions |
|---|---|---|
| `config.py` | `.env`-driven `SETTINGS` singleton | `_get*` readers, `Settings`, `SETTINGS` |
| `stealth_browser.py` | Chromium-only launcher + uBO Lite wiring | `launch_context`, `_launch_chromium`, `_extension_args`, `human_pause` |
| `naukri_scraper.py` | Search URLs, extractors, pipeline | `build_search_url`, `build_slug_search_url`, `scrape_search_page`, `_click_next_page`, `enrich_job`, `run_scrape`, `run_skills_scan`, `build_skills_report`, `save_results`, `coerce_job`, `normalize_raw` |
| `parser.py` | Offline BS4+lxml twin of the JS extractors | `parse_search_html`, `parse_detail_html` |
| `models.py` | Pydantic `Job` + ORM `JobRow`/`ScrapeRun` | `Job.skill_text`, `JobRow.from_job/to_job` |
| `db.py` | Engine, sessions, upsert, audit | `init_db`, `upsert_jobs`, `record_run`, `fetch_all_jobs`, `count_jobs` |
| `export.py` | Pandas CSV/Excel snapshots | `load_frame`, `export_jobs` |
| `scheduler.py` | Daily cron triggers | `run_scheduled` |
| `main.py` | Typer commands + Rich tables | `do_scrape`, `scrape/export/stats/parse/schedule` |
| `log.py` | Std-logging setup | `setup_logging` |

## 3. Configuration (`.env`, see `.env.example`)

| Var | Default | Meaning |
|---|---|---|
| `KEYWORDS` | `asp.net core c# .net fullstack` | Search keywords (`k`) |
| `LOCATIONS` | `pune,hyderabad` | One search per location (`l`) |
| `EXPERIENCE` / `DATE_FILTER` | `6` / `7` | Years exp · posted last N days |
| `MAX_PAGES_PER_SEARCH` / `MAX_JOBS_TOTAL` | `3` / `60` | Politeness caps (pages per search; one search per location) |
| `ENRICH_DETAILS` | `true` | Visit each job page (`--no-enrich` skips) |
| `BROWSER` / `HEADLESS` | `chromium` / `false` | Engine (chromium-only) · background |
| `USER_DATA_DIR` | `.pw-profile` | Persistent profile (cookies, uBO) |
| `TIMEZONE` / `LOCALE` | `Asia/Kolkata` / `en-IN` | Fingerprint consistency |
| `UBLOCK_UNPACKED_DIR` | `vendor/ubol-chrome` | uBO Lite dir (fetch via `vendor/download-ubol.sh`; headed-only) |
| `ADBLOCK_FALLBACK` | `true` | Built-in tracker-blocker |
| `MIN_DELAY_S` / `MAX_DELAY_S` / `NAV_TIMEOUT_MS` | `2.0` / `5.0` / `45000` | Polite timing |
| `OUTPUT_DIR` / `DATABASE_URL` / `LOG_LEVEL` | `output` / `sqlite:///jobs.db` / `INFO` | Outputs |

## 4. Commands

```bash
source .venv/bin/activate
python -m src.main scrape --keywords "asp.net core c# .net" --locations "pune,hyderabad" --days 7 --pages 3
python -m src.main scrape --no-enrich --pages 2          # fast link sweep
python -m src.main stats                                  # DB overview
python -m src.main export --format excel --location pune # filtered snapshot
python -m src.main parse output/debug_last_search.html   # offline re-parse
python -m src.main schedule --hours 8,20                 # daily 08:05 + 20:05
pytest                                                    # 336 tests, 100% coverage gate

# Key-skills scan (API fast path, browser fallback): POST /api/skills
curl -s -X POST http://127.0.0.1:8000/api/skills -H 'Content-Type: application/json' \
  -d '{"keywords":"c#, asp.net core, .net fullstack","location":"pune, hyderabad, bangalore",\
"experience":6,"days":7,"pages":23,"max_jobs":500,"count_mode":"postings"}'
```

## 5. Data model

`jobs(job_id PK, title, company, location, search_location, experience, salary,
posted, url, apply_url, snippet, description, skills, first_seen, last_seen)` ·
`scrape_runs(id, started_at, keywords, locations, pages, found, new_jobs)`.

## 6. Known environment notes (verified)

- Chromium-only by decision (Playwright-bundled build, no `channel:`): no Firefox engine (stable 155, Nightly 1543)
  starts in this environment — both die spawning the profile/content
  process (`Operation not permitted` on helper exec). Chromium works.
- uBO Lite loads headed-only (headless-shell can't load extensions);
  headless runs use the fallback blocker. Verified functionally live.
- Retries catch BOTH `TimeoutError` classes: Playwright raises its own, not
  the builtin — catching only the builtin silently disables retries
  (found by the live practice suite, regression-tested).
- Naukri blocks headless browsers: first run must be headful.

## 7. Fair use

Public listings only, rate-limited, personal job search. Respect Naukri's ToS
and `robots.txt`; never share/sell scraped data or run concurrent workers. On
a block page: back off, retry later.

## 8. Knowledge graph (Graphify)

This repo ships a queryable map of itself ([details](GRAPHIFY.md),
[upstream](https://github.com/Graphify-Labs/graphify),
[code explanation](CODE_EXPLANATION.md)): `graphify-out/`
(`graph.html`, `GRAPH_REPORT.md`, `graph.json`; current node/edge/community
counts are in `GRAPH_REPORT.md`).
Query before grepping: `graphify query "<question>"`. Rebuild after code
changes: `graphify update .` (free). Excludes: `vendor/`, `docs/evidence/`
(see `.graphifyignore`).

## 9. External repo survey (5 repos, verified Oct 2026)

Our collector is **collection-only** (links into SQLite, human applies).
Four adjacent repos cover the write-side (apply / profile-touch) plus one
multi-board read-side (JobSpy). All summaries below were verified against the
live repos (README + source reads); star counts are approximate.

### 9.1 speedyapply/JobSpy (~4.5k stars, MIT, `pip install python-jobspy`)

Multi-board **read-only** scraper: one call
`scrape_jobs(site_name=[...], search_term, location, results_wanted, hours_old, ...)`
fans out via threads to LinkedIn / Indeed / Glassdoor / ZipRecruiter / Bayt /
Naukri / BDJobs / HelloWork, normalizes to a 33-column `JobPost` pydantic model,
returns a DataFrame (`df.attrs["errors"/"warnings"]` carry per-board failures).
Transport is raw HTTP with TLS impersonation (`curl_cffi`), proxy round-robin,
fixed 2–7s delays — no browser. Naukri goes through the private
`jobapi/v3/search` (+ `v4/job/{id}`) with an RSA `nkparam` token
(`appid:109/121`); `406` means rate-limit or stale hardcoded public key.
Only `internship` job_type is natively supported on Naukri; salary is parsed to
`min/max/currency/interval`; `fetch_description` costs one extra request per job.
Google Jobs is a dead stub. See prior session analysis for the full breakdown.

**Reusable in our scraper:** `nkparam` fast-path as an optional pre-filter with
Playwright fallback on 406; salary parsing (`hideSalary` → yearly INR, else
`N/month` stipend regex); `jobAge=ceil(hours/24)`, `wfhType=2` params;
`skills.split(",")`; errors/warnings attrs pattern.

### 9.2 lordzohar/Naukri-autoapply-bot (~61 stars, educational)

Selenium + Edge (`webdriver-manager`) **bulk-apply bot**: auto-login
(`login.naukri.com` + `usernameField`), multi-tab parallel search
(`/{keyword}-jobs[-in-{location}]`), BS4 (`html5lib`) parse of
`div.srp-jobtuple-wrapper` / `a.title`, per-job `driver.get` + ordered
try of `Apply` / `Apply on company site` selectors, inline firstname/lastname
fill, daily-quota detection, `naukriapplied.csv {passed, failed}`.
Second script (`Naukri-Recommended.py`) drives `/mnjuser/recommendedjobs`
multi-apply + chatbot drawer with a `difflib` fuzzy Q&A bank
(`application_answers.csv`, radio + contenteditable handlers).
Anti-bot is minimal (`--disable-notifications`, sleeps, `scrollIntoView`).

**Reusable:** ordered apply-button selector fallback chain; quota-text
detection (`daily quota has been expired`); passed/failed CSV split;
recommended-jobs multi-apply concept. **Not reusable:** Edge-only stack,
`time.sleep`-heavy waits, counting external redirects as `passed`.

### 9.3 navchandar/Naukri (~93 stars, GPL-3.0)

Selenium + Chrome **profile-touch bot** (no search/apply at all): premise is
recruiters surface recently-updated profiles. Flow
`login → UpdateProfile (rewrite mobile number, verify "today") →
UploadResume (via attachCV/lazyAttachCV, verify updateOn date) → Logout`.
Optional stealth PDF mutation (off-page invisible text via
reportlab+pypdf, default off). Config is plaintext `constants.py`
(`USERNAME/PASSWORD/MOBILE` — do-not-commit warning). Minimal anti-bot
(maximized Chrome, popup closers, `safe_click` JS fallback); scheduling is
external (Windows Task Scheduler how-to link only).

**Reusable:** profile-freshness concept as a complement to collection
(visibility vs apply links); `attachCV` upload + `updateOn`-date verification
pattern; `safe_click` JS fallback for chatbot-overlay intercepts.
**Not reusable:** hardcoded ID/XPath selectors, Windows-only date format
(`%#d`), plaintext-creds-in-source pattern, GPL-3.0 (license-incompatible
with permissive reuse — treat as ideas-only).

### 9.4 ankitbaghel01/naukri_update (~83 stars, Node.js 18+, Windows)

Playwright (`playwright-core` + stealth plugin) **two-part system**:
(1) `naukri-profile-refresh.js` — hourly headline dot-cycle
(`""→"."→".. "→""`) + daily CV re-upload with server re-verification,
Google-login flow with persistent profile dir, off-screen window
(headless is blocked by Akamai/DataDome), error screenshots;
(2) `auto-apply-runner.js` + per-site inject scripts
(`naukri-/wellfound-/indeed-auto-apply.js`) — title keyword/blocklist
filtering, infinite-scroll + Next-page, `localStorage` seen-lists
(separate dry/live), chatbot/Q&A bank + Gemini fallback, cover-letter
generation, external-ATS handler (`external-apply.js`, skips
Workday/Taleo/iCIMS/etc.), post-submit verification against the site's
applied list, `applications.csv` (with `Verified` column) +
`apply-state-{site}.json` daily caps (Naukri 20/day), `DRY_RUN`-by-default,
Task Scheduler hourly/daily wiring, `check-setup.js` diagnostics.
Best engineering of the four: persistent contexts, human typing
(45–150s paces), text-based selectors, supervisor restart loop.

**Reusable:** headline dot-cycle refresh (cheapest visibility bump);
dry-run-by-default discipline; seen vs seenDry split; daily-cap state files;
post-submit verification against applied list; external-ATS skip-list;
`check-setup.js`-style session diagnostics. **Adaptation needed:** Node→Python
port, Windows Scheduler → APScheduler, Chrome profile dirs → our
`.pw-profile` convention.

### 9.5 Traverser25/NopeRi (~88 stars, self-reports working Jul 2026)

Selenium-free Python **API client** for Naukri (closest to JobSpy's Naukri
module, but account-aware): `NaukriLoginClient` (login + OTP/MFA,
`nauk_at` bearer, profile-id cache, `formKey` extraction from JS bundles,
resume upload via `filevalidation...` + `advResume`, profile update) +
`NaukriJobClient` (recommended-jobs POST, `v3/search` + `nkparam`, job
details, `is_external_apply` check, `cloudgateway-workflow/.../v1/apply`
with questionnaire heuristics + hardcoded profile answers, history fetch).
`nkparam` generated pure-Python (RSA `PKCS1_v1_5`, `v0|<ms>|121_srp`) with
Selenium harvester fallback (`nkPool.txt`); `httpcloak`/`curl_cffi` TLS
impersonation; exponential retry with jitter (no retry on 403/406);
`apply_agent.py` adds OpenAI scoring + `applied_jobs.csv` dedup + terminal
dashboard. IP-bound sessions (datacenter IPs burned; home/residential OK).

**Reusable:** the write-side API surface our collector lacks (login/OTP,
`formKey` mining, resume/profile endpoints, apply + questionnaire payloads,
`APPLY_SRC_MAP`/`sid`/`logstr` construction); pure-Python `nkparam`
generator (compare with JobSpy's before adopting either); retry-with-jitter
helper (extend our tenacity policy); CSV-dedupe agent loop shape.
**Caution:** hardcoded RSA key + payload formats break on Naukri rotation;
questionnaire answers are hardcoded; ToS risk is highest here (authenticated
writes at volume).

### 9.6 Adoption map for our collector (read-side stays, write-side optional)

| Idea | Source | Fits our stack? | Notes |
|---|---|---|---|
| `nkparam` fast-path search w/ Playwright fallback | JobSpy / NopeRi | Yes, low risk | Compare both generators first; fallback on 403/406 |
| Structured salary/skills/WFH parsing | JobSpy / NopeRi | Yes | Port `_parse_salary`, `tagsAndSkills.split`, placeholder location parse |
| Ordered apply-button fallback + quota detection | lordzohar | Only if we add apply | New capability; needs auth + caps + dry-run |
| Profile headline dot-cycle + CV re-upload verify | ankitbaghel01 / navchandar | Only if we add refresh | Cheapest visibility win; port to Playwright/Python + APScheduler |
| Dry-run default + applied-list verification + daily caps | ankitbaghel01 / NopeRi | Only if we add apply | Required guardrails before any live apply |
| `safe_click` JS fallback, `check-setup` diagnostics | navchandar / ankitbaghel01 | Yes | Small, stack-neutral robustness wins |

Scope guard: our repo is collection-only by design (see §7 fair use).
Anything in the "only if we add" rows is a new authenticated write capability
and needs an explicit requirement prompt before implementation — which is the
next step (awaiting user requirements).
