"""Read-side data access for the web layer (SQLite remains source of truth).

Thin wrappers over :mod:`src.db` with web-friendly shapes: filtering,
pagination, and dashboard aggregates. Writes happen only inside orchestrated
runs, never here.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, inspect, select, text

from ..db import count_jobs, fetch_all_jobs, get_engine, get_session
from ..models import Job, JobRow
from .errors import ApiError, TableNotFound


class JobNotFound(ApiError):
    """Unknown job id."""

    status = 404
    code = "JOB_NOT_FOUND"


def list_jobs(q: str = "", location: str = "",
              page: int = 1, page_size: int = 20) -> tuple[list[Job], int]:
    """Filter + paginate collected jobs (freshest first).

    Args:
        q: Case-insensitive substring over title/company/skills/location.
        location: Matches the job's own location OR its search_location.
        page: 1-based page number. page_size: rows per page.

    Returns:
        ``(rows, total)`` — rows for this page, total matches overall.
    """
    needle = (q or "").strip().lower()
    loc = (location or "").strip().lower()
    jobs = fetch_all_jobs(limit=5000)
    if needle:
        jobs = [j for j in jobs if needle in f"{j.title} {j.company} {j.skill_text()} {j.location}".lower()]
    if loc:
        jobs = [j for j in jobs if loc in (j.location or "").lower() or loc in (j.search_location or "").lower()]
    total = len(jobs)
    start = (page - 1) * page_size
    return jobs[start:start + page_size], total


def get_job(job_id: str) -> Job:
    """Return one job by id or raise :class:`JobNotFound`."""
    with get_session() as session:
        row = session.get(JobRow, job_id)
        if row is None:
            raise JobNotFound(f"no job with id {job_id!r}")
        return row.to_job()


def get_stats(top_n: int = 8) -> dict:
    """Aggregate DB overview for KPIs + charts (safe on an empty DB)."""
    jobs = fetch_all_jobs(limit=5000)
    cutoff = datetime.now() - timedelta(hours=24)  # naive: matches func.now()
    with get_session() as session:
        new_24h = session.scalar(
            select(func.count()).select_from(JobRow)
            .where(JobRow.first_seen >= cutoff)) or 0
    by_loc = Counter(j.location or "Unknown" for j in jobs).most_common(top_n)
    by_co = Counter(j.company or "Unknown" for j in jobs).most_common(top_n)
    return {
        "total_jobs": count_jobs(),
        "new_last_24h": new_24h,
        "by_location": [{"name": name, "count": n} for name, n in by_loc],
        "by_company": [{"name": name, "count": n} for name, n in by_co],
    }


# ---------------------------------------------------------------------------
# Database explorer (serverless SQLite, browsed from the dashboard)
# ---------------------------------------------------------------------------
def list_tables() -> list[dict]:
    """Every user table with columns + row count (explorer overview)."""
    engine = get_engine()
    inspector = inspect(engine)
    tables = []
    with engine.connect() as conn:
        for name in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns(name)]
            total = conn.execute(
                text(f'SELECT COUNT(*) FROM "{name}"')).scalar() or 0
            tables.append({"name": name, "columns": columns, "rows": total})
    return tables


def table_rows(name: str, page: int = 1,
               page_size: int = 20) -> tuple[list[str], list[dict], int]:
    """Paginated rows of one table (name validated against the inspector).

    Returns ``(columns, rows, total)`` with JSON-safe values. Raises
    :class:`TableNotFound` for unknown tables (never interpolates raw input
    into SQL — the name must come from :func:`list_tables` first).
    """
    engine = get_engine()
    inspector = inspect(engine)
    if name not in inspector.get_table_names():
        raise TableNotFound(f"no table {name!r}")
    columns = [c["name"] for c in inspector.get_columns(name)]
    with engine.connect() as conn:
        total = conn.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar() or 0
        rows = conn.execute(
            text(f'SELECT * FROM "{name}" LIMIT :limit OFFSET :offset'),
            {"limit": page_size,
             "offset": (page - 1) * page_size}).mappings().all()
    return columns, [jsonable_encoder(dict(r)) for r in rows], total
