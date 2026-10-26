# Spec — Naukri key-skills scan

Status: implemented and verified live **2026-10-26**.

This is the living spec for `POST /api/skills`, `run_skills_scan()` (browser),
and `api_scan_skills()` (search API). It records the DOM as it exists now, the
pagination bug found on 2026-10-26, and the rules the implementation must keep.

---

## 1. Goal

Answer: **"For this search, which key skills appear in the most postings?"**

- One Naukri search for the whole comma-separated keyword string.
- Experience, freshness (`jobAge`), and multi-city location filters applied
  exactly as the manual UI applies them.
- One vote per posting per skill (case-insensitive duplicates collapse).
- `count_mode="postings"` for demand across postings; `"companies"` for
  demand across distinct employers (default).
- Analysis only: postings are **not** written to SQLite. The report + `.txt`
  are the artifact.

## 2. Search URL shape

```text
https://www.naukri.com/<keyword-slug>-jobs-in-<first-city>[-<page>]?
    k=<all keywords>&l=<all cities>&experience=<years>&jobAge=<days>
```

Rules:

- The path uses **only the first city**. The full comma-separated list stays
  in `l` (e.g. `l=pune, hyderabad, bangalore`).
- Putting the whole list in the path
  (`...-jobs-in-pune, hyderabad, bangalore-2`) makes Naukri redirect to page 1
  and silently drop `k/l/experience/jobAge`.
- Page 1 is safe to request directly.
- Pages 2+ are reached by clicking the native **Next** control. A direct
  `...-pune-2` load keeps the page number but loses the SPA filter state.
- `?page=2` on a slug URL is ignored by Naukri.
- The API path uses `sort=f` (freshness); the browser uses Naukri's default
  relevance order. Both see the same live pool, but page composition can shift
  while a run is in flight.

## 3. DOM map (verified live 2026-10-26)

### Home page

| Field | Selector |
|---|---|
| Keywords | `input[placeholder="Enter skills / designations / companies"]` |
| Experience | `#expereinceDD` (site typo) / `input[placeholder="Select experience"]` |
| Location | `input[placeholder="Enter location"]` |
| Autocomplete option | `li.tuple-wrap` |
| Submit | No visible Search button in the served variant; `Enter` submits |

### Search results page (SRP)

| Element | Selector |
|---|---|
| Page shell | `div.styles_job-listing-container__OCfZC` |
| List | `ul.styles_jlc__main__VdwtF` |
| Card | `li.styles_jlc__list-item__cAWRu > div.cust-job-tuple` |
| Title | `h2 > a.title` |
| Company | `a.comp-name` |
| Experience | `span.expwdth` |
| Location | `span.locWdth` |
| Snippet | `span.job-desc` |
| **Key Skills** | **`ul.tags-gt > li.tag-li`** |
| Promoted-card skills | `.keyskill > span` |
| Posted date | `span.job-post-day` |
| Pagination | `nav[aria-label="Pagination"]`; **Next** is an anchor |

The card chips are the same list the search API returns as `tagsAndSkills`
(verified on 398 postings captured by both paths; the raw API string can
repeat a tag, which the aggregator collapses).

### Job detail page

| Element | Selector |
|---|---|
| Description | `section[class*="job-desc"]` (`styles_job-desc-container__txpYf`) |
| Key Skills block | `div[class*="key-skill"]` (`styles_key-skill__GIPn_`) |
| Skill chip | `a.styles_chip > span` |
| Preferred marker | `i.ni-icon-jd-save` inside the chip |

Detail chips can differ from the card chips. The skills scan uses the **card
chips** by design, so it never needs 438 detail visits.

## 4. Pagination bug and fix (2026-10-26)

**Symptom.** Browser pagination kept loading page 1; runs stopped near 20
jobs. Direct `-2` URLs also returned page 1 with only Pune/all-time results
(68 rows instead of 442).

**Root cause.** `build_slug_search_url()` put the whole multi-city string in
the path. Naukri canonicalised the malformed path to page 1 and stripped the
query filters. Even a valid `-2` load loses the SPA's in-memory experience /
`jobAge` / multi-city state.

**Fix.**

1. `build_slug_search_url()` slugs only the first city into the path and keeps
   the full list in `l`.
