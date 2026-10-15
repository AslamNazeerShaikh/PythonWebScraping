"""Jobs router — read-only access to collected jobs.

``APIRouter`` with ``prefix`` + ``tags`` per the FastAPI bigger-applications
guide; pure CRUD reads, so no dependencies needed. Included by
:mod:`src.web.main` (import the submodule, not ``router``, to avoid name
collisions across routers).
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from ...models import Job
from ..crud import get_job, list_jobs
from ..schemas import JobsPage

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=JobsPage, operation_id="list_jobs")
def list_all(q: str = Query(default=""),
             location: str = Query(default=""),
             page: int = Query(default=1, ge=1),
             page_size: int = Query(default=20, ge=1, le=100)) -> JobsPage:
    """Search collected jobs (paginated, freshest first)."""
    rows, total = list_jobs(q=q, location=location,
                            page=page, page_size=page_size)
    return JobsPage(data=rows, page=page, page_size=page_size, total=total)


@router.get("/{job_id}", response_model=Job, operation_id="get_job")
def get_one(job_id: str) -> Job:
    """One job by id (404 ``JOB_NOT_FOUND`` when unknown)."""
    return get_job(job_id)
