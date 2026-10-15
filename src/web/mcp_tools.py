"""Curated MCP tools over the orchestrator (purpose-built, not auto-converted).

Per the FastMCP FastAPI guide, auto-converting every REST endpoint gives LLMs
a worse interface than a small curated set — so the MCP surface here is five
focused tools: read stats, search jobs, start a scrape, check a run, cancel
a run. Mounted at ``/mcp`` by :mod:`src.web.app`.

Sources:
* https://gofastmcp.com/integrations/fastapi — ``mcp.http_app(path=...)``,
  ``lifespan`` passthrough, ``app.mount(...)``.
"""
from __future__ import annotations

from .data import get_stats, list_jobs
from .orchestrator import BusyError, Orchestrator, RunNotCancellable, RunNotFound


def build_mcp(orch: Orchestrator):  # type: ignore[no-untyped-def]
    """Build the FastMCP server bound to ``orch``, or None if unavailable.

    Returns None (instead of raising) when ``fastmcp`` is not installed so
    the REST + dashboard layers keep working without the MCP extra.
    """
    try:
        from fastmcp import FastMCP
    except ImportError:
        return None

    mcp = FastMCP("Naukri Collector")

    @mcp.tool
    def collector_stats() -> dict:
        """DB overview: totals plus top locations/companies for charts."""
        return get_stats()

    @mcp.tool
    def search_jobs(query: str = "", location: str = "",
                    page_size: int = 10) -> dict:
        """Search collected jobs (freshest first)."""
        jobs, total = list_jobs(q=query, location=location,
                                page=1, page_size=page_size)
        return {"total": total,
                "jobs": [j.model_dump() for j in jobs]}

    @mcp.tool
    def start_scrape(keywords: str = "",
                     locations: str = "") -> dict:
        """Start a scrape run; returns its run id (409-style error when busy)."""
        try:
            return orch.start_scrape({"keywords": keywords,
                                      "locations": locations}).to_dict()
        except BusyError as e:
            return {"error": str(e)}

    @mcp.tool
    def run_status(run_id: str) -> dict:
        """Live status + progress + result summary for one run."""
        try:
            return orch.get(run_id).to_dict()
        except RunNotFound as e:
            return {"error": str(e)}

    @mcp.tool
    def cancel_run(run_id: str) -> dict:
        """Ask a running scrape/export to stop (keeps partial results)."""
        try:
            return orch.cancel(run_id).to_dict()
        except (RunNotFound, RunNotCancellable) as e:
            return {"error": str(e)}

    return mcp
