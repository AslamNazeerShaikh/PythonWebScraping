"""Operation orchestrator — the brain. Browsers are only the hands.

Every long action (scrape, export) runs as a tracked background run:

* ``POST /api/scrape`` / ``POST /api/exports`` starts a run and returns its
  id immediately (HTTP 202) — the server never blocks the caller.
* ``GET /api/runs/{id}`` reports live progress (stage/page/found counts).
* ``POST /api/runs/{run_id}/cancel`` asks the worker to stop; the run keeps
  whatever it already collected and lands on ``cancelled``.

Scrape runs hold a process-wide lock (one polite browser pass at a time — a
second start gets HTTP 409). Cancellation is cooperative: the worker thread
polls ``record.should_stop()`` between pages/details and the scraper's
``should_stop`` hook ends the pass early with partial results upserted.
"""
from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from .errors import ApiError


class RunNotFound(ApiError):
    """Unknown run id."""

    status = 404
    code = "RUN_NOT_FOUND"


class RunNotCancellable(ApiError):
    """Cancel hit a run that already finished."""

    status = 409
    code = "RUN_NOT_CANCELLABLE"


class BusyError(ApiError):
    """A scrape is already running (one polite pass at a time)."""

    status = 409
    code = "SCRAPE_ALREADY_RUNNING"


#: A runner executes one run synchronously in a worker thread and returns a
#: JSON-safe summary dict. It reads cancellation via ``record.should_stop()``
#: and reports progress via ``record.push_progress({...})``.
RunnerFunc = Callable[["RunRecord"], dict]


@dataclass
class RunRecord:
    """Mutable state for one background run (owned by the orchestrator)."""

    run_id: str
    kind: str  # "scrape" | "export"
    seq: int = 0
    status: str = "running"  # running|cancelling|cancelled|succeeded|failed
    cancel_requested: bool = False
    params: dict = field(default_factory=dict)
    progress: dict = field(default_factory=dict)
    summary: dict = field(default_factory=dict)
    error: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    _stop_event: threading.Event = field(default_factory=threading.Event,
                                         repr=False, compare=False)

    def should_stop(self) -> bool:
        """True once ``cancel`` was requested (polled between pages)."""
        return self._stop_event.is_set()

    def push_progress(self, update: dict) -> None:
        """Merge a progress update (stage/page/found) into the record."""
        self.progress = {**self.progress, **update}
        self.updated_at = time.time()

    def to_dict(self) -> dict:
        """JSON-safe snapshot for REST responses and MCP tool results."""
        return {
            "run_id": self.run_id, "kind": self.kind, "status": self.status,
            "cancel_requested": self.cancel_requested,
            "params": dict(self.params), "progress": dict(self.progress),
            "summary": dict(self.summary), "error": self.error,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }


def default_scrape_runner(record: RunRecord) -> dict:
    """Full collection pipeline in the worker thread (browser + DB + files).

    Imports stay inside the function so importing this module never touches
    Playwright. ``SETTINGS`` overrides from ``record.params`` are restored in
    ``finally`` so concurrent API reads always see the configured defaults.
    Partial results are upserted even when cancelled mid-pass.
    """
    from ..config import SETTINGS
    from ..db import init_db, record_run, upsert_jobs
    from ..log import setup_logging
    from ..naukri_scraper import run_scrape, save_results
    from ..stealth_browser import launch_context

    prev = {"keywords": SETTINGS.keywords, "locations": list(SETTINGS.locations),
            "experience": SETTINGS.experience, "date_filter": SETTINGS.date_filter,
            "max_pages_per_search": SETTINGS.max_pages_per_search,
            "max_jobs_total": SETTINGS.max_jobs_total,
            "enrich_details": SETTINGS.enrich_details}
    params = record.params
    if params.get("keywords"):
        SETTINGS.keywords = str(params["keywords"])
    if params.get("locations"):
        SETTINGS.locations = [s.strip().lower() for s in str(params["locations"]).split(",") if s.strip()]
    for key in ("experience", "date_filter", "max_pages_per_search", "max_jobs_total"):
        alias = {"experience": "experience", "date_filter": "days",
                 "max_pages_per_search": "pages", "max_jobs_total": "max_jobs"}[key]
        if params.get(alias) is not None:
            setattr(SETTINGS, key, params[alias])
    if params.get("enrich") is not None:
        SETTINGS.enrich_details = bool(params["enrich"])
    try:
        from playwright.sync_api import sync_playwright

        setup_logging(SETTINGS.log_level)
        init_db()
        with sync_playwright() as p:
            context = launch_context(p)
            try:
                jobs = run_scrape(context, should_stop=record.should_stop,
                                  on_progress=record.push_progress)
            finally:
                context.close()
        new, total = upsert_jobs(jobs)
        record_run(SETTINGS.keywords, ",".join(SETTINGS.locations),
                   SETTINGS.max_pages_per_search, found=total, new_jobs=new)
        save_results(jobs)
        return {"found": total, "new": new,
                "cancelled": record.should_stop()}
    finally:
        for key, value in prev.items():
            setattr(SETTINGS, key, value)


