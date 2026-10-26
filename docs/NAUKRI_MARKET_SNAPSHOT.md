# Naukri market snapshot — C#/.NET (2026-10-26)

> **Status:** point-in-time analysis, not a forecast. Naukri counts move as
> postings are added, refreshed and removed. This snapshot records the exact
> queries, counts and caveats so a later run can be compared like-for-like.

**Scope:** C#/.NET developer demand at 6 years' experience, using two
complementary lenses. The cities and freshness windows differ by lens (see the
table); the roles lens adds Noida and a 30-day window.

| Lens | What it answers | Query | Freshness | Sample |
|---|---|---|---|---|
| **Skills** | Which key skills appear most often? | `c#, asp.net core, asp.net core mvc, asp.net web api, .net application developer, full stack .net developer, net fullstack, entity framework core` | last **7 days** | **398** postings seen by both API and browser (444 API / 435 browser) |
| **Roles** | Which job titles appear most often? | `.net core` | last **30 days** | **1,709** unique postings (live count moved 1,711 → 1,716) |

The two lenses use different windows and keyword sets. They are not the same
denominator and should not be divided into each other. The skills lens is the
validated API/browser cross-check; the roles lens is the 30-day title scan
requested on 2026-10-26.

## TL;DR

- **Top 10 key skills:** **C#, .NET, SQL, .NET Core, ASP.NET, Angular,
  Microsoft Azure, REST, JavaScript, MVC**.
- **Top 10 job titles:** **.NET Developer, Custom Software Engineer
  (Accenture mass posting), .NET Full Stack Developer, Full Stack Developer,
  Senior Software Engineer, Senior .NET Developer, Software Developer,
  Software Engineer, Python Lead (noise), SFDC Developer (noise)**.
- **The real .NET role leaders** are `.NET Developer` (149 postings / 86
  employers), `.NET Full Stack Developer` (98 / 60) and `Senior .NET
  Developer` (32 / 24). Together: **279 postings (16.3% of the pool), 142
  employers, 36.3% of all explicitly .NET-titled postings**.
- **45.0% of the 30-day title pool explicitly names .NET/C#/ASP.NET**;
  another **14.7%** are generic software engineer/developer titles whose stack
  is not stated.
- **The biggest raw title is not the best market signal.** Accenture's
  `Custom Software Engineer` accounts for 109 postings (6.4%) from one
  employer. `Python Lead` and `SFDC Developer` are Shashwath Solution mass
  postings and non-.NET noise.

## 1. Top 10 key skills

Technology-only view: Naukri's generic chips are removed (`application`,
`architecture`, `automation`, `coding`, `core`, `development`, `full stack`,
`integration`, `program`, `senior`, `software`, `software development`,
`stack`). `Core` alone is generic; `.NET Core` is the real skill.

| # | Skill | Shared postings | % of 398 | API rank | Browser rank |
|---:|---|---:|---:|---:|---:|
| 1 | **C#** | 165 | 41.5% | 1 | 1 |
| 2 | **.NET** | 118 | 29.6% | 2 | 2 |
| 3 | **SQL** | 107 | 26.9% | 3 | 3 |
| 4 | **.NET Core** | 81 | 20.4% | 4 | 4 |
| 5 | **ASP.NET** | 70 | 17.6% | 5 | 5 |
| 6 | **Angular** | 48 | 12.1% | 6 | 6 |
| 7 | **Microsoft Azure** | 40 | 10.1% | 7 | 7 |
| 8 | **REST** | 33 | 8.3% | 8 | 8 |
| 9 | **JavaScript** | 31 | 7.8% | 9 | 9 |
| 10 | **MVC** | 31 | 7.8% | 10 | 10 |

The 398 postings were captured by **both** the API and the browser. Their
card chips (`ul.tags-gt > li.tag-li`) and API `tagsAndSkills` lists matched
exactly (after collapsing duplicate API tags), so the ranking is not
method-dependent. The shared set agrees on the exact top 10 order; the full
API and browser samples agree on the top seven, then diverge in the tail
because they contain slightly different postings. Display casing is
normalised; raw Naukri tags are in the artifacts.

