"""Layer 3 (validation: Pydantic) + Layer 4 (persistence: SQLAlchemy ORM).

Data contract for the whole pipeline::

    Website
      ↓  raw HTML
    Parser (in-page JS live, or BeautifulSoup+lxml offline)
      ↓  plain dicts (untrusted — sites change markup without notice)
    Job (Pydantic)  ← ★ validation gate: bad cards fail HERE with a field name
      ↓  validated objects
    JobRow (SQLAlchemy) → SQLite

Why two models? :class:`Job` is the in-memory contract (validated, typed,
serialisable). :class:`JobRow` is the storage shape (flat columns, timestamps).
Converters (:meth:`JobRow.from_job` / :meth:`JobRow.to_job`) bridge them.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ---------------------------------------------------------------------------
# Pydantic validation gate
# ---------------------------------------------------------------------------
class Job(BaseModel):
    """One validated job record.

    Attributes:
        job_id: Stable Naukri numeric id parsed from the job URL
            (``/job-listings-<slug>-<digits>``). Primary key downstream.
        title: Job title (min 4 chars — filters out nav-link junk).
        company / location / search_location / experience / salary / posted:
            Free-text fields; empty string when the card omits them.
        url: Canonical Naukri job URL (query params stripped).
        apply_url: External company-site link when found, else ``url``.
        snippet / description: Short card text / full detail text (capped).
        skills: Skill list (stored comma-joined in SQLite).
    """

    job_id: str = Field(min_length=3)
    title: str = Field(min_length=4)
    company: str = ""
    location: str = ""
    search_location: str = ""
    experience: str = ""
    salary: str = ""
    posted: str = ""
    url: str = ""
    apply_url: str = ""
    snippet: str = ""
    description: str = ""
    skills: list[str] = Field(default_factory=list)

    @field_validator("url", "apply_url")
    @classmethod
    def _strip(cls, v: str) -> str:
        """Canonicalise URLs: trim whitespace, drop tracking query params."""
        return (v or "").strip().split("?")[0]

    @field_validator("title", "company")
    @classmethod
    def _squeeze(cls, v: str) -> str:
        """Collapse inner whitespace/newlines so table output stays tidy."""
        return " ".join((v or "").split())

    def skill_text(self) -> str:
        """Return skills as a single comma-joined string (DB column shape)."""
        return ", ".join(self.skills)


# ---------------------------------------------------------------------------
# SQLAlchemy storage shape
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Declarative base — all ORM tables derive from this (shared metadata)."""


class JobRow(Base):
    """``jobs`` table: one row per unique Naukri job id.

    ``first_seen``/``last_seen`` power the incrementality story: re-scrapes
    upsert on ``job_id`` and bump ``last_seen``, so “new since yesterday” is
    a simple query instead of CSV diffing.
    """

    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    company: Mapped[str] = mapped_column(String(300), default="")
    location: Mapped[str] = mapped_column(String(300), default="")
    search_location: Mapped[str] = mapped_column(String(64), default="")
    experience: Mapped[str] = mapped_column(String(128), default="")
    salary: Mapped[str] = mapped_column(String(256), default="")
    posted: Mapped[str] = mapped_column(String(128), default="")
    url: Mapped[str] = mapped_column(String(1000), default="")
    apply_url: Mapped[str] = mapped_column(String(1000), default="")
    snippet: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    skills: Mapped[str] = mapped_column(Text, default="")  # comma-joined
    first_seen: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    @classmethod
    def from_job(cls, job: Job) -> "JobRow":
        """Build a new ORM row from a validated :class:`Job`."""
        return cls(
            job_id=job.job_id,
            title=job.title,
            company=job.company,
            location=job.location,
            search_location=job.search_location,
            experience=job.experience,
            salary=job.salary,
            posted=job.posted,
            url=job.url,
            apply_url=job.apply_url or job.url,
            snippet=job.snippet,
            description=job.description,
            skills=job.skill_text(),
        )

    def to_job(self) -> Job:
        """Convert a DB row back into a validated :class:`Job`."""
        return Job(
            job_id=self.job_id,
            title=self.title,
            company=self.company,
            location=self.location,
            search_location=self.search_location,
            experience=self.experience,
            salary=self.salary,
            posted=self.posted,
            url=self.url,
            apply_url=self.apply_url,
            snippet=self.snippet,
            description=self.description,
            skills=[s.strip() for s in (self.skills or "").split(",") if s.strip()],
        )


class ScrapeRun(Base):
    """``scrape_runs`` table: audit log of every pipeline execution."""

    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    keywords: Mapped[str] = mapped_column(String(500), default="")
    locations: Mapped[str] = mapped_column(String(500), default="")
    pages: Mapped[int] = mapped_column(default=0)
    found: Mapped[int] = mapped_column(default=0)
    new_jobs: Mapped[int] = mapped_column(default=0)
