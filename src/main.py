"""Typer CLI + Rich output — the app's front door.

Commands (``python -m src.main <cmd> --help`` for details)::

    scrape          Full pipeline: browser → Pydantic → SQLite + JSON/CSV files.
    export          SQLite → CSV/Excel snapshots (Pandas).
    stats           DB overview table.
    parse           Offline re-parse of saved HTML (BS4+lxml, no browser needed).
    schedule        Daily runs at given hours (APScheduler, blocking).
    collect-emails  Harvest recruiter emails from LinkedIn posts → SQLite + Excel.
    collect-role-emails  Role-specific @domain search → five-sheet Excel (no DB).
    export-emails   contact_emails → Excel/CSV snapshot.

:func:`do_scrape` holds the shared pipeline so both the ``scrape`` command
and the scheduler execute identical logic.
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from playwright.sync_api import sync_playwright
from rich.console import Console
from rich.table import Table

from .config import BASE_DIR, SETTINGS
from .db import (count_emails, count_jobs, fetch_all_jobs, init_db,
                 record_run, upsert_emails, upsert_jobs)
from .domain_targets import DomainTarget, parse_domain_targets
from .export import export_emails, export_jobs, load_email_frame
from .linkedin_email_scraper import run_collect
from .linkedin_role_email import (CHECKPOINT_POSTS, DEFAULT_PHRASE,
                                  MAX_POSTS, TARGET_EMAILS, parse_domains,
                                  run_role_collect, write_role_workbook)
from .log import setup_logging
from .models import Job
from .naukri_scraper import run_scrape, save_results
from .stealth_browser import launch_context

#: Typer app — each ``@app.command()`` function below becomes a subcommand.
app = typer.Typer(help="Secure Naukri.com job collector (personal use).")

#: Shared Rich console for tables/status (test-friendly: prints to stdout).
console = Console()


def _ensure_env(base_dir: Path = BASE_DIR) -> None:
    """One-time startup setup: ``.env`` bootstrap + logging + DB tables.

    Args:
        base_dir: Project root (parameterised — and defaulted — so tests can
            point it at a tmp dir to cover the “first run, no .env” branch
            without touching the real project files).
    """
    # First-run convenience: seed `.env` from the documented example.
    if not (base_dir / ".env").exists() and (base_dir / ".env.example").exists():
        shutil.copy(base_dir / ".env.example", base_dir / ".env")
        console.print("[dim]Created .env from .env.example[/dim]")
    setup_logging(SETTINGS.log_level)
    init_db()


def do_scrape() -> int:
    """Execute the shared scrape pipeline; return process exit code.

    Opens the browser, collects + validates jobs, upserts them into SQLite,
    records the run, writes JSON/CSV snapshots, and prints the top apply
    links. Empty result is exit ``0`` with guidance (not an error — widening
    keywords or running headful usually fixes it).
    """
    setup_logging(SETTINGS.log_level)
    init_db()
    with sync_playwright() as p:
        context = launch_context(p)
        try:
            jobs = run_scrape(context)
        finally:
            context.close()
    if not jobs:
        console.print("[yellow]No jobs found — widen keywords/days or run headful.[/yellow]")
        return 0
    new, total = upsert_jobs(jobs)
    record_run(SETTINGS.keywords, ",".join(SETTINGS.locations),
               SETTINGS.max_pages_per_search, found=total, new_jobs=new)
    save_results(jobs)
    _print_jobs(jobs[:20])
    console.print(f"[green]Done:[/green] {total} jobs ({new} new) -> SQLite + output/")
    return 0


def do_collect_emails(domains: list[str] | None,
                      max_scrolls: int | None = None,
                      targets: dict[str, int] | None = None) -> int:
    """Run the LinkedIn email collector; return process exit code.

    One browser, one search per domain. Each domain is searched for
    ``"@<domain>"``, switched to the native Posts view, sorted Latest +
    Past month, and scrolled only until its unique-email target is met.
    Every batch is upserted and the checkpoint workbook is rewritten.
    """
    setup_logging(SETTINGS.log_level)
    init_db()
    if targets is None:
        domains = domains or SETTINGS.email_domains
        targets = {d: SETTINGS.email_default_target for d in domains}
    totals = {"new": 0}
    persisted: set[tuple[str, str]] = set()
    out_dir = SETTINGS.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    partial = out_dir / "linkedin_emails_partial.xlsx"

    def _persist(batch: list[EmailContact]) -> None:
        """Upsert one batch and rewrite the checkpoint workbook."""
        if not batch:
            return
        keys = {(c.email, c.post_id) for c in batch}
        if not (keys - persisted):
            return
        new, _ = upsert_emails(batch)
        totals["new"] += new
        persisted.update(keys)
        export_emails(fmt="excel", out_path=str(partial))

    with sync_playwright() as p:
        context = launch_context(p)
        try:
            contacts = run_collect(context, domains=list(targets),
                                   max_scrolls=max_scrolls,
                                   on_batch=_persist, targets=targets)
        finally:
            context.close()

    # Mocked/legacy callers may return contacts without invoking the hook;
    # persist anything the callback did not already see.
    remaining = [c for c in contacts if (c.email, c.post_id) not in persisted]
    if remaining:
        _persist(remaining)
    if not contacts and totals["new"] == 0 and count_emails() == 0:
        console.print("[yellow]No emails found — check login state "
                      "(first run headful) or widen the date facet.[/yellow]")
        return 0
    dest = export_emails(fmt="excel")
    unique = len(load_email_frame())
    console.print(f"[green]Done:[/green] {unique} unique emails "
                  f"({totals['new']} new) -> SQLite + {dest}")
    console.print(f"[dim]Checkpoints:[/dim] {partial}")
    return 0


def do_collect_role_emails(domains: list[str], phrase: str,
                           target: int, checkpoint_posts: int,
                           max_posts: int, pause_s: int,
                           out: str | None, headless: bool) -> int:
    """Run the role-targeted LinkedIn collector; return process exit code.

    This path is intentionally separate from :func:`do_collect_emails`: it
    writes a multi-sheet Excel artifact and never touches SQLite.
    """
    setup_logging(SETTINGS.log_level)
    SETTINGS.headless = headless or SETTINGS.headless
    out_path = (Path(out) if out else SETTINGS.output_dir /
                f"linkedin_role_emails_{datetime.now():%Y%m%d_%H%M%S}.xlsx")

    def _checkpoint(rows, posts, summary) -> None:
        write_role_workbook(out_path, rows, posts, summary, phrase, target,
                            checkpoint_posts, max_posts)

    with sync_playwright() as p:
        context = launch_context(p)
        try:
            contacts, posts, summary = run_role_collect(
                context, domains, phrase, target, checkpoint_posts, max_posts,
                pause_s, on_domain=_checkpoint)
        finally:
            context.close()

    write_role_workbook(out_path, contacts, posts, summary, phrase, target,
                        checkpoint_posts, max_posts)
    if not contacts:
        console.print("[yellow]No role emails found — check login state or "
                      "widen the phrase/domains.[/yellow]")
        return 0
    hits = len({contact.company_domain for contact in contacts})
    console.print(f"[green]Done:[/green] {len(contacts)} role emails across "
                  f"{hits} domains -> {out_path}")
    return 0


def _print_jobs(jobs: list[Job]) -> None:
    """Render jobs as a Rich table (title/company/location/apply URL)."""
    table = Table(title="Top apply links", show_lines=False)
    table.add_column("Title", max_width=55)
    table.add_column("Company", max_width=22)
    table.add_column("Loc", max_width=14)
    table.add_column("Apply URL", max_width=60)
    for j in jobs:
        table.add_row(j.title[:55], (j.company or "")[:22],
                      (j.location or j.search_location)[:14], j.apply_url or j.url)
    console.print(table)


@app.command()
def scrape(
    keywords: str = typer.Option(SETTINGS.keywords, help="Search keywords"),
    locations: str = typer.Option(",".join(SETTINGS.locations),
                                  help="Comma-separated, e.g. 'pune,hyderabad'"),
    experience: int = typer.Option(SETTINGS.experience),
    days: int = typer.Option(SETTINGS.date_filter, help="Posted within last N days"),
    pages: int = typer.Option(SETTINGS.max_pages_per_search),
    max_jobs: int = typer.Option(SETTINGS.max_jobs_total),
    enrich: bool = typer.Option(True, "--enrich/--no-enrich",
                                help="Visit each job page for details"),
    browser: str = typer.Option(SETTINGS.browser, help="browser engine (chromium)"),
    headless: bool = typer.Option(False, "--headless", help="Background run"),
) -> None:
    """Run the full scrape pipeline (browser -> Pydantic -> SQLite + files)."""
    _ensure_env()
    # CLI flags override .env defaults for this run only.
    SETTINGS.keywords = keywords
    SETTINGS.locations = [s.strip().lower() for s in locations.split(",") if s.strip()]
    SETTINGS.experience = experience
    SETTINGS.date_filter = days
    SETTINGS.max_pages_per_search = pages
    SETTINGS.max_jobs_total = max_jobs
    SETTINGS.enrich_details = enrich
    SETTINGS.browser = browser
    SETTINGS.headless = headless or SETTINGS.headless
    console.print(f"[bold]Scraping[/bold] '{keywords}' in {SETTINGS.locations} "
                  f"| exp={experience}y | last {days}d | {browser}")
    console.print("[dim]Personal use only — polite delays + caps are built in.[/dim]")
    raise typer.Exit(code=do_scrape())


@app.command()
def export(
    fmt: str = typer.Option("csv", "--format", help="csv or excel"),
    location: str = typer.Option("", help="Filter, e.g. 'pune'"),
    out: Optional[str] = typer.Option(None, help="Output path"),
    exclude_java: bool = typer.Option(True, "--exclude-java/--include-java",
                                      help="Drop pure-Java postings (default on)"),
    exclude_unwanted: bool = typer.Option(
        True, "--exclude-unwanted/--include-unwanted",
        help="Drop irrelevant / pure-frontend / company-portal postings "
             "(default on)"),
    days: Optional[int] = typer.Option(
        None, "--days",
        help="Only rows first seen in the last N days (default: whole DB)"),
    location_match: str = typer.Option(
        "contains", "--location-match",
        help="contains (default, substring) or exact city equality"),
) -> None:
    """Export SQLite -> CSV/Excel snapshot (Pandas)."""
    _ensure_env()
    if fmt not in ("csv", "excel"):
        console.print("[red]--format must be csv or excel[/red]")
        raise typer.Exit(code=2)
    if location_match not in ("contains", "exact"):
        console.print("[red]--location-match must be contains or exact[/red]")
        raise typer.Exit(code=2)
    dest = export_jobs(fmt=fmt, location=location, out_path=out,
                       exclude_java=exclude_java, days=days,
                       location_match=location_match,
                       exclude_unwanted=exclude_unwanted)
    console.print(f"[green]Exported ->[/green] {dest}")


@app.command("collect-emails")
def collect_emails(
    domains: str = typer.Option(
        "", help="Comma-separated domains (default: EMAIL_DOMAINS, 11 targets)"),
    input_csv: Optional[str] = typer.Option(
        None, "--input-csv", "--csv",
        help="CSV of '@domain:unique_email_target' entries (searched in order)"),
    max_scrolls: Optional[int] = typer.Option(
        None, help="Max scroll rounds per domain (default: EMAIL_MAX_SCROLLS)"),
    headless: bool = typer.Option(False, "--headless", help="Background run"),
) -> None:
    """Harvest domain-matching emails from the Latest/Past-month posts feed.

    Each CSV entry ``@cognizant.com:5`` searches for ``"@cognizant.com"``,
    opens the native Posts tab, sorts Latest + Past month, and scrolls only
    until 5 distinct ``@cognizant.com`` addresses are found. Non-matching
    domains are discarded, and the Excel keeps one row per address.
    """
    _ensure_env()
    targets: dict[str, int] | None = None
    parsed: list[DomainTarget] = []
    if input_csv:
        try:
            parsed = parse_domain_targets(input_csv,
                                          SETTINGS.email_default_target)
        except (OSError, ValueError) as exc:
            console.print(f"[red]Invalid --input-csv:[/red] {exc}")
            raise typer.Exit(code=2)
        targets = {item.domain: item.target for item in parsed}
        doms: list[str] | None = list(targets)
    else:
        doms = [d.strip().lower().lstrip("@")
                for d in domains.split(",") if d.strip()] or None
        if doms:
            targets = {d: SETTINGS.email_default_target for d in doms}
    SETTINGS.headless = headless or SETTINGS.headless
    description = (", ".join(f"{d}:{t}" for d, t in targets.items())
                   if targets else str(doms or SETTINGS.email_domains))
    console.print(f"[bold]Collecting emails[/bold] for {description} "
                  f"| facet={SETTINGS.email_date_facet} "
                  f"| max-scrolls={max_scrolls or SETTINGS.email_max_scrolls}")
    console.print("[dim]Personal use only — never auto-solves CAPTCHAs.[/dim]")
    raise typer.Exit(code=do_collect_emails(doms, max_scrolls, targets))


@app.command("collect-role-emails")
def collect_role_emails(
    phrase: str = typer.Option(DEFAULT_PHRASE, help="Role phrase, e.g. 'asp.net core'"),
    domains: str = typer.Option(
        "", help="Comma-separated domains (default: the 15 saved targets)"),
    target: int = typer.Option(
        TARGET_EMAILS, min=1, help="Unique emails to aim for per domain"),
    checkpoint_posts: int = typer.Option(
        CHECKPOINT_POSTS, min=1,
        help="Stop after this many posts if the email target is met"),
    max_posts: int = typer.Option(
        MAX_POSTS, min=1, help="Hard cap on posts read per domain"),
    pause: int = typer.Option(
        15, min=0, help="Seconds between company searches"),
    out: Optional[str] = typer.Option(
        None, help="Output .xlsx path (default: output/linkedin_role_emails_<ts>.xlsx)"),
    headless: bool = typer.Option(False, "--headless", help="Background run"),
) -> None:
    """Collect role-specific recruiter emails into a five-sheet Excel workbook.

    Unlike ``collect-emails`` (broad ``@domain`` search + SQLite), this command
    searches ``"<phrase> @<domain>"`` on the Latest content feed, requires an
    explicit non-hashtag phrase mention, keeps only exact-domain emails, and
    guards against multi-role section mis-association. It does not write SQLite.
    """
    if checkpoint_posts > max_posts:
        console.print("[red]--checkpoint-posts cannot exceed --max-posts[/red]")
        raise typer.Exit(code=2)
    _ensure_env()
    phrase = (phrase or DEFAULT_PHRASE).strip()
    doms = parse_domains(domains)
    SETTINGS.headless = headless or SETTINGS.headless
    console.print(f"[bold]Collecting role emails[/bold] for '{phrase}' "
                  f"across {len(doms)} domains | target={target} "
                  f"| posts={checkpoint_posts}/{max_posts}")
    console.print("[dim]Personal use only — never auto-solves CAPTCHAs.[/dim]")
    raise typer.Exit(code=do_collect_role_emails(
        doms, phrase, target, checkpoint_posts, max_posts, pause, out,
        SETTINGS.headless))


@app.command("export-emails")
def export_emails_cmd(
    fmt: str = typer.Option("excel", "--format", help="excel or csv"),
    out: Optional[str] = typer.Option(None, help="Output path"),
) -> None:
    """Export harvested emails (contact_emails) -> Excel/CSV snapshot."""
    _ensure_env()
    if fmt not in ("csv", "excel"):
        console.print("[red]--format must be csv or excel[/red]")
        raise typer.Exit(code=2)
    dest = export_emails(fmt=fmt, out_path=out)
    console.print(f"[green]Exported ->[/green] {dest}")


@app.command()
def stats() -> None:
    """Show DB overview (total count + freshest 15 as a table)."""
    _ensure_env()
    jobs = fetch_all_jobs(limit=5000)
    console.print(f"[bold]Jobs in DB:[/bold] {count_jobs()} (showing {len(jobs)})")
    _print_jobs(jobs[:15])


@app.command()
def parse(html_path: str) -> None:
    """Offline re-parse saved search HTML into the DB (no browser needed)."""
    _ensure_env()
    from .naukri_scraper import coerce_job
    from .parser import parse_search_html

    html = Path(html_path).read_text(encoding="utf-8")
    raw = parse_search_html(html)
    jobs: list[Job] = []
    for r in raw:
        j = coerce_job(r)
        if j:
            jobs.append(j)
    console.print(f"Parsed {len(raw)} cards -> {len(jobs)} valid Jobs")
    if jobs:
        new, total = upsert_jobs(jobs)
        console.print(f"[green]Upserted:[/green] {total} ({new} new)")
        _print_jobs(jobs[:15])


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
) -> None:
    """Serve the FastAPI control plane (dashboard + REST + MCP + Scalar).

    One process, one port: the dashboard (``/``), Scalar API UI
    (``/scalar``), REST (``/api/...``), and MCP (``/mcp``). Playwright stays
    the hands — every browser pass runs as a cancellable background run.
    """
    _ensure_env()
    import uvicorn

    from .web.main import app as web_app

    console.print(f"[bold]Serving control plane[/bold] on http://{host}:{port} "
                  f"(dashboard + /scalar + /mcp)")
    uvicorn.run(web_app, host=host, port=port)


@app.command()
def schedule(
    hours: str = typer.Option("8,20", help="Comma-separated hours, e.g. '8,12,20'"),
) -> None:
    """Run the scraper daily at the given hours (blocking until Ctrl+C)."""
    _ensure_env()
    parsed = [int(h.strip()) for h in hours.split(",") if h.strip().isdigit()]
    if not parsed:
        console.print("[red]No valid hours given[/red]")
        raise typer.Exit(code=2)
    from .scheduler import run_scheduled
    run_scheduled(parsed)


if __name__ == "__main__":  # `python -m src.main …` entry point
    app()  # pragma: no cover - manual CLI launch, exercised via CliRunner instead
