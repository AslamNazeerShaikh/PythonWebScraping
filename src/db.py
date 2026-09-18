"""SQLite access via SQLAlchemy — engine, sessions, and upsert logic.

Design notes:
    - :func:`get_engine` lazily creates ONE process-wide engine (cached in a
      module global). Tests reset it via the ``fresh_db`` fixture.
    - Relative ``sqlite:///jobs.db`` URLs resolve against the project root so
      the app works no matter which directory you launch it from.
    - To move to PostgreSQL later, only ``DATABASE_URL`` changes — every query
      here is dialect-agnostic SQLAlchemy, no raw SQL strings anywhere.
"""
from __future__ import annotations

import logging

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from .config import BASE_DIR, SETTINGS
from .models import Base, Job, JobRow, ScrapeRun

#: Module logger — configured once by :func:`src.log.setup_logging`.
log = logging.getLogger(__name__)

# -- Process-wide engine cache (see get_engine) ------------------------------
_engine = None            # type: ignore[no-untyped-def]  # sqlalchemy Engine
_SessionFactory = None    # type: ignore[no-untyped-def]  # sessionmaker


def _resolve_url(url: str) -> str:
    """Resolve a relative ``sqlite:///jobs.db`` URL against the project root.

    Absolute SQLite paths (``sqlite:////abs/path``) and server URLs
    (``postgresql://…``) pass through untouched.
    """
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        rel = url[len("sqlite:///"):]
        return f"sqlite:///{(BASE_DIR / rel).resolve()}"
    return url


def get_engine():  # type: ignore[no-untyped-def]
    """Return the cached engine, creating it (and the session factory) first."""
    global _engine, _SessionFactory
    if _engine is None:
        url = _resolve_url(SETTINGS.database_url)
        _engine = create_engine(url, future=True)
        _SessionFactory = sessionmaker(bind=_engine, class_=Session,
                                       expire_on_commit=False)
    return _engine


def init_db() -> None:
    """Create ``jobs`` / ``scrape_runs`` tables if they don't exist (idempotent)."""
    get_engine()
    Base.metadata.create_all(_engine)
    log.info("DB ready")


def get_session() -> Session:
    """Open a new ORM session from the shared factory."""
    get_engine()
    assert _SessionFactory is not None  # guaranteed by get_engine()
    return _SessionFactory()


def upsert_jobs(jobs: list[Job]) -> tuple[int, int]:
    """Insert new jobs; refresh already-seen rows and bump ``last_seen``.

    Args:
        jobs: Validated jobs from the scraper (or the offline ``parse`` cmd).

    Returns:
        ``(new_count, total_count)`` — e.g. ``(3, 60)`` means 3 unseen jobs
        out of 60 processed. Empty input short-circuits to ``(0, 0)``.
    """
    if not jobs:
        return 0, 0
    new = 0
    with get_session() as s:
        for job in jobs:
            row = s.get(JobRow, job.job_id)
            if row is None:
                # First sighting — full insert (first_seen defaults to now).
                s.add(JobRow.from_job(job))
                new += 1
            else:
                # Re-seen — refresh mutable fields so edits on Naukri propagate,
                # and touch last_seen so “still live” is queryable.
                for attr, value in {
                    "title": job.title, "company": job.company,
                    "location": job.location, "experience": job.experience,
                    "salary": job.salary, "posted": job.posted,
                    "url": job.url, "apply_url": job.apply_url or job.url,
                    "snippet": job.snippet, "description": job.description,
                    "skills": job.skill_text(),
                    "search_location": job.search_location,
                }.items():
                    setattr(row, attr, value)
                row.last_seen = func.now()  # type: ignore[assignment]
        s.commit()
    log.info("Upserted %d jobs (%d new)", len(jobs), new)
    return new, len(jobs)


def record_run(keywords: str, locations: str, pages: int,
               found: int, new_jobs: int) -> None:
    """Append one audit row to ``scrape_runs`` for this pipeline execution."""
    with get_session() as s:
        s.add(ScrapeRun(keywords=keywords, locations=locations,
                        pages=pages, found=found, new_jobs=new_jobs))
        s.commit()


def fetch_all_jobs(limit: int = 5000) -> list[Job]:
    """Return the freshest jobs (by ``last_seen`` desc) as validated models."""
    with get_session() as s:
        rows = s.scalars(
            select(JobRow).order_by(JobRow.last_seen.desc()).limit(limit)
        ).all()
        return [r.to_job() for r in rows]


def count_jobs() -> int:
    """Return the total number of unique jobs stored."""
    with get_session() as s:
        return s.scalar(select(func.count()).select_from(JobRow)) or 0
