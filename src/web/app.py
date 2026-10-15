"""FastAPI control plane: REST + dashboard + Scalar docs + MCP on one port.

* Dashboard UI ......... ``GET /`` (Tailwind v4 + IBM Plex Mono)
* Scalar API tester .... ``GET /scalar`` (via ``scalar-fastapi``)
* REST ................. ``GET/POST /api/...`` (OpenAPI at ``/openapi.json``)
* MCP (Streamable HTTP)  ``/mcp`` (via FastMCP ``http_app`` mount)

Every action endpoint has a cancel twin: ``POST /api/scrape`` and
``POST /api/exports`` start tracked runs (202 + run id);
``POST /api/runs/{run_id}/cancel`` stops them. All failures share one
envelope: ``{"error": {"code": ..., "message": ...}}``.

Sources:
* Scalar FastAPI: https://scalar.com/products/api-references/integrations/fastapi
  (``add_scalar_reference(app)`` registers ``/scalar``).
* FastMCP FastAPI: https://gofastmcp.com/integrations/fastapi
  (``mcp.http_app`` + ``FastAPI(lifespan=...)`` + ``app.mount``).
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

from ..models import Job
from .data import JobNotFound, get_job, get_stats, list_jobs
from .errors import ApiError
from .mcp_tools import build_mcp
from .orchestrator import BusyError, Orchestrator, RunNotCancellable, RunNotFound
from .schemas import ExportRequest, HealthOut, JobsPage, RunOut, ScrapeRequest, StatsOut

#: Dashboard template served at ``GET /`` (single self-contained file).
DASHBOARD_HTML = Path(__file__).parent / "templates" / "dashboard.html"


def _mount_scalar(app: FastAPI) -> bool:
    """Register Scalar API reference at ``/scalar``; False when unavailable."""
    try:
        from scalar_fastapi import add_scalar_reference
    except ImportError:
        return False
    add_scalar_reference(app)
    return True


def create_app(orch: Orchestrator | None = None) -> FastAPI:
    """Build the app (inject an :class:`Orchestrator` in tests)."""
    orch = orch if orch is not None else Orchestrator()
    mcp = build_mcp(orch)
    if mcp is not None:
        mcp_app = mcp.http_app(path="/")
        app = FastAPI(title="Naukri Collector",
                      description="Polite Naukri.com job collector — control plane",
                      version="1.0.0", lifespan=mcp_app.lifespan)
        app.mount("/mcp", mcp_app)
    else:
        app = FastAPI(title="Naukri Collector",
                      description="Polite Naukri.com job collector — control plane",
                      version="1.0.0")

    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse({"error": {"code": exc.code,
                                       "message": exc.message}},
                            status_code=exc.status)

    @app.exception_handler(HTTPException)
    async def _http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse({"error": {"code": exc.status_code,
                                       "message": exc.detail}},
                            status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request,
                                exc: RequestValidationError) -> JSONResponse:
        return JSONResponse({"error": {"code": "VALIDATION_ERROR",
                                       "message": "request validation failed",
                                       "details": jsonable_encoder(exc.errors())}},
                            status_code=422)

    @app.get("/", include_in_schema=False)
    def dashboard() -> FileResponse:
        """Serve the control-plane dashboard (single HTML file)."""
        return FileResponse(DASHBOARD_HTML, media_type="text/html")

    @app.get("/api/health", response_model=HealthOut, operation_id="get_health")
    def health() -> HealthOut:
        """Liveness: process up, DB reachable, run-hub size."""
        from ..db import count_jobs

        return HealthOut(jobs=count_jobs(), runs=len(orch.list_runs()))

    @app.get("/api/stats", response_model=StatsOut, operation_id="get_stats")
    def stats() -> StatsOut:
        """KPIs + chart facets for the dashboard."""
        data = get_stats()
        return StatsOut(**data, active_runs=orch.active_count())

    @app.get("/api/jobs", response_model=JobsPage, operation_id="list_jobs")
    def jobs(q: str = Query(default=""),
             location: str = Query(default=""),
             page: int = Query(default=1, ge=1),
             page_size: int = Query(default=20, ge=1, le=100)) -> JobsPage:
        """Search collected jobs (paginated, freshest first)."""
        rows, total = list_jobs(q=q, location=location,
                                page=page, page_size=page_size)
        return JobsPage(data=rows, page=page, page_size=page_size, total=total)

    @app.get("/api/jobs/{job_id}", response_model=Job, operation_id="get_job")
    def job_detail(job_id: str) -> Job:
        """One job by id (404 ``JOB_NOT_FOUND`` when unknown)."""
        return get_job(job_id)

    @app.post("/api/scrape", status_code=202, response_model=RunOut,
              operation_id="start_scrape")
    def scrape(body: ScrapeRequest) -> RunOut:
        """Start a scrape run (202 + run id; 409 when one already runs)."""
        record = orch.start_scrape(body.model_dump())
        return RunOut.from_record(record)

    @app.post("/api/exports", status_code=202, response_model=RunOut,
              operation_id="start_export")
    def start_export(body: ExportRequest) -> RunOut:
        """Start an export run; fetch the file at its download URL when done."""
        record = orch.start_export(body.model_dump())
        return RunOut.from_record(record)

    @app.get("/api/runs", response_model=list[RunOut], operation_id="list_runs")
    def runs() -> list[RunOut]:
        """All runs, newest first."""
        return [RunOut.from_record(r) for r in orch.list_runs()]

    @app.get("/api/runs/{run_id}", response_model=RunOut,
             operation_id="get_run")
    def run_detail(run_id: str) -> RunOut:
        """Live status + progress + result for one run."""
        return RunOut.from_record(orch.get(run_id))

    @app.post("/api/runs/{run_id}/cancel", response_model=RunOut,
              operation_id="cancel_run")
    def run_cancel(run_id: str) -> RunOut:
        """Cancel twin for every action: stops the run, keeps partials."""
        return RunOut.from_record(orch.cancel(run_id))

    @app.get("/api/runs/{run_id}/download", operation_id="download_export")
    def run_download(run_id: str):  # type: ignore[no-untyped-def]
        """Download a finished export run's file (409 until it succeeds)."""
        record = orch.get(run_id)
        if record.kind != "export":
            raise HTTPException(status_code=409,
                                detail="only export runs have files")
        if record.status != "succeeded":
            raise HTTPException(status_code=409,
                                detail=f"export {record.status}; retry when it succeeds")
        path = Path(record.summary.get("path") or "")
        if not path.is_file():
            raise HTTPException(status_code=404, detail="export file missing")
        return FileResponse(path, filename=path.name)

    _mount_scalar(app)
    return app


#: Module app for ``uvicorn src.web.app:app`` (own orchestrator + MCP mount).
app = create_app()


if __name__ == "__main__":  # `python -m src.web.app` entry point
    import uvicorn

    uvicorn.run(app, host=os.getenv("WEB_HOST", "127.0.0.1"),
                port=int(os.getenv("WEB_PORT", "8000")))
