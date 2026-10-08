# LinkedIn Jobs Expansion — Deep Research

Goal: collect jobs from `https://www.linkedin.com/jobs/` in addition to
Naukri.com, reusing this repo's pipeline
(Browser → Extract → Pydantic → SQLite → CSV/Excel, see `README.md` §3).

Date: 2026-10-09. All links below were fetched and read in full (README +
skill indexes). No hurry items — accuracy over speed.

## 1. Link index (everything in one place)

### Skills catalog + MCP

| # | Link | What it is |
|---|------|------------|
| S1 | https://github.com/VoltAgent/awesome-agent-skills | Curated catalog, 1497+ real-world agent skills (not AI-slop). Compatible with OpenCode. |
| S2 | https://mcpservers.org/servers/shadowrootdev/awesome-agent-skills-mcp | Listing page for the MCP server below (install, tools, troubleshooting). |
| S3 | https://github.com/shadowrootdev/awesome-agent-skills-mcp | The MCP server source (TypeScript, MIT). `npx awesome-agent-skills-mcp`. 4 tools: `list_skills`, `get_skill`, `invoke_skill`, `refresh_skills`. Auto-syncs S1 on a timer. Needs Node ≥ 20. |

### LinkedIn / jobs repos

| # | Link | What it is |
|---|------|------------|
| R1 | https://github.com/speedyapply/JobSpy | `python-jobspy` (MIT, Py ≥ 3.10): multi-board **HTTP/API** job scraper → pandas DataFrame. Boards: LinkedIn, Indeed, Glassdoor, ZipRecruiter, **Naukri**, Bayt, BDJobs, HelloWork. |
| R2 | https://github.com/joeyism/linkedin_scraper | `linkedin-scraper` (Apache-2.0, Py 3.8+): **async Playwright + Pydantic v2** scraper for LinkedIn persons, companies, jobs. Session file reuse, typed errors, progress callbacks. |
| R3 | https://github.com/stickerdaniel/linkedin-mcp-server | `mcp-server-linkedin` (Apache-2.0, Py ≥ 3.12.4, Patchright Chromium): **MCP server** driving a real LinkedIn browser session. 20 tools incl. `search_jobs`, `get_job_details`, `get_job_apply_url`. Run via `uvx mcp-server-linkedin@latest`. |
| R4 | https://github.com/m8sec/CrossLinked | `crosslinked` (GPL-3.0): LinkedIn **employee-name enumeration via Google/Bing** (OSINT). No login, no API keys. NOT a job scraper. |

## 2. awesome-agent-skills (S1) — how the catalog is organized

- One giant `README.md` (~1900 lines) of `<details>` sections per
  **vendor/team**: Official Claude, VoltAgent, SerpApi, Crawlbase, TestMu AI,
  Angular, Composio, Supabase, Google Gemini, Stripe, Courier, CallStack,
  Expo, Better Auth, Tinybird, HashiCorp, Sanity, Firecrawl, Neon,
  ClickHouse, Remotion, Replicate, Typefully, Vercel, Cloudflare, Netlify,
  Hugging Face, Trail of Bits, Sentry, Microsoft, fal.ai, WordPress, OpenAI,
  Figma, Brave, Browserbase, CodeRabbit, … plus a **Community Skills**
  section (273 entries).
- Every skill hyperlink resolves to either `officialskills.sh/<org>/skills/<name>`
  (canonical content) or the source GitHub repo path.
- There is **no LinkedIn-job-scraping skill** in the catalog. The value for
  us is neighboring skills (below).

## 3. Skills relevant to THIS project (checked hyperlink by hyperlink)

### 3a. Directly usable — browser automation / scraping

