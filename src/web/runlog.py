"""Per-run log files — Python and Playwright loggers, timestamped.

Each background run gets its own ``logs/<kind>_<run-id>_<ts>.log`` file so a
run's full story (orchestrator decisions + browser navigation) is reviewable
after the fact — in the dashboard's log viewer or straight from disk.

Line shape: ``2026-10-15 19:02:11 INFO     src.web.orchestrator: message``.
Console logging is untouched; this only *adds* a file sink per run.
"""
from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .errors import ApiError


class LogNotFound(ApiError):
    """Unknown (or unsafe) log file name."""

    status = 404
    code = "LOG_NOT_FOUND"


#: Line format shared by console and files (files add full date via datefmt).
LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"

#: File timestamps: ``2026-10-15 19:02:11`` (console keeps ``HH:MM:SS``).
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"

#: Allowed log file names (no paths, no traversal — the viewer serves these).
_SAFE_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.\-]*$")


def log_dir() -> Path:
    """Return the log directory, creating it on first use."""
    from ..config import SETTINGS

    path = Path(SETTINGS.log_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_log_path(kind: str, run_id: str) -> Path:
    """File for one run: ``logs/<kind>_<run-id>_YYYYMMDD_HHMMSS.log``."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return log_dir() / f"{kind}_{run_id}_{stamp}.log"


@contextmanager
def attached_run_log(kind: str, run_id: str) -> Iterator[str]:
    """Attach a per-run file sink to the Python + Playwright loggers.

    Yields the file name. On exit the handler is removed and the Playwright
    level restored, so concurrent runs never leak handlers into each other.
    """
    path = run_log_path(kind, run_id)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATEFMT))
    root = logging.getLogger()
    playwright = logging.getLogger("playwright")
    prev_level = playwright.level
    root.addHandler(handler)
    playwright.setLevel(logging.INFO)
    try:
        yield path.name
    finally:
        root.removeHandler(handler)
        handler.close()
        playwright.setLevel(prev_level)


def list_log_files() -> list[dict]:
    """Log files, newest first (name/size/modified epoch)."""
    files = [p for p in log_dir().glob("*.log") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [{"name": p.name, "size": p.stat().st_size,
             "modified": p.stat().st_mtime} for p in files]


def read_log_file(name: str, max_lines: int = 500) -> str:
    """Tail of one log file; rejects traversal/missing names loudly."""
    if not _SAFE_NAME.fullmatch(name or ""):
        raise LogNotFound(f"unsafe log name {name!r}")
    path = log_dir() / name
    if not path.is_file():
        raise LogNotFound(f"no log file {name!r}")
    return "\n".join(path.read_text(encoding="utf-8").splitlines()[-max_lines:])