2. `run_skills_scan()` loads page 1 from that URL.
3. `_click_next_page()` clicks the native **Next** anchor and waits for
   `#listContainer` range text or the first card href to change.
4. The scan never `goto()`s a `-N` URL.
5. `LISTING_EXTRACT_JS` now captures card `skills` and `span.job-post-day`.

Verified sequence: page 1 → 2 kept `21 - 40 of 442`; 23 pages covered the
whole result set.

## 5. Code map

| Concern | Code |
|---|---|
| URL builder (first city in path) | `src/naukri_scraper.py::build_slug_search_url` |
| Card skills + posted date | `src/naukri_scraper.py::LISTING_EXTRACT_JS` |
| Native paging | `src/naukri_scraper.py::_click_next_page`, `NEXT_PAGE_JS`, `LIST_STATE_JS` |
| Browser scan (no detail visits) | `src/naukri_scraper.py::run_skills_scan` |
| API fast path | `src/web/nkapi.py::api_scan_skills` |
| API row → Job | `src/web/nkapi.py::api_job_to_raw` (`tagsAndSkills`) |
| Aggregation | `src/naukri_scraper.py::build_skills_report` |
| Offline detail twin | `src/parser.py::parse_detail_html` |
| Request contract | `src/web/schemas.py::SkillsRequest` (30 pages / 600 jobs cap) |
| Web orchestration | `src/web/orchestrator.py::default_skills_runner` |

## 6. Gating and counting rules

- Skills scans are exploratory: **both** `exclude_unwanted` and `exclude_java`
  are pinned `False`. A Java/Spring posting returned for a .NET query still
  contributes honest demand data.
- Browser scans apply no lane/Java gates at all — every card with a valid
  title is collected.
- Every posting votes at most once per skill (case-insensitive). The display
  casing follows the most common raw form.
- `companies` mode scores distinct companies; `postings` mode scores postings.
  `pct` divides by `companies_total` or `jobs_scanned` respectively.

## 7. Verification snapshot (2026-10-26)

Query: `c#, asp.net core, asp.net core mvc, asp.net web api, .net application
developer, full stack .net developer, net fullstack, entity framework core`
· 6 years · Pune + Hyderabad + Bangalore · last 7 days.

| Metric | API | Browser |
|---|---:|---:|
| Unique postings | 444 | 435 |
| With key-skill tags | 428 | 425 |
| Without tags | 16 | 10 |
| Unique raw tags | 785 | 699 |
| Pages | 23 | 23 |

The live UI count moved 438 → 442 → 447 during the runs. 398 postings were
captured by both paths; their card and API skill lists matched. Raw top 15
agreed on 14/15 entries; technology-only top 15 also agreed on 14/15.

Top 10 technology-only consensus (generic Naukri chips removed): **C#,
.NET, SQL, .NET Core, ASP.NET, Angular, Microsoft Azure, REST, JavaScript,
MVC**. Tail: Automation Testing, CSS, HTML, React.js, Software testing.

The market-facing summary — including the separate 30-day job-title scan,
employer-breadth correction and caveats — is
[`NAUKRI_MARKET_SNAPSHOT.md`](NAUKRI_MARKET_SNAPSHOT.md).

Run artifacts (gitignored, regenerable):

- `output/naukri_skills_top15_20261026.md`
- `output/naukri_skills_api_20261026.json`
- `output/naukri_skills_browser_20261026.json`

## 8. Test coverage

`pytest` keeps the repo at 100% statement + branch coverage. Relevant tests:

- `tests/test_scraper.py` — card skills, multi-city URL, native paging,
  no-detail scan, stop/cap/empty paths.
- `tests/test_web.py` — API/browser skills runners, raw-pool gating,
  postings/companies modes, caps.
- `tests/test_export.py` / `tests/test_parser.py` — offline detail parsing.

## 9. Related market analysis

- [`NAUKRI_MARKET_SNAPSHOT.md`](NAUKRI_MARKET_SNAPSHOT.md) — dated C#/.NET
  snapshot: top 10 skills, top 10 job titles, employer-breadth correction and
  data-quality caveats (2026-10-26).
- `output/naukri_titles_netcore_30d_20261026.md` — title-frequency report for
  the separate `.net core` / 30-day / 4-city scan.
