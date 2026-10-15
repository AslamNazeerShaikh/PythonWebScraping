"""Web control plane: FastAPI app + run orchestrator + MCP tools + dashboard.

The Python backend is the brain — it orchestrates every operation, owns the
data (SQLite), and serves visualization plus import/export. The browser
(Playwright) is only the hands: it opens pages when a scrape run tells it to.

Start it with ``python -m src.main web`` (or ``uvicorn src.web.app:app``),
then drive everything from the dashboard (``/``), Scalar API UI
(``/scalar``), plain REST (``/api/...``), or MCP tools (``/mcp``).
"""