**Tail (shared 398):** Automation Testing 28 (7.0%), CSS 27 (6.8%), HTML 27
(6.8%), React.js 26 (6.5%), Software testing 25 (6.3%).

**Notable tags in the full samples** (not necessarily in the shared top 10):
ASP.NET Core 15 API / 14 browser (3.4% / 3.2%), Web API 18 / 17 (4.1% /
3.9%), Microservices 14 / 20 (3.2% / 4.6%), SQL Server 13 / 19 (2.9% / 4.4%),
Azure DevOps 20 / 19 (4.5% / 4.4%), Continuous Integration 23 / 22 (5.2% /
5.1%), Docker 7 / 8 (1.6% / 1.8%), Kubernetes 2 / 2 (0.5%). Entity Framework
Core is a long-tail tag: **1 posting in each sample tagged it exactly**
(0.2%). Treat recruiter tags as noisy; absence is not proof that a skill is
unused.

**How to read the skills table**

- **C# is the anchor** (41.5%); .NET, .NET Core and ASP.NET are the platform
  layers; SQL is the data layer.
- **Angular is the clear front-end pairing** (12.1%), ahead of React.js
  (6.5%) in this sample.
- **Azure (10.1%)** is the cloud default; REST (8.3%) and MVC (7.8%) are the
  API/web patterns.
- **ASP.NET (17.6%) outranks ASP.NET Core (3.4% as a separate tag)**. This is
  likely a tagging effect: `ASP.NET` is a generic chip that does not
  distinguish Core, and the query included both `asp.net core` and `asp.net
  web api`. It is not evidence that the market is legacy-only.
- **JavaScript/HTML/CSS** remain relevant because full-stack .NET roles are a
  large part of the pool.

## 2. Top 10 job titles

Titles are normalised to merge spelling and word-order variants:
`Dot Net` / `DotNet` / `.NET` / `.NET Core` / `.NET Software` / `.NET
Application` → `.NET Developer`; `.NET Fullstack` / `Full Stack .NET` →
`.NET Full Stack Developer`; `Full Stack Engineer` → `Full Stack Developer`;
`Sr` → `Senior`; `Dev` → `Developer`; city tags, parentheticals and
walk-in/drive noise removed. Raw variants are preserved in the CSV.

Parenthetical stack details are removed for title grouping. §3 classifies on
the **raw** title, so a variant such as `Full Stack Developer (.NET + React)`
groups under the generic title here but counts as a .NET full-stack posting
there. This is a grouping choice, not a contradiction.

