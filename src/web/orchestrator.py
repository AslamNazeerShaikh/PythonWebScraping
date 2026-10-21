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

import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

log = logging.getLogger(__name__)

from .errors import ApiError
from .runlog import attached_run_log


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
    #: Stage timeline (append-only, newest 500 kept): every ``push_progress``
    #: lands here with a timestamp — the dashboard renders it as live steps.
    events: deque = field(default_factory=lambda: deque(maxlen=500),
                         repr=False, compare=False)
    _stop_event: threading.Event = field(default_factory=threading.Event,
                                         repr=False, compare=False)

    def should_stop(self) -> bool:
        """True once ``cancel`` was requested (polled between pages)."""
        return self._stop_event.is_set()

    def push_progress(self, update: dict) -> None:
        """Merge a progress update and append it to the stage timeline."""
        self.progress = {**self.progress, **update}
        self.events.append({"t": round(time.time(), 3), **update})
        self.updated_at = time.time()

    def to_dict(self) -> dict:
        """JSON-safe snapshot for REST responses and MCP tool results."""
        return {
            "run_id": self.run_id, "kind": self.kind, "status": self.status,
            "cancel_requested": self.cancel_requested,
            "params": dict(self.params), "progress": dict(self.progress),
            "events": list(self.events)[-50:],
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
    loc = params.get("locations") or params.get("location") or ""
    if loc:
        SETTINGS.locations = [s.strip().lower() for s in str(loc).split(",") if s.strip()]
    for key in ("experience", "date_filter", "max_pages_per_search", "max_jobs_total"):
        alias = {"experience": "experience", "date_filter": "days",
                 "max_pages_per_search": "pages", "max_jobs_total": "max_jobs"}[key]
        if params.get(alias) is not None:
            setattr(SETTINGS, key, params[alias])
    if params.get("enrich") is not None:
        SETTINGS.enrich_details = bool(params["enrich"])
    started = time.time()
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
        duration = round(time.time() - started, 1)
        places = len(SETTINGS.locations)
        if record.should_stop():
            verdict = (f"cancelled after {duration}s — {new} new of {total} "
                       f"kept across {places} location(s) (partials upserted)")
        else:
            verdict = (f"{new} new of {total} collected across {places} "
                       f"location(s) in {duration}s")
        return {"found": total, "new": new, "cancelled": record.should_stop(),
                "duration_s": duration, "verdict": verdict}
    finally:
        for key, value in prev.items():
            setattr(SETTINGS, key, value)


def default_export_runner(record: RunRecord) -> dict:
    """Snapshot export in the worker thread (fast op, still tracked)."""
    from ..export import export_jobs

    dest = export_jobs(fmt=record.params.get("format") or "csv",
                       location=record.params.get("location") or "",
                       exclude_java=record.params.get("exclude_java", True),
                       days=record.params.get("days"),
                       location_match=record.params.get("location_match")
                       or "contains",
                       exclude_unwanted=record.params.get(
                           "exclude_unwanted", True))
    return {"file": dest.name, "path": str(dest)}


def default_collect_runner(record: RunRecord) -> dict:
    """API collection into SQLite (JobSpy-clone): fetch → upsert → audit.

    Falls back to the browser scrape pipeline when the API refuses, so a
    lane collection never comes home empty-handed without trying.
    """
    from ..config import SETTINGS
    from ..db import init_db, record_run, upsert_jobs
    from ..log import setup_logging

    started = time.time()
    try:
        from .nkapi import api_collect_jobs

        setup_logging(SETTINGS.log_level)
        init_db()
        jobs, pages = api_collect_jobs(record.params, record.should_stop,
                                       record.push_progress)
        source = "api"
    except Exception as e:
        log.warning("API collect failed (%s) — browser fallback", e)
        summary = default_scrape_runner(record)
        summary["source"] = "browser"
        return summary
    new, total = upsert_jobs(jobs)
    params = record.params
    record_run(str(params.get("keywords") or ""),
               str(params.get("location") or ""), pages,
               found=total, new_jobs=new)
    duration = round(time.time() - started, 1)
    verdict = (f"{new} new of {total} collected via API in {duration}s")
    return {"found": total, "new": new, "source": source,
            "duration_s": duration, "verdict": verdict,
            "cancelled": record.should_stop()}
def browser_scan_skills(record: RunRecord) -> dict:
    """Browser skills scan (fallback when the API fast path fails).

    Same report shape as :func:`nkapi.api_scan_skills` — the caller cannot
    tell which path produced it except via the ``source`` it stamps after.
    """
    from playwright.sync_api import sync_playwright

    from ..config import SETTINGS
    from ..log import setup_logging
    from ..naukri_scraper import run_skills_scan
    from ..stealth_browser import launch_context

    from .nkapi import company_mode

    params = record.params
    by_company = company_mode(params)
    keywords = str(params.get("keywords") or "").strip()
    location = str(params.get("location") or "pune").strip().lower()
    experience = params.get("experience") or 6
    days = params.get("days") or 7
    pages = params.get("pages") or 5
    max_jobs = params.get("max_jobs") or 100
    setup_logging(SETTINGS.log_level)
    with sync_playwright() as p:
        context = launch_context(p)
        try:
            report = run_skills_scan(context, keywords, location, experience,
                                     days, pages, max_jobs,
                                     by_company=by_company,
                                     should_stop=record.should_stop,
                                     on_progress=record.push_progress)
        finally:
            context.close()
    return report


def default_skills_runner(record: RunRecord) -> dict:
    """Key-skills scan in the worker thread (API fast path, browser fallback).

    Tries the direct search API first (20 postings/request, no browser);
    any failure (rate-limit, rotated key, network) falls back to the
    polite browser scan. Analysis-only either way: scanned postings are
    NOT upserted — the frequency report (and its text file) is the
    artifact. Params carry explicit search fields so ``SETTINGS`` is
    never mutated here.
    """
    from ..config import SETTINGS

    try:
        from .nkapi import api_scan_skills, company_mode

        report = api_scan_skills(record.params, record.should_stop,
                                 record.push_progress)
        source = "api"
    except Exception as e:
        log.warning("API fast-path failed (%s) — browser fallback", e)
        report = browser_scan_skills(record)
        source = "browser"
    started = record.created_at
    duration = round(time.time() - started, 1)
    top = report["top"]
    if top:
        names = ", ".join(t["skill"] for t in top[:3])
        verdict = (f"{report['unique_skills']} unique skills across "
                   f"{report['jobs_scanned']} postings in {duration}s — "
                   f"top: {names}")
    else:
        verdict = f"no postings found in {duration}s"
    out = SETTINGS.output_dir
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"skills_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    dest.write_text(render_skills_text(report, record.params), encoding="utf-8")
    mode = "companies" if company_mode(record.params) else "postings"
    return {**report, "file": dest.name, "path": str(dest),
            "duration_s": duration, "verdict": verdict, "source": source,
            "count_mode": mode, "cancelled": record.should_stop()}


_MODE_LABEL = {"companies": "distinct companies", "postings": "per posting"}


def render_skills_text(report: dict, params: dict) -> str:
    """Render the frequency report as a plain-text file (the .txt export)."""
    mode = _MODE_LABEL.get(report.get("count_mode") or "companies", "distinct companies")
    lines = [f"Key skills across {report['jobs_scanned']} postings "
             f"(counting: {mode}; "
             f"{params.get('keywords') or ''} | {params.get('location') or ''} | "
             f"exp {params.get('experience') or ''}y | last {params.get('days') or ''}d)",
             ""]
    for t in report["top"]:
        lines.append(f"{t['count']:4d}x ({t['pct']:5.1f}%)  {t['skill']}")
        lines.append("           @ " + ", ".join(
            f"{c['name']} x{c['count']}" for c in t["companies"]))
    lines += ["", f"Unique skills: {report['unique_skills']} | "
                  f"postings with skills: {report['with_skills']} | "
                  f"without skills (detail unreadable or skill-less): "
                  f"{report['without_skills']}"]
    return "\n".join(lines) + "\n"


class Orchestrator:
    """Spawns, tracks, and cancels background runs (thread-safe)."""

    def __init__(self, scrape_runner: RunnerFunc | None = None,
                 export_runner: RunnerFunc | None = None,
                 skills_runner: RunnerFunc | None = None,
                 collect_runner: RunnerFunc | None = None,
                 max_runs: int = 200) -> None:
        self._scrape_runner = scrape_runner or default_scrape_runner
        self._export_runner = export_runner or default_export_runner
        self._skills_runner = skills_runner or default_skills_runner
        self._collect_runner = collect_runner or default_collect_runner
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

    def start_skills(self, params: dict | None = None) -> RunRecord:
        """Start a key-skills scan (shares the single browser lock)."""
        if not self._scrape_lock.acquire(blocking=False):
            raise BusyError("a browser run is already in progress")
        record = self._new_record("skills", params or {})
        self._launch(record, self._skills_runner, release_lock=True)
        return record

    def start_collect(self, params: dict | None = None) -> RunRecord:
        """Start an API lane collection into SQLite (lock-guarded)."""
        if not self._scrape_lock.acquire(blocking=False):
            raise BusyError("a browser run is already in progress")
        record = self._new_record("collect", params or {})
        self._launch(record, self._collect_runner, release_lock=True)
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
            with attached_run_log(record.kind, record.run_id) as log_name:
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
            record.summary["log"] = log_name

        thread = threading.Thread(target=_target, daemon=True,
                                  name=f"run-{record.run_id}")
        self._threads[record.run_id] = thread
        thread.start()
