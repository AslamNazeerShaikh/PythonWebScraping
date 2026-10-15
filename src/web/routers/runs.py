"""Runs router — start actions, watch progress, cancel, download results.

Every action endpoint has a cancel twin: ``POST /scrape`` and
``POST /exports`` start tracked runs (202 + run id);
``POST /runs/{run_id}/cancel`` stops them. The orchestrator arrives via the
shared ``get_orchestrator`` dependency (``..`` = up to this package, per the
guide's relative-import rule).
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..dependencies import get_orchestrator
from ..orchestrator import Orchestrator
from ..schemas import ExportRequest, RunOut, ScrapeRequest, SkillsRequest

router = APIRouter(prefix="/api", tags=["runs"])


@router.post("/scrape", status_code=202, response_model=RunOut,
             operation_id="start_scrape")
def start_scrape(body: ScrapeRequest,
                 orch: Orchestrator = Depends(get_orchestrator)) -> RunOut:
    """Start a scrape run (202 + run id; 409 when one already runs)."""
    record = orch.start_scrape(body.model_dump())
    return RunOut.from_record(record)


@router.post("/exports", status_code=202, response_model=RunOut,
             operation_id="start_export")
def start_export(body: ExportRequest,
                 orch: Orchestrator = Depends(get_orchestrator)) -> RunOut:
    """Start an export run; fetch the file at its download URL when done."""
    record = orch.start_export(body.model_dump())
    return RunOut.from_record(record)


@router.post("/skills", status_code=202, response_model=RunOut,
             operation_id="start_skills_scan")
def start_skills(body: SkillsRequest,
                 orch: Orchestrator = Depends(get_orchestrator)) -> RunOut:
    """Scan key skills across fresh postings (202 + run id; 409 when busy)."""
    record = orch.start_skills(body.model_dump())
    return RunOut.from_record(record)


@router.get("/runs", response_model=list[RunOut], operation_id="list_runs")
def list_all(orch: Orchestrator = Depends(get_orchestrator)) -> list[RunOut]:
    """All runs, newest first."""
    return [RunOut.from_record(r) for r in orch.list_runs()]


@router.get("/runs/{run_id}", response_model=RunOut, operation_id="get_run")
def get_one(run_id: str,
            orch: Orchestrator = Depends(get_orchestrator)) -> RunOut:
    """Live status + progress + stage timeline + result for one run."""
    return RunOut.from_record(orch.get(run_id))


@router.post("/runs/{run_id}/cancel", response_model=RunOut,
             operation_id="cancel_run")
def cancel(run_id: str,
           orch: Orchestrator = Depends(get_orchestrator)) -> RunOut:
    """Cancel twin for every action: stops the run, keeps partials."""
    return RunOut.from_record(orch.cancel(run_id))


@router.get("/runs/{run_id}/download", operation_id="download_export")
def download(run_id: str,
             orch: Orchestrator = Depends(get_orchestrator)):  # type: ignore[no-untyped-def]
    """Download a finished export/skills run's file (409 until it succeeds)."""
    record = orch.get(run_id)
    if record.kind not in ("export", "skills"):
        raise HTTPException(status_code=409,
                            detail="only export/skills runs have files")
    if record.status != "succeeded":
        raise HTTPException(status_code=409,
                            detail=f"export {record.status}; retry when it succeeds")
    path = Path(record.summary.get("path") or "")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="export file missing")
    return FileResponse(path, filename=path.name)
