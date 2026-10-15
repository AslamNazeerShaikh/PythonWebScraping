"""Shared API error type — one shape for every failure.

All errors surface as ``{"error": {"code": ..., "message": ...}}`` (see the
``ApiError`` handler in :mod:`src.web.app`), per the consistent-error rule in
the api-and-interface-design skill.
"""
from __future__ import annotations


class ApiError(Exception):
    """Base domain error: carries an HTTP status + machine-readable code."""

    status: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.code)
        self.message = message or self.code