| Skill (hyperlink target) | Why it matters here |
|---|---|
| `openai/playwright` → https://officialskills.sh/openai/skills/playwright | Automate real browser interactions for navigation, forms, **and scraping**. Closest official Playwright recipe; our `stealth_browser.py` + `naukri_scraper.py` already live in this space — use it to review/extend our LinkedIn flow. |
| `openai/playwright-interactive` → https://officialskills.sh/openai/skills/playwright-interactive | Persistent-browser + `js_repl` debugging loop. Useful while developing `linkedin_scraper.py` selectors live. |
| `anthropics/webapp-testing` → https://officialskills.sh/anthropics/skills/webapp-testing | Playwright-based testing of web apps. Pairs with our `scripts/practice_*.py` + pytest suite when adding LinkedIn fixtures. |
| `testmu-ai/playwright-skill` → https://github.com/LambdaTest/agent-skills/tree/main/playwright-skill | Playwright E2E in **Python** among others — same language as us. Reference for wait/retry/locator patterns. |
| `testmu-ai/puppeteer-skill` → https://github.com/LambdaTest/agent-skills/tree/main/puppeteer-skill | Explicitly covers **browser automation and scraping** script generation. Logic portable to Playwright-Python. |
| `testmu-ai/selenium-skill` → https://github.com/LambdaTest/agent-skills/tree/main/selenium-skill | Selenium in Python among others. We deliberately excluded Selenium (`README.md` §4) — consult only if Playwright hits a wall. |
| `testmu-ai/pytest-skill` → https://github.com/LambdaTest/agent-skills/tree/main/pytest-skill | pytest fixtures/parametrize/mocking — our suite enforces a 100% coverage gate (`pytest`); use when adding `test_linkedin*.py`. |
| `browser-act/browser-act` → https://github.com/browser-act/skills/tree/main/browser-act (community) | **Automate authenticated browsers with extraction + human handoff.** This is exactly our bot-wall pattern (first headful run, manual CAPTCHA/login, persistent profile). Best-practice reference. |
| `reliefeai/browser-relay` → community | Control an existing logged-in Chrome without stealing focus. Alternative session pattern; note only. |
| `lackeyjb/playwright-skill`, `testdino-hq/playwright-skill` → community | Playwright automation patterns (the latter: 70+ production-tested patterns incl. POM/CI). Consult as needed. |
| `eatmoreduck/boss-zhipin-scraper` → https://github.com/eatmoreduck/boss-zhipin-scraper (community) | A **job-board scraper skill** (BOSS Zhipin via Chrome CDP, plaintext salaries). Closest analog to what we are building — study its card→record mapping approach. |

### 3b. Usable as services (API, not browser) — discovery / enrichment

| Skill | How we could use it |
|---|---|
| `firecrawl/firecrawl-build-scrape`, `-search`, `-interact` → https://officialskills.sh/firecrawl/skills/firecrawl-build-scrape (et al.) | Hosted scrape/search/extraction with auth-aware flows. Fallback if LinkedIn hard-blocks our IP: pay-per-call instead of fighting bot walls. Needs API key. |
| `crawlbase/crawl-html`, `crawl-markdown` → officialskills.sh/crawlbase/… | JS-rendered crawl + proxy rotation + anti-bot via the `@crawlbase/mcp` server. Same fallback role as Firecrawl. |
| `serpapi/serpapi-web-search` → https://officialskills.sh/serpapi/skills/serpapi-web-search | 130+ engines **including a Google Jobs engine**. Could power a *job-discovery* pass (find postings across boards incl. LinkedIn) before deep-scraping. Needs API key; pair with `serpapi-search-tools-python`. |
| `browserbase/*` (browser, fetch, search, cookie-sync) → officialskills.sh/browserbase/… | Cloud browsers + `cookie-sync` (export local Chrome cookies into a cloud context): the hosted version of our persistent-profile trick. |
| `brave/web-search`, `brave/llm-context` → officialskills.sh/brave/… | Cheap web search + pre-extracted page content. Discovery helper, not a scraper. |

### 3c. Job-domain (career) skills — pipeline-adjacent, not scraping

| Skill | Note |
|---|---|
| `santifer/career-ops` → https://github.com/santifer/career-ops (community) | 14-skill job-search collection: JD A–F scoring, ATS-optimized PDFs, **portal scanners (Greenhouse/Ashby/Lever)**, interview prep. Useful *after* collection (ranking/enrichment); its portal-scanner pattern previews a phase-3 expansion. |
| `vaibhavarora14/job-application-agent` → community | Privacy-first job discovery/tracking. Tracking-DB ideas for our `ScrapeRun`/exports. |
| `Linked-API/linkedin` → https://github.com/Linked-API/linkedin-skills/tree/main/linkedin (community) | LinkedIn profiles/people/company workflows for agents. Complements (not replaces) job collection. |
| `sergebulaev/linkedin-skills`, `typefully/typefully` | Marketing/posting on LinkedIn. **Out of scope** for scraping. |

## 4. awesome-agent-skills-mcp (S2/S3) — evaluation for this repo

- **What it does:** serves the S1 catalog over MCP (stdio). Tools:
  `list_skills` (filter by source/tag), `get_skill` (full markdown),
  `invoke_skill` (parameterized), `refresh_skills` (re-sync repo).
