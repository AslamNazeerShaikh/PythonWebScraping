"""Layer 5 (analysis/output): Pandas over SQLite → CSV / Excel snapshots.

Ownership rule: **SQLite is the source of truth**; files produced here are
disposable point-in-time snapshots for quick filtering/sharing. Re-running an
export never touches the database.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from sqlalchemy import select

from .config import SETTINGS
from .db import get_engine
from .models import EmailRow, JobRow

#: Module logger — configured once by :func:`src.log.setup_logging`.
log = logging.getLogger(__name__)

#: Column order for every export (kept stable so diffs stay readable).
COLUMNS = ["job_id", "title", "company", "location", "search_location",
           "experience", "salary", "posted", "url", "apply_url",
           "skills", "first_seen", "last_seen"]

#: Job-identity columns for the export-time repost collapse: a posting
#: re-listed under a fresh job id keeps the same identity, so it collapses.
#: ``search_location`` is deliberately NOT here — it describes the *search*,
#: not the posting (and both lanes use the same combined-city string).
DEDUPE_KEYS = ["title", "company", "location", "experience"]


def _external_apply_url(apply_url: str) -> bool:
    """True when ``apply_url`` leaves Naukri for a company careers/ATS portal.

    The lane recipe applies **on Naukri**, so postings whose apply flow
    redirects to the employer's own portal (``companyApplyJob`` rows at
    collect time, browser-enriched external links at export time) stay out.
    An empty value/host means "falls back to the Naukri job URL" → kept.
    """
    host = urlparse(apply_url or "").netloc.casefold()
    return bool(host) and not host.removeprefix("www.").endswith("naukri.com")


def _dedupe(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse near-identical reposts (``job_id`` differs, identity doesn't).

    Rows arrive freshest-first (``last_seen DESC``), so the first occurrence
    of an identity is kept. Always on — a duplicate is never useful in an
    apply sheet.
    """
    if df.empty:
        return df
    key = df[DEDUPE_KEYS].astype(str).apply(
        lambda col: col.str.strip().str.casefold())
    return df[~key.duplicated()]


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
              location_match: str = "contains",
              exclude_unwanted: bool = True) -> pd.DataFrame:
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
        exclude_unwanted: Drop the lane-quality gates' casualties — postings
            matching neither lane (:func:`src.naukri_scraper.should_exclude_irrelevant_job`),
            pure-frontend roles (:func:`src.naukri_scraper.should_exclude_frontend_job`),
            and postings whose ``apply_url`` leaves Naukri for the company's
            own portal (:func:`_external_apply_url`). ``False`` keeps them.
            The repost collapse (:func:`_dedupe`) is always on.
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
    if exclude_unwanted and not df.empty:
        from .naukri_scraper import (should_exclude_frontend_job,
                                     should_exclude_irrelevant_job)

        def _keep_wanted(row) -> bool:  # type: ignore[no-untyped-def]
            skills = [s.strip() for s in
                      str(row.get("skills") or "").split(",")]
            title = str(row.get("title") or "")
            snippet = str(row.get("snippet") or "")
            return (not should_exclude_irrelevant_job(title, skills, snippet)
                    and not should_exclude_frontend_job(title, skills, snippet)
                    and not _external_apply_url(str(row.get("apply_url") or "")))

        before = len(df)
        df = df[df.apply(_keep_wanted, axis=1)]
        if len(df) != before:
            log.info("Export gates dropped %d unwanted rows", before - len(df))
    df = _dedupe(df)
    return df[COLUMNS]