| # | Job title | Postings | Share | Employers | Note |
|---:|---|---:|---:|---:|---|
| 1 | **.NET Developer** | **149** | 8.7% | 86 | Includes Dot Net Developer (71), .NET Software Developer (28), .NET Application Developer (11), .NET Developer (8), Dotnet Developer (4), .NET Core Developer (3), … |
| 2 | **Custom Software Engineer** | **109** | 6.4% | 1 | All **Accenture**, across Bengaluru/Hyderabad/Pune; 109 distinct job IDs, a mass-hiring campaign |
| 3 | **.NET Full Stack Developer** | **98** | 5.7% | 60 | Includes Dot Net Fullstack Developer (36), Full Stack .Net Developer (23), .NET Full Stack Developer (8), Full Stack .NET Developer (4), … |
| 4 | **Full Stack Developer** (generic title) | **58** | 3.4% | 43 | Includes Fullstack Developer, Full Stack Engineer, and variants that name .NET/React/AWS in parentheses |
| 5 | **Senior Software Engineer** | **43** | 2.5% | 36 | Some specify .NET/full-stack in parentheses; title itself is generic |
| 6 | **Senior .NET Developer** | **32** | 1.9% | 24 | Includes Senior Dot Net Software Developer, Senior .NET Developer, Sr .Net Developer |
| 7 | **Software Developer** | **21** | 1.2% | 12 | Generic title; stack usually only in the description |
| 8 | **Software Engineer** | **17** | 1.0% | 16 | Includes Software Engineer (Dotnet), Software Engineer (C#, Unity) |
| 9 | **Python Lead** | **11** | 0.6% | 1 | All **Shashwath Solution**; non-.NET search noise |
| 10 | **SFDC Developer & Senior Developer** | **10** | 0.6% | 1 | All **Shashwath Solution**; non-.NET search noise |

**Literal vs meaningful.** The literal top 10 is dominated by one employer's
mass posting at #2 and two non-.NET mass postings at #9–#10. The employer-
breadth view below is the better read of market demand.

### Top 10 by employer breadth

| # | Job title | Employers | Postings |
|---:|---|---:|---:|
| 1 | .NET Developer | **86** | 149 |
| 2 | .NET Full Stack Developer | **60** | 98 |
| 3 | Full Stack Developer | **43** | 58 |
| 4 | Senior Software Engineer | **36** | 43 |
| 5 | Senior .NET Developer | **24** | 32 |
| 6 | Software Engineer | **16** | 17 |
| 7 | Software Developer | **12** | 21 |
| 8 | DevOps Engineer | **6** | 6 |
| 9 | Java Full Stack Developer | **6** | 6 |
| 10 | Software Engineer II | **5** | 7 |

Tied at 5 employers: Senior Full Stack Developer (5 postings) and Senior
DevOps Engineer (5 postings).

## 3. What the .NET role market looks like

| Measure | Postings | Share of 1,709 | Employers |
|---|---:|---:|---:|
| Explicitly .NET/C#/ASP.NET/WPF/Sitecore/SharePoint/Dynamics title | **769** | **45.0%** | **277** |
| Core .NET developer / .NET full-stack titles (incl. senior/specialised) | **390** | **22.8%** | **169** |
| Top three .NET roles: .NET Developer + .NET Full Stack + Senior .NET | **279** | **16.3%** | **142** |
| Generic software engineer/developer title, no stack named | **252** | **14.7%** | **97** |
| Full-stack title with no .NET named | **111** | **6.5%** | **65** |

The top three .NET roles account for **36.3% of all explicitly .NET-titled
postings** (279 of 769). After those three, the .NET title list becomes a long
tail of specialised and lead roles, each with small counts: Azure .NET Full
Stack (6 postings / 2 employers), .NET + Angular (6 / 1), .NET Core Developer
(5 / 3), .NET Engineer with SQL (5 / 1), Senior .NET Engineer (5 / 1), C# WPF
Developer (4 / 3), Sitecore Developer (4 / 2), and so on. A "top 10 pure .NET
titles" table would be misleading because positions 4–10 are mostly
single-employer or single-digit counts.

**What this means for a C#/.NET candidate**

1. **Lead with C# + .NET + SQL + .NET Core + ASP.NET.** These are the five
   strongest recurring signals across the skills sample.
2. **Add Angular + Azure + REST/MVC** for full-stack and API roles. Angular
   is the most common front-end tag here; Azure is the default cloud tag.
3. **Target both ".NET Developer" and ".NET Full Stack Developer" titles.**
   They are separate, large pools: 149 non-full-stack vs 98 full-stack.
   Senior .NET is the next distinct title (32).
4. **Do not over-index on the literal #2 title.** Accenture's "Custom Software
   Engineer" is a single-employer hiring drive; it does not mean the market
   uses that title broadly.
5. **Ignore Python Lead and SFDC as .NET signals.** They are Naukri's broad
   matching returning adjacent roles, not C#/.NET demand.

## 4. Method and data quality

### Skills lens

- Source: Naukri card key-skill chips (`ul.tags-gt > li.tag-li`) and the
  identical API `tagsAndSkills` field.
- API sample: 444 postings, 428 with tags, 785 unique raw tags, 198 companies.
- Browser sample: 435 postings, 425 with tags, 699 unique raw tags, 187
  companies.
- Shared sample: 398 postings. Skill lists matched exactly on every shared
  posting; the API/browser top 10 order is identical.
- Generic Naukri chips are removed for the technology-only view; no skills are
  inferred from job descriptions.
- Full detail: `output/naukri_skills_top15_20261026.md` and
  `docs/SPEC-naukri-skills-scan.md`.

### Roles lens

- Source: Naukri search API, 20 cards/page, deduplicated by `jobId`.
- 1,709 unique postings collected; the live count moved from 1,711 at the
  start to ~1,715–1,716 while paging (99.6% of the end count). New postings
  arriving during paging explain most of the gap.
- All collected postings have `createdDate` between 2026-09-25 and
  2026-10-26, so the 30-day window is applied.
- 553 distinct employers (normalised), 996 raw title strings, 827 normalised
  titles.
- No detail-page visits: titles and employers come from the result cards.

### Caveats

- **The 679 figure.** The exact 30-day URL returned **1,711** on the live page
  header when this run started and ~**1,715–1,716** while it was in flight,
  not 679. 679 may be an earlier snapshot or a personalised/filtered session.
  The rankings here use the live 30-day pool.
- **Mass postings distort raw counts.** Accenture's `Custom Software Engineer`
  is 109 distinct job IDs from one employer; Shashwath Solution's `Python
  Lead` (11) and `SFDC Developer` (10) are also one-employer campaigns. Use the
  employer-breadth table for market breadth.
- **The two lenses are not the same query.** Skills use 8 keyword phrases,
  3 cities, 7 days; roles use `.net core`, 4 cities, 30 days. Do not compare
  percentages across lenses as if they shared a denominator.
- **Recruiter tags are noisy.** `ASP.NET` is used as a generic chip even for
  Core roles; Entity Framework Core is barely tagged. Absence from the top 10
  is not proof a skill is unused.
- **Point-in-time.** Naukri counts and page composition move during a run.
  Re-run both lenses before making a refreshed comparison.
- **No evasion.** A later browser re-check hit Naukri's CAPTCHA; the run
  stopped rather than retry or bypass it. The API collection had already
  completed. This project stays a polite, low-volume collector, not an
  anti-detect stack (see `docs/BOT_DETECTION.md`).

## 5. Reproduce

### Skills lens

```bash
curl -s -X POST http://127.0.0.1:8000/api/skills \
  -H 'Content-Type: application/json' \
  -d '{
    "keywords": "c#, asp.net core, asp.net core mvc, asp.net web api, .net application developer, full stack .net developer, net fullstack, entity framework core",
    "location": "pune, hyderabad, bangalore",
    "experience": 6,
    "days": 7,
    "pages": 23,
    "max_jobs": 500,
    "count_mode": "postings"
  }'