- **Working nature:** stateless catalog lookup; JSON cache (`.cache/`);
  `SKILLS_SYNC_INTERVAL` (default 60 min) re-pulls S1. No browsing itself —
  it hands the *agent* the recipe at task time.
- **Cost:** 4 tools added to model context (Code Mode groups them). Small
  vs. pasting skill docs into prompts.
- **Fit for us:** HIGH as a *development assistant*. When we build
  `src/linkedin_scraper.py`, the agent can pull `openai/playwright`,
  `testmu-ai/playwright-skill`, `browser-act/browser-act`,
  `firecrawl-build-scrape` on demand instead of us vendoring docs.
- **Config note:** the README's OpenCode snippet is **v1 syntax**
  (`"mcp": {"name": {...}}`). v2 requires `"mcp": {"servers": {...}}`
  (verified against https://opencode.ai/v2/docs/mcp-servers). Wired below
  accordingly as a local stdio server: `command: ["npx", "-y",
  "awesome-agent-skills-mcp"]`.
- **Verified findings (2026-10-09, live test on this Mac):**
  - Cold start takes ~96 s (repo sync + README parse: 325 links, 303
    skills loaded) — far past the 30 s default. Config sets
    `timeout.startup: 180000, catalog: 120000`.
  - Cache defaults to relative `.cache/` → pinned to
    `SKILLS_CACHE_DIR: ~/.cache/awesome-agent-skills` so the repo stays
    clean.
  - Interop bug: tools declare `outputSchema` but return text-only
    `content` (no `structuredContent`), so OpenCode Code Mode rejects
    calls (`did not return structured content`). Workaround:
    `"codemode": false` — tools are exposed natively as text (the model
    parses the JSON-in-text itself). Verified connected after the change.
  - Index quality is lossy: `filter: "playwright"` returns only
    `playwright-skill` (description `">"`) and misses
    `openai/playwright`. Use this MCP for discovery, but **verify
    against §3 above / officialskills.sh** before relying on a skill.
- **Decision: CONFIGURED** in `.opencode/opencode.json`
  (`mcp.servers.agent-skills`). Zero secrets required. Disable with
  `"disabled": true` if context gets noisy.

## 5. R1 JobSpy — deep dive (highest reference value)

- **Tech stack:** Python ≥ 3.10, `requests` (+ `requests[socks]` for SOCKS),
  `pandas`, `markdownify`/HTML parsing, `pip install -U python-jobspy`
  (MIT). No browser, no Selenium/Playwright.
- **Architecture:** one package, per-board modules behind a single
  `scrape_jobs()` router:
  `site_name=[...]` → board module → normalize → one DataFrame.
  Proxy round-robin per board; `fetch_description` second pass for boards
  whose cards lack descriptions.
- **Working nature / logic flow:**
  1. Build board search request (`search_term`, `location`, `distance`,
     `job_type`, `is_remote`, `easy_apply`, `offset`, `hours_old`).
  2. Page results (≈1000/board cap), parse cards → `JobPost` rows.
  3. Optional per-job page fetch for description/details.
  4. Return DataFrame (`to_csv`/`to_excel`).
- **LinkedIn specifics:** global search via `location` only; burst 429s
  that clear in ~1 min; proxies for volume. **Naukri module exists too**
  (`location` = city, e.g. `"Pune"`).
- **What to reference:** (a) `JobPost` schema — compare with our
  `src/models.py Job` and adopt missing fields (`job_url_direct`,
  `salary interval/min/max/currency`, `job_level/function`,
  `listing_type`, `company_*`); (b) site-router pattern for our
  `naukri_scraper.py` → `linkedin` second source; (c) proxy round-robin +
  `hours_old`/`--days` filtering parity; (d) `fetch_description` two-pass
  idea mirrors our `--no-enrich` fast sweep.
- **Risk:** LinkedIn changes markup/endpoints often → **pin
  `python-jobspy==x.y.z`** in `requirements.txt`, add a parsing smoke test.

## 6. R2 joeyism/linkedin_scraper — deep dive (stack twin)

- **Tech stack:** Python 3.8+, **async Playwright**, **Pydantic v2**,
  `aiofiles`, `python-dotenv` (Apache-2.0). Same DNA as our repo.
- **Architecture:** `BrowserManager` (headless flag, slow_mo, viewport,
  UA; `save_session`/`load_session` JSON) + `PersonScraper` /
  `CompanyScraper` / `JobSearchScraper(page)` + Pydantic models
  (`Person`, `Company`, `Job`) + `ProgressCallback` + typed errors
  (`AuthenticationError`, `RateLimitError`, `ProfileNotFoundError`).
- **Logic flow (jobs):** load session → `JobSearchScraper.search(keywords,
  location, limit)` → paginate cards → open each → Pydantic `Job{title,
  company, location, description, employment_type, seniority_level,
  linkedin_url}`.
- **Auth:** LinkedIn login wall; manual-login script then session reuse —
  **identical** to our Naukri first-headful-run + `.pw-profile` pattern
  (`README.md` §2b heads-up).
- **What to reference:** (a) `JobSearchScraper.search` pagination/extract
  skeleton for our `src/linkedin_scraper.py`; (b) session save/load module
  boundary (compare with `stealth_browser.py`); (c) Pydantic `Job` fields →
  extend our `models.py`; (d) typed anti-bot errors → our failure taxonomy
  (`docs/TESTING.md`) and tenacity policy (retry transient-only, never
  CAPTCHA/429-loops).

## 7. R3 stickerdaniel/linkedin-mcp-server — deep dive (agent aid)

- **Tech stack:** Python ≥ 3.12.4, **Patchright** Chromium (Playwright
  fork), FastMCP/Uvicorn, `uvx` distribution (Apache-2.0).
- **Architecture:** MCP stdio (or streamable-HTTP) server owning ONE
  shared browser + profile (`~/.linkedin-mcp/profile`); serialized tool
  calls; session via `--login` window or `--import-from-browser`
  (Chrome/Edge/Brave cookies incl. macOS keychain nuance).
- **Job tools:** `search_jobs` (keyword+location → ids),
  `get_job_details` (description/requirements/company),
  `get_job_apply_url` (Easy-Apply vs external), `get_saved_jobs`.
- **What to reference:** selector knowledge for LinkedIn job pages
  (debug via `--no-headless` + `--log-level DEBUG`); proxy-before-login
  discipline (sticky residential, set up **before** `--login`); timeout
  ladder (`--timeout` page-op vs `--tool-timeout` whole-call).
- **Fit for us:** assistant during development (probe pages, validate
  selectors without writing scripts), NOT the collection engine — our
  pipeline must run unattended via scheduler, and this server needs an
  interactive session + separate browser. Optional future
  `mcp.servers.linkedin` entry; deliberately **not** added now.

## 8. R4 m8sec/CrossLinked — deep dive (mostly out of scope)

- **Tech stack:** Python, `requests`, Google/Bing HTML scraping (PyPI
  `crosslinked`, **GPL-3.0**).
- **Working nature:** `search "<company> site:linkedin.com/in"` →
  names/titles/urls → `names.txt`/`names.csv` → offline re-parse with new
  `-f` format; `--proxy/--proxy-file` rotation, `-t` timeout, `-j` jitter.
- **What to reference:** ONLY the politeness/rotation CLI pattern
  (timeout + jitter + proxy file) — and even that overlaps our existing
  `MIN_DELAY_S/MAX_DELAY_S` + tenacity setup.
- **Do NOT use for jobs:** enumerates *people*, not postings; needs a
  known naming convention; GPL-3.0 forbids copying code into this repo;
  search-engine scraping of LinkedIn violates both ToSes at once.

## 9. Recommended LinkedIn plan for this repo

1. **Phase 1 (fast, no browser):** spike `JobSpy`
   (`site_name=["linkedin","naukri"]`, same keywords/locations) →
   compare its rows with our DB; adopt useful `JobPost` fields into
   `src/models.py`; pin version.
2. **Phase 2 (native, same stack):** add `src/linkedin_scraper.py`
   mirroring `src/naukri_scraper.py` (URL builder → tenacity `goto` →
   in-page JS extractor w/ honeypot guards → Pydantic coerce), reusing
   `stealth_browser.py` persistent profile + first-headful manual login;
   R2's `JobSearchScraper` as the selector reference.
3. **Phase 3 (enrich):** per-job detail pass (R1 `fetch_description` /
   R3 `get_job_details` pattern) behind `--enrich`, rate-limited.
4. **Testing:** `tests/test_linkedin.py` (offline HTML fixtures, no
   network) keeping the 100% coverage gate; practice-suite entry in
   `docs/TESTING.md`.
5. **Assistants:** `agent-skills` MCP (configured) for on-demand
   Playwright/scraping recipes; R3 MCP only as an opt-in dev probe.

## 10. Fair-use note (extends README §5 to LinkedIn)

Public postings only, personal search, rate-limited; respect LinkedIn ToS
+ `robots.txt`; never share/sell data; LinkedIn login-walls aggressively —
first run headful, reuse the profile, back off on 429/verification pages.
