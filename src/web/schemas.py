"""REST contracts — typed input/output for every endpoint (contract-first).

Request bodies keep every field optional: an omitted field means "keep the
configured default from ``SETTINGS``", so ``POST /api/scrape {}`` reproduces
the CLI run exactly. Responses reuse :class:`src.models.Job` directly.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ..models import Job


class ScrapeRequest(BaseModel):
    """Start-scrape parameters; ``None``/empty resolves to SETTINGS defaults."""

    keywords: str = ""
    locations: str = ""  # comma-separated, e.g. "pune,hyderabad"
    experience: int | None = Field(default=None, gt=0)
    days: int | None = Field(default=None, gt=0)
    pages: int | None = Field(default=None, gt=0)
    max_jobs: int | None = Field(default=None, gt=0)
    enrich: bool | None = None


class ExportRequest(BaseModel):
    """Start-export parameters (runs as a tracked, cancellable run)."""

    format: str = Field(default="csv", pattern="^(csv|excel)$")
    location: str = ""


class SkillsRequest(BaseModel):
    """Start a key-skills scan over the freshest matching postings."""

    keywords: str = Field(min_length=1)  # comma-separated titles, e.g. "asp.net core, web api"
    location: str = "pune"
    experience: int | None = Field(default=6, gt=0)
    days: int | None = Field(default=7, gt=0)
    pages: int | None = Field(default=5, gt=0, le=10)
    max_jobs: int | None = Field(default=100, gt=0, le=200)


class SkillTop(BaseModel):
    """One ranked skill: posting count + share of scanned postings."""

    skill: str
    count: int
    pct: float


class RunOut(BaseModel):
    """One background run: scrape or export, with live progress + result."""

    run_id: str
    kind: str
    status: str  # running | cancelling | cancelled | succeeded | failed
    cancel_requested: bool
    params: dict = Field(default_factory=dict)
    progress: dict = Field(default_factory=dict)
    #: Stage timeline (newest 50) — the dashboard renders these as live steps.
    events: list = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)
    error: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0

    @classmethod
    def from_record(cls, record: object) -> "RunOut":
        """Build from an orchestrator :class:`RunRecord` (duck-typed)."""
        get = getattr
        return cls(
            run_id=get(record, "run_id"), kind=get(record, "kind"),
            status=get(record, "status"),
            cancel_requested=get(record, "cancel_requested"),
            params=dict(get(record, "params") or {}),
            progress=dict(get(record, "progress") or {}),
            events=list(get(record, "events") or []),
            summary=dict(get(record, "summary") or {}),
            error=get(record, "error") or "",
            created_at=get(record, "created_at") or 0.0,
            updated_at=get(record, "updated_at") or 0.0,
        )


class TopItem(BaseModel):
    """One ranked facet row for the dashboard charts."""

    name: str
    count: int


class StatsOut(BaseModel):
    """DB overview powering the dashboard KPIs + charts."""

    total_jobs: int
    new_last_24h: int
    by_location: list[TopItem] = Field(default_factory=list)
    by_company: list[TopItem] = Field(default_factory=list)
    active_runs: int = 0


class JobsPage(BaseModel):
    """Paginated job list (every list endpoint paginates — no exceptions)."""

    data: list[Job] = Field(default_factory=list)
    page: int = 1
    page_size: int = 20
    total: int = 0


class HealthOut(BaseModel):
    """Liveness probe: process up + DB reachable + run-hub size."""

    status: str = "ok"
    jobs: int = 0
    runs: int = 0


class DbTable(BaseModel):
    """One database table in the explorer (name/columns/row count)."""

    name: str
    columns: list[str] = Field(default_factory=list)
    rows: int = 0


class DbTablePage(BaseModel):
    """Paginated rows of one table (JSON-safe values)."""

    name: str
    columns: list[str] = Field(default_factory=list)
    data: list[dict] = Field(default_factory=list)
    page: int = 1
    page_size: int = 20
    total: int = 0


class LogFile(BaseModel):
    """One per-run log file on disk."""

    name: str
    size: int = 0
    modified: float = 0.0
