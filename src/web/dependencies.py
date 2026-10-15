"""Shared dependencies — one place for cross-router needs.

Per the FastAPI bigger-applications guide, dependencies used in several
routers live in their own ``dependencies`` module and routers pull them in
with ``Depends`` (relative import ``..`` = up to this package).
"""
from __future__ import annotations

from fastapi import Request

from .orchestrator import Orchestrator


def get_orchestrator(request: Request) -> Orchestrator:
    """Resolve the process-wide :class:`Orchestrator` from app state.

    Tests and the LLM harness swap it via ``app.dependency_overrides`` —
    the documented FastAPI testing pattern — without touching routers.
    """
    return request.app.state.orchestrator
