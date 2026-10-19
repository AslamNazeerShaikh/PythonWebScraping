"""Layer 5 (analysis/output): Pandas over SQLite → CSV / Excel snapshots.

Ownership rule: **SQLite is the source of truth**; files produced here are
disposable point-in-time snapshots for quick filtering/sharing. Re-running an
export never touches the database.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import select

from .config import SETTINGS
from .db import get_engine
from .models import JobRow

#: Module logger — configured once by :func:`src.log.setup_logging`.
log = logging.getLogger(__name__)

#: Column order for every export (kept stable so diffs stay readable).
COLUMNS = ["job_id", "title", "company", "location", "search_location",
           "experience", "salary", "posted", "url", "apply_url",
           "skills", "first_seen", "last_seen"]


def fresh_cutoff(days: int) -> datetime:
    """Naive UTC cutoff for "first seen within the last ``days`` days".

    ``first_seen``/``last_seen`` are written by SQLite's
    ``CURRENT_TIMESTAMP``, which is UTC — so the comparison must be UTC too.
    A local-time cutoff would shift every window by the machine's UTC offset
    (18.5h instead of 24h from IST).
    """
    return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)


def load_frame(location: str = "", limit: int = 5000,
              exclude_java: bool = True,
              days: int | None = None,
              location_match: str = "contains") -> pd.DataFrame:
    """Load jobs from SQLite into a :class:`~pandas.DataFrame`.

    Args:
        location: Optional case-insensitive filter matched against BOTH the
            job's own ``location`` and the ``search_location`` it was found
            under (e.g. ``"pune"``). Empty string disables filtering.
        limit: Max rows, freshest first (mirrors :func:`src.db.fetch_all_jobs`).
        exclude_java: Drop pure-Java postings (Java stack, no .NET anchor —
            see :func:`src.naukri_scraper.should_exclude_java_job`) so the
            Excel never carries them. ``False`` keeps every row.
        days: Freshness window — keep only rows whose ``first_seen`` falls
            within the last N days (``days=1`` → the last 24h, i.e. what a
            ``days: 1`` collect just brought in). ``None`` keeps the whole DB.
        location_match: ``"contains"`` (default) treats ``location`` as a
            substring, so ``"pune"`` also matches the combined
            ``"pune,hyderabad,bengaluru"`` search string; ``"exact"`` keeps
            only rows whose city equals the needle (the "Pune-only" sheet).
    """
    engine = get_engine()
    stmt = select(JobRow).order_by(JobRow.last_seen.desc())
    if days:
        stmt = stmt.where(JobRow.first_seen >= fresh_cutoff(days))
    stmt = stmt.limit(limit)
    with engine.connect() as conn:
        df = pd.read_sql(stmt, conn)
    if location:
        # Match either column — a Hyderabad-found job may list "Pune" and v.v.
        if location_match == "exact":
            # City equality: "pune" must NOT pass "pune,hyderabad,bengaluru"
            # (the 3-city search_location), which substring matching lets through.
            needle = location.strip().casefold()
            own = df["location"].fillna("").astype(str).str.strip()
            where = df["search_location"].fillna("").astype(str).str.strip()
            mask = (own.str.casefold() == needle) | \
                (where.str.casefold() == needle)
        else:
            mask = df["location"].str.contains(location, case=False, na=False) | \
                df["search_location"].str.contains(location, case=False, na=False)
        df = df[mask]
    if exclude_java and not df.empty:
        from .naukri_scraper import should_exclude_java_job

        def _keep(row) -> bool:  # type: ignore[no-untyped-def]
            skills = [s.strip() for s in
                      str(row.get("skills") or "").split(",")]
            return not should_exclude_java_job(
                str(row.get("title") or ""), skills,
                str(row.get("snippet") or ""),
                str(row.get("description") or ""))

        df = df[df.apply(_keep, axis=1)]
    return df[COLUMNS]


def export_jobs(fmt: str = "csv", location: str = "",
                out_path: str | None = None,
                exclude_java: bool = True,
                days: int | None = None,
                location_match: str = "contains") -> Path:
    """Export the current DB snapshot to CSV or Excel.

    Args:
        fmt: ``"csv"`` (default) or ``"excel"`` (``.xlsx`` via openpyxl).
        location: Forwarded to :func:`load_frame` for pre-export filtering.
        out_path: Explicit destination; otherwise a timestamped file under
            ``OUTPUT_DIR`` (``naukri_export_<ts>.csv|.xlsx``).
        exclude_java: Forwarded to :func:`load_frame` (pure-Java filter).
        days: Forwarded to :func:`load_frame` — only rows first seen within
            the last N days (``None`` exports everything).
        location_match: Forwarded to :func:`load_frame` — ``"contains"``
            (default) or ``"exact"`` city equality.

    Returns:
        Path of the written file.
    """
    df = load_frame(location=location, exclude_java=exclude_java, days=days,
                    location_match=location_match)
    out_dir = SETTINGS.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    if out_path:
        dest = Path(out_path)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = "xlsx" if fmt == "excel" else "csv"
        dest = out_dir / f"naukri_export_{ts}.{suffix}"
    if fmt == "excel":
        df.to_excel(dest, index=False)
        _hyperlink_titles(dest)
    else:
        df.to_csv(dest, index=False)
    log.info("Exported %d rows -> %s", len(df), dest)
    return dest


def _hyperlink_titles(path: Path) -> None:
    """Turn title cells into clickable apply hyperlinks (Excel-ready).

    Display text stays the job title; the link target is the apply URL
    (falling back to the listing URL). Plain-text URL columns already
    auto-linkify in Excel/Calc; this makes the title itself the link.
    """
    from openpyxl import load_workbook

    workbook = load_workbook(path)
    sheet = workbook.active
    headers = [cell.value for cell in sheet[1]]
    title_idx = headers.index("title") + 1
    url_idx = headers.index("apply_url") + 1
    for row in sheet.iter_rows(min_row=2):
        target = row[url_idx - 1].value or ""
        if target:
            row[title_idx - 1].hyperlink = target
            row[title_idx - 1].style = "Hyperlink"
    workbook.save(path)
