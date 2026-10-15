"""Ops router — liveness, stats, DB explorer, and run-log viewer.

Mirrors the guide's ``internal/admin`` pattern: this module sets no prefix
or tags itself, so :mod:`src.web.main` applies them at ``include_router``
time (``prefix="/api", tags=["ops"]``) without touching this file. These are
operational endpoints (process/DB/logs), not the product API.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from ...db import count_jobs
from ..crud import get_stats, list_tables, table_rows
from ..dependencies import get_orchestrator
from ..orchestrator import Orchestrator
from ..runlog import list_log_files, read_log_file
from ..schemas import DbTable, DbTablePage, HealthOut, LogFile, StatsOut

router = APIRouter()


@router.get("/health", response_model=HealthOut, operation_id="get_health")
def health(orch: Orchestrator = Depends(get_orchestrator)) -> HealthOut:
    """Liveness: process up, DB reachable, run-hub size."""
    return HealthOut(jobs=count_jobs(), runs=len(orch.list_runs()))


@router.get("/stats", response_model=StatsOut, operation_id="get_stats")
def stats(orch: Orchestrator = Depends(get_orchestrator)) -> StatsOut:
    """KPIs + chart facets for the dashboard."""
    return StatsOut(**get_stats(), active_runs=orch.active_count())


@router.get("/db/tables", response_model=list[DbTable],
            operation_id="list_db_tables")
def db_tables() -> list[DbTable]:
    """Every table in the serverless SQLite store (explorer overview)."""
    return [DbTable(**t) for t in list_tables()]


@router.get("/db/tables/{name}", response_model=DbTablePage,
            operation_id="get_db_table")
def db_table(name: str,
             page: int = Query(default=1, ge=1),
             page_size: int = Query(default=20, ge=1, le=200)) -> DbTablePage:
    """Paginated rows of one table (404 ``TABLE_NOT_FOUND`` when unknown)."""
    columns, rows, total = table_rows(name, page=page, page_size=page_size)
    return DbTablePage(name=name, columns=columns, data=rows,
                       page=page, page_size=page_size, total=total)


@router.get("/logs", response_model=list[LogFile], operation_id="list_logs")
def logs() -> list[LogFile]:
    """Per-run log files, newest first."""
    return [LogFile(**f) for f in list_log_files()]


@router.get("/logs/{name}", response_class=PlainTextResponse,
            operation_id="get_log")
def log_tail(name: str,
             max_lines: int = Query(default=500, ge=1, le=5000)) -> PlainTextResponse:
    """Tail of one run log (timestamps for every Python + browser line)."""
    return PlainTextResponse(read_log_file(name, max_lines=max_lines))