```

### Roles lens

The title scan used the same search-API fast path, one page at a time:

```python
from src.web.nkapi import fetch_search_page

rows, total = fetch_search_page(
    ".net core",
    "pune, hyderabad, bangalore, noida",
    6,      # experience
    30,     # jobAge / freshness in days
    page_no,
)
```

Loop pages 1..`ceil(total / 20)`, sleep 3–6 s between requests, dedupe by
`jobId`, and normalise titles with the rules in §2. This was an analysis run,
not a new API endpoint. No detail-page visits are needed.

## 6. Artifacts

| Artifact | What it contains |
|---|---|
| `output/naukri_skills_top15_20261026.md` | Full skills report, API vs browser, DOM notes |
| `output/naukri_skills_api_20261026.json` | 444 API postings with `tagsAndSkills` |
| `output/naukri_skills_browser_20261026.json` | 435 browser postings with card skills |
| `output/naukri_titles_netcore_30d_20261026.md` | Title-frequency report and caveats |
| `output/naukri_titles_netcore_30d_20261026.csv` | All 827 normalised titles with raw variants and employers |
| `output/title_scan_netcore_30d.json` | Raw 1,709 postings used for the title scan |
| `docs/SPEC-naukri-skills-scan.md` | Living spec for the skills scan |

All `output/` files are gitignored snapshots; regenerate them with the commands
above. The committed record is this document.

## 7. Refresh log

| Date | Change |
|---|---|
| 2026-10-26 | Initial snapshot: 398-posting skills cross-check (7 days) + 1,709-posting title scan (30 days). |

**Refresh checklist:** keep the same keywords/cities/experience/freshness;
record the live count before and after; report both raw postings and employer
breadth; flag any single-employer title above ~5% of the pool; re-check the
skills top 10 against both API and browser before publishing.
