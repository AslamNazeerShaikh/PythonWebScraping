"""Main entry — ties routers together (FastAPI bigger-applications shape).

Structure per https://fastapi.tiangolo.com/tutorial/bigger-applications/::

    src/web/
        main.py          ← this file: FastAPI app + include_router + mounts
        dependencies.py  ← shared Depends (orchestrator from app state)
        routers/jobs.py  ← APIRouter(prefix="/api/jobs", tags=["jobs"])
        routers/runs.py  ← APIRouter(prefix="/api", tags=["runs"])
        internal/ops.py  ← prefix/tags applied at include time (admin pattern)

Run with ``uvicorn src.web.main:app`` (or ``python -m src.main web``).
Entry point is also declared in ``pyproject.toml`` (``[tool.fastapi]``).

Sources:
* Scalar FastAPI: https://scalar.com/products/api-references/integrations/fastapi
* FastMCP FastAPI: https://gofastmcp.com/integrations/fastapi
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

from .errors import ApiError
from .internal import ops
from .mcp_tools import build_mcp
from .orchestrator import Orchestrator
from .routers import jobs, runs

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
    """Build the app (pass an :class:`Orchestrator`, else one is made).

    Routers resolve the orchestrator through the ``get_orchestrator``
    dependency reading ``app.state`` — override it in tests/harness via
    ``app.dependency_overrides`` without touching router code.
    """
    state_orch = orch if orch is not None else Orchestrator()
    mcp = build_mcp(state_orch)
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
    app.state.orchestrator = state_orch

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

    app.include_router(jobs.router)
    app.include_router(runs.router)
    app.include_router(ops.router, prefix="/api", tags=["ops"])

    @app.get("/", include_in_schema=False)
    def dashboard() -> FileResponse:
        """Serve the control-plane dashboard (single HTML file, never cached)."""
        return FileResponse(DASHBOARD_HTML, media_type="text/html",
                            headers={"Cache-Control": "no-store"})

    _mount_scalar(app)
    return app


#: Module app for ``uvicorn src.web.main:app`` (own orchestrator + MCP mount).
app = create_app()


if __name__ == "__main__":  # `python -m src.web.main` entry point
    import uvicorn

    uvicorn.run(app, host=os.getenv("WEB_HOST", "127.0.0.1"),
                port=int(os.getenv("WEB_PORT", "8000")))