def export_jobs(fmt: str = "csv", location: str = "",
                out_path: str | None = None,
                exclude_java: bool = True,
                days: int | None = None,
                location_match: str = "contains",
                exclude_unwanted: bool = True) -> Path:
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
        exclude_unwanted: Forwarded to :func:`load_frame` — the lane-quality
            gates (irrelevant / pure-frontend / external-apply postings).

    Returns:
        Path of the written file.
    """
    df = load_frame(location=location, exclude_java=exclude_java, days=days,
                    location_match=location_match,
                    exclude_unwanted=exclude_unwanted)
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


# ---------------------------------------------------------------------------
# LinkedIn email collector snapshots (docs/SPEC-linkedin-email-collector.md)
# ---------------------------------------------------------------------------
#: Column order for ``contact_emails`` exports (stable, spec-mandated).
EMAIL_COLUMNS = ["email", "post_id", "domain", "author", "posted", "post_url",
                 "snippet", "keyword", "first_seen", "last_seen"]

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

#: ``2h``, ``19h``, ``1w``, ``3mo``, ``1yr``.
_RELATIVE_RE = re.compile(r"^(\d+)\s*(mo|yr|[smhdw])$", re.I)

#: ``Oct 13`` or ``Oct 13, 2025``.
_MONTH_DAY_RE = re.compile(
    r"^([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2})(?:,\s*(\d{4}))?$")

#: ISO-ish fallback (``2026-10-13`` / ``2026-10-13T09:00:00``).
_ISO_RE = re.compile(r"^\d{4}-\d{1,2}-\d{1,2}(?:[t ].*)?$")


def _email_domain(email: str) -> str:
    """Return the lowercased domain after ``@`` (empty for malformed rows)."""
    return str(email or "").rsplit("@", 1)[-1].strip().lower()


def _naive_timestamp(value: object) -> pd.Timestamp:
    """Coerce to a naive UTC-ish Timestamp (SQLite stores naive UTC)."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is not None:
        ts = ts.tz_localize(None)
    return ts


def _posted_timestamp(posted: str, reference: object) -> pd.Timestamp:
    """Approximate a post's publication time from LinkedIn's label.

    ``posted`` is what the feed shows (``19h``, ``2d``, ``Oct 13``,
    ``Oct 13, 2025``). Relative labels resolve against ``reference``
    (``last_seen``/``first_seen``); month-day labels without a year use the
    reference year, stepping back one year when that would be in the future.

    Returns ``NaT`` for an empty/unparseable label. That is deliberate: an
    unknown date must never outrank a post with a real date during the
    "newest post" collapse (the caller falls back to ``last_seen`` only when
    every candidate is unknown).
    """
    ref = _naive_timestamp(reference)
    if pd.isna(ref):
        ref = pd.Timestamp.now(tz="UTC").tz_localize(None)
    text = str(posted or "").strip().lower()
    if not text:
        return pd.NaT
    if text in ("just now", "now", "today"):
        return ref

    relative = _RELATIVE_RE.fullmatch(text)
    if relative:
        amount = int(relative.group(1))
        unit = relative.group(2).lower()
        days = {"d": 1, "w": 7}.get(unit, 0)
        if unit == "mo":
            days = 30
        elif unit == "yr":
            days = 365
        if days:
            return ref - pd.Timedelta(days=amount * days)
        hours = {"h": 1}.get(unit, 0)
        if hours:
            return ref - pd.Timedelta(hours=amount)
        minutes = {"m": 1}.get(unit, 0)
        if minutes:
            return ref - pd.Timedelta(minutes=amount)
        return ref - pd.Timedelta(seconds=amount)

    month_day = _MONTH_DAY_RE.fullmatch(text)
    if month_day:
        month = _MONTHS.get(month_day.group(1).lower())
        if month:
            day = int(month_day.group(2))
            year = int(month_day.group(3)) if month_day.group(3) else ref.year
            try:
                stamp = pd.Timestamp(year=year, month=month, day=day)
            except ValueError:
                return pd.NaT
            if stamp > ref + pd.Timedelta(days=1):
                try:
                    stamp = stamp.replace(year=year - 1)
                except ValueError:      # 29 Feb in a non-leap year
                    return pd.NaT
            return stamp

    if not _ISO_RE.fullmatch(text):
        return pd.NaT
    try:
        stamp = pd.Timestamp(text)
    except (TypeError, ValueError):
        return pd.NaT
    return _naive_timestamp(stamp)


