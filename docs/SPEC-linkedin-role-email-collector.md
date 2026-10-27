# Spec: LinkedIn Role-Targeted Email Collector

Status: IMPLEMENTED 2026-10-27. Ported from the verified one-off scrape without
changing the existing `collect-emails` flow. Live check:
`collect-role-emails --domains ltm.com` returned 7 exact-domain emails from 19
posts, including the previously missed `ASPNET Core` spelling.

## Objective

Collect recruiter emails from LinkedIn **content search** for a role phrase
scoped to a company domain, e.g.:

```text
asp.net core @ltm.com
```

The collector must:

1. Search the exact query on LinkedIn's content-search surface.
2. Sort by **Latest** using the native array form:
   `sortBy=["date_posted"]`.
3. Read the latest feed, stop after 20 posts when 10 unique emails are found,
   otherwise extend to a hard cap of 30 posts.
4. Expand every “more” control before reading.
5. Keep only emails on the **exact searched company domain**.
6. Keep only hiring posts that explicitly mention the role phrase; a hashtag
   mention such as `#ASPNETCore` is not enough.
7. Avoid multi-role mis-association (the Wipro case): a company email in one
   job section must not be attributed to an ASP.NET Core requirement in a
   different section.
8. Write a multi-sheet Excel workbook with the email list, evidence, summary,
   scanned posts, and method.

The existing broad collector (`collect-emails`) stays unchanged, including its
SQLite storage and `@<domain>` search path.

## Commands

```bash
# Default: asp.net core + the 15 requested domains
python -m src.main collect-role-emails

# Explicit subset / phrase
python -m src.main collect-role-emails \
  --phrase "asp.net core" \
  --domains ltm.com,capgemini.com,tcs.com \
  --target 10 --checkpoint-posts 20 --max-posts 30 \
  --out output/linkedin_role_emails.xlsx

# Gates
pytest
graphify update .
```

## Project structure

```text
src/
  linkedin_role_email.py     # new: URL builder, filters, browser loop, workbook
  main.py                    # new CLI command only; existing commands untouched
tests/
  test_role_email_collector.py
docs/
  SPEC-linkedin-role-email-collector.md
tasks/
  plan.md                    # appended section
  todo.md                    # appended checklist
output/
  linkedin_role_emails_<ts>.xlsx  # gitignored
```

## Design decisions

- **No SQLite writes.** This is an analysis artifact and does not change the
  `contact_emails` schema or the existing collector's dedupe semantics.
- **New module, not a rewrite.** Shared browser helpers are imported from
  `linkedin_email_scraper.py`; existing functions are not modified.
- **Exact URL shape** from the verified scrape:
  `keywords=<phrase>%20%40<domain>&origin=FACETED_SEARCH&sortBy=%5B%22date_posted%22%5D`.
- **Pydantic row model** for the output, with email/domain validation.
- **Section guard.** Split on strong multi-role separators (`━━`, `══`, long
  rules) and require the phrase match and email match to be in the same
  section. This removes the Wipro BPO-email false positive without a manual
  blocklist.
- **Best-effort post URL.** LinkedIn content search often exposes only an
  opaque post id; the workbook always carries that id as `post_reference`.
- **No evasion.** No CAPTCHA solving, proxy rotation, fingerprint spoofing, or
  retry loops against a wall.

## Workbook

| Sheet | Contents |
|---|---|
| `Email List` | `email, company, company_domain, role, location, posted, post_rank, author, post_reference` |
| `Emails` | Full evidence: phrase snippet, email context, post excerpt, query, URL |
| `Summary` | Per-domain posts scanned, phrase posts, unique emails, target/status |
| `Posts Scanned` | Audit trail including posts with no email |
| `Method` | Query, sort, gates, limits, caveats |

## Testing strategy

- Offline pytest only; no live LinkedIn.
- Pure-function tests: URL encoding, phrase matching, hashtag masking, exact
  domain parsing, section guard, role/location extraction, dedupe.
- FakePage tests: navigation retry, no-results, wall/login stop, 20-post stop,
  30-post extension, scroll stall, extraction failure.
- Workbook test: all five sheets, rows, headers, empty-safe.
- CLI test: delegation, invalid limits, checkpoint output, no-email message.
- Coverage gate stays `--cov-fail-under=100`.

## Boundaries

- **Always:** keep existing commands/tests green; 100% coverage; polite pauses;
  exact domain match; no wall bypass.
- **Ask first:** new dependencies, DB schema changes, scheduler/API surface.
- **Never:** modify `collect-emails` behavior; commit `output/`, `.env`, or
  `jobs.db`; scrape while signed out; solve CAPTCHAs.

## Success criteria

1. `collect-role-emails --domains ltm.com` writes an Excel workbook and leaves
   `collect-emails` behavior/tests unchanged.
2. The URL contains `sortBy=%5B%22date_posted%22%5D` and no `datePosted`.
3. A synthetic Wipro-style multi-role post keeps the .NET-section email and
   drops the BPO-section email.
4. Hashtag-only `#ASPNETCore` posts are rejected.
5. 20-post stop and 30-post extension are both covered by tests.
6. Full suite passes at 100% coverage.