def default_export_runner(record: RunRecord) -> dict:
    """Snapshot export in the worker thread (fast op, still tracked)."""
    from ..export import export_jobs

    dest = export_jobs(fmt=record.params.get("format") or "csv",
                       location=record.params.get("location") or "")
    return {"file": dest.name, "path": str(dest)}


class Orchestrator:
    """Spawns, tracks, and cancels background runs (thread-safe)."""

    def __init__(self, scrape_runner: RunnerFunc | None = None,
                 export_runner: RunnerFunc | None = None,
                 max_runs: int = 200) -> None:
        self._scrape_runner = scrape_runner or default_scrape_runner
        self._export_runner = export_runner or default_export_runner
        self._max_runs = max_runs
        self._runs: dict[str, RunRecord] = {}
        self._threads: dict[str, threading.Thread] = {}
        self._scrape_lock = threading.Lock()
        self._mutex = threading.Lock()
        self._seq = 0

    # -- starting ---------------------------------------------------------
    def start_scrape(self, params: dict | None = None) -> RunRecord:
        """Start a scrape run; 409-style :class:`BusyError` if one runs."""
        if not self._scrape_lock.acquire(blocking=False):
            raise BusyError("a scrape run is already in progress")
        record = self._new_record("scrape", params or {})
        self._launch(record, self._scrape_runner, release_lock=True)
        return record

    def start_export(self, params: dict | None = None) -> RunRecord:
        """Start an export run (exports never contend with each other)."""
        record = self._new_record("export", params or {})
        self._launch(record, self._export_runner, release_lock=False)
        return record

    # -- observing --------------------------------------------------------
    def get(self, run_id: str) -> RunRecord:
        """Return one run or raise :class:`RunNotFound`."""
        try:
            return self._runs[run_id]
        except KeyError:
            raise RunNotFound(f"no run with id {run_id!r}") from None

    def list_runs(self) -> list[RunRecord]:
        """All runs, newest first."""
        return sorted(self._runs.values(), key=lambda r: r.seq, reverse=True)

    def active_count(self) -> int:
        """Runs currently in flight (running or cancelling)."""
        return sum(1 for r in self._runs.values() if r.status == "running" or r.status == "cancelling")

    # -- cancelling -------------------------------------------------------
    def cancel(self, run_id: str) -> RunRecord:
        """Request cancellation; the worker lands the run on ``cancelled``.

        Raises :class:`RunNotCancellable` when the run already finished —
        cancelling a finished run is a client bug, surfaced loudly (409).
        """
        record = self.get(run_id)
        if record.status in ("cancelled", "succeeded", "failed"):
            raise RunNotCancellable(f"run {run_id!r} already {record.status}")
        record.cancel_requested = True
        record.status = "cancelling"
        record._stop_event.set()
        return record

    # -- test/driver helpers ----------------------------------------------
    def wait_for(self, run_id: str, timeout: float = 30.0) -> RunRecord:
        """Join the worker thread, then return the final record."""
        thread = self._threads.get(run_id)
        if thread is None:
            raise RunNotFound(f"no run with id {run_id!r}") from None
        thread.join(timeout)
        return self.get(run_id)

    def wait_all(self, timeout: float = 30.0) -> None:
        """Join every worker thread (used by tests)."""
        for thread in list(self._threads.values()):
            thread.join(timeout)

    # -- internals --------------------------------------------------------
    def _new_record(self, kind: str, params: dict) -> RunRecord:
        with self._mutex:
            self._seq += 1
            record = RunRecord(run_id=f"{kind}-{self._seq:04d}",
                               kind=kind, seq=self._seq, params=dict(params))
            self._runs[record.run_id] = record
        while len(self._runs) > self._max_runs:
            oldest = min(self._runs, key=lambda r: self._runs[r].seq)
            self._runs.pop(oldest, None)
            self._threads.pop(oldest, None)
        return record

    def _launch(self, record: RunRecord, func: RunnerFunc,
                release_lock: bool) -> None:
        def _target() -> None:
            try:
                record.summary = func(record)
            except Exception as e:  # worker must never die silently
                record.error = f"{type(e).__name__}: {e}"
                record.status = "failed"
            else:
                if record.cancel_requested:
                    record.status = "cancelled"
                else:
                    record.status = "succeeded"
            finally:
                record.updated_at = time.time()
                if release_lock:
                    self._scrape_lock.release()

        thread = threading.Thread(target=_target, daemon=True,
                                  name=f"run-{record.run_id}")
        self._threads[record.run_id] = thread
        thread.start()