def _latest_email_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Keep one row per email (newest post) and sort domain → email.

    Rules:
      * the row's searched ``domain`` must equal the email's own domain —
        legacy/contaminated rows are discarded, never exported;
      * duplicate addresses collapse to the row with the newest post label;
      * output is grouped alphabetically by domain, then by email.
    """
    if df.empty:
        return df
    df = df.copy()
    df["email"] = df["email"].astype(str).str.strip().str.lower()
    df["domain"] = df["domain"].fillna("").astype(str).str.strip().str.lower()
    keyword_domain = (df["keyword"].fillna("").astype(str).str.strip()
                      .str.lower().str.lstrip("@"))
    searched = df["domain"].str.lstrip("@")
    searched = searched.where(searched.ne(""), keyword_domain)
    df["domain"] = searched

    email_domain = df["email"].map(_email_domain)
    df = df[searched.ne("") & searched.eq(email_domain)].copy()
    if df.empty:
        return pd.DataFrame(columns=EMAIL_COLUMNS)

    reference = df["first_seen"].where(df["first_seen"].notna(),
                                       df["last_seen"])
    df["_latest_at"] = [
        _posted_timestamp(posted, ref)
        for posted, ref in zip(df["posted"], reference)
    ]
    df = df.sort_values(
        ["domain", "email", "_latest_at", "last_seen"],
        ascending=[True, True, False, False],
        kind="mergesort",
    )
    df = df.drop_duplicates(subset=["email"], keep="first")
    df["_domain_key"] = df["domain"].str.casefold()
    df["_email_key"] = df["email"].str.casefold()
    df = df.sort_values(["_domain_key", "_email_key"], kind="mergesort")
    return df[EMAIL_COLUMNS].reset_index(drop=True)


def load_email_frame(limit: int = 5000) -> pd.DataFrame:
    """Load harvested emails, one row per address, newest post evidence.

    Args:
        limit: Max unique addresses returned (default 5000). All raw rows are
            read so the newest-post choice is never truncated mid-email.

    Returns:
        A DataFrame with :data:`EMAIL_COLUMNS`: mismatched-domain rows are
        dropped, duplicate addresses keep their newest post, and rows are
        ordered by domain then email. Empty DB still yields the columns.
    """
    engine = get_engine()
    stmt = select(EmailRow).order_by(EmailRow.last_seen.desc())
    with engine.connect() as conn:
        df = pd.read_sql(stmt, conn)
    if df.empty:
        return pd.DataFrame(columns=EMAIL_COLUMNS)
    return _latest_email_frame(df).head(limit).reset_index(drop=True)


def export_emails(fmt: str = "excel", out_path: str | None = None,
                  limit: int = 5000) -> Path:
    """Export the harvested-email snapshot to Excel or CSV.

    SQLite stays the source of truth; the file is a disposable snapshot.

    Args:
        fmt: ``"excel"`` (default, ``.xlsx``) or ``"csv"``.
        out_path: Explicit destination; otherwise a timestamped
            ``linkedin_emails_<ts>.xlsx|.csv`` under ``SETTINGS.output_dir``.
        limit: Forwarded to :func:`load_email_frame`.

    Returns:
        Path of the written file.
    """
    df = load_email_frame(limit=limit)
    out_dir = SETTINGS.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    if out_path:
        dest = Path(out_path)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = "xlsx" if fmt == "excel" else "csv"
        dest = out_dir / f"linkedin_emails_{ts}.{suffix}"
    if fmt == "excel":
        df.to_excel(dest, index=False)
    else:
        df.to_csv(dest, index=False)
    log.info("Exported %d emails -> %s", len(df), dest)
    return dest
