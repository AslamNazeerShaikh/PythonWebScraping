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

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
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


# ---------------------------------------------------------------------------
# LinkedIn email collector (see docs/SPEC-linkedin-email-collector.md)
# ---------------------------------------------------------------------------
#: Email format gate — JobSpy's regex pattern, doubled-TLD tolerant.
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

#: Snippet cap — evidence window around the email, not the whole post.
SNIPPET_CAP = 300


class EmailContact(BaseModel):
    """One validated email harvested from a LinkedIn post body.

    Attributes:
        email: Lowercased, format-validated address (primary key downstream).
        domain: Target domain whose search surfaced the post (e.g.
            ``"cognizant.com"`` for keyword ``"@cognizant.com"``). Empty
            only if caller omits it.
        post_url / author / posted: Best-effort post evidence — LinkedIn's
            content search renders no permalink anchor, so ``post_url`` may
            stay empty while the email still stands.
        snippet: ~200-char window around the email (whitespace-squeezed,
            capped at :data:`SNIPPET_CAP`).
        keyword: Search keyword that found the post.
        first_seen / last_seen: Set by the DB layer on insert/re-sighting.
    """

    email: str
    post_id: str = ""
    domain: str = ""
    post_url: str = ""
    author: str = ""
    posted: str = ""
    snippet: str = ""
    keyword: str = ""
    first_seen: datetime | None = None
    last_seen: datetime | None = None

    @field_validator("email")
    @classmethod
    def _valid_email(cls, v: str) -> str:
        """Trim + lowercase the address; reject anything unmailable."""
        v = (v or "").strip().lower()
        if not EMAIL_RE.fullmatch(v):
            raise ValueError(f"invalid email address: {v!r}")
        return v

    @field_validator("post_url")
    @classmethod
    def _strip_url(cls, v: str) -> str:
        """Trim whitespace; keep the URL as-is (LinkedIn adds params itself)."""
        return (v or "").strip()

    @field_validator("snippet", "author", "posted", "keyword", "domain", "post_id")
    @classmethod
    def _squeeze(cls, v: str) -> str:
        """Collapse whitespace; cap snippet so Excel rows stay readable."""
        v = " ".join((v or "").split())
        return v[:SNIPPET_CAP]


class EmailRow(Base):
    """``contact_emails`` table: one row per harvested (email, post) sighting.

    ``email`` alone is no longer the primary key — the same address may be
    re-posted by recruiters across several posts (hiring still ongoing), and
    each distinct post is a distinct row. Dedupe happens on
    ``(email, post_id)``: a re-sighting of the *same* post bumps
    ``last_seen`` and backfills empty evidence instead of duplicating.
    """

    __tablename__ = "contact_emails"
    __table_args__ = (UniqueConstraint("email", "post_id", name="uq_email_post"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    post_id: Mapped[str] = mapped_column(String(500), default="")
    domain: Mapped[str] = mapped_column(String(255), default="")
    post_url: Mapped[str] = mapped_column(String(1000), default="")
    author: Mapped[str] = mapped_column(String(300), default="")
    posted: Mapped[str] = mapped_column(String(128), default="")
    snippet: Mapped[str] = mapped_column(Text, default="")
    keyword: Mapped[str] = mapped_column(String(255), default="")
    first_seen: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    @classmethod
    def from_contact(cls, contact: EmailContact) -> "EmailRow":
        """Build a new ORM row from a validated :class:`EmailContact`."""
        return cls(
            email=contact.email,
            post_id=contact.post_id,
            domain=contact.domain,
            post_url=contact.post_url,
            author=contact.author,
            posted=contact.posted,
            snippet=contact.snippet,
            keyword=contact.keyword,
        )

    def to_contact(self) -> EmailContact:
        """Convert a DB row back into a validated :class:`EmailContact`."""
        return EmailContact(
            email=self.email,
            post_id=self.post_id,
            domain=self.domain,
            post_url=self.post_url,
            author=self.author,
            posted=self.posted,
            snippet=self.snippet,
            keyword=self.keyword,
            first_seen=self.first_seen,
            last_seen=self.last_seen,
        )

