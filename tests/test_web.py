"""Tests for src.web — orchestrator, REST, dashboard, Scalar, MCP tools.

Strategy mirrors the repo's fake-based approach: instant/blocking runner
doubles instead of a real browser, ``fresh_db`` for SQLite, ``TestClient``
for HTTP, and FastMCP's in-memory ``Client`` for tools. No network, no
browser — yet every line and branch of the new code is executed.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

import src.main as main
import src.naukri_scraper as ns
from src.web.dependencies import get_orchestrator
from src.web.main import create_app
from src.web.crud import get_job, get_stats, list_jobs, list_tables, table_rows
from src.web.errors import ApiError, TableNotFound
from src.web.mcp_tools import build_mcp
from src.web.orchestrator import (
    BusyError,
    Orchestrator,
    RunNotCancellable,
    RunNotFound,
    RunRecord,
    default_export_runner,
    default_scrape_runner,
)
from tests.conftest import FakeContext, FakePage, make_job, raw_card


@pytest.fixture(autouse=True)
def _isolated_logs(tmp_path, monkeypatch):
    """Per-run log files land in a tmp dir (never the real logs/)."""
    from src.config import SETTINGS

    monkeypatch.setattr(SETTINGS, "log_dir", tmp_path / "logs")


# ---------------------------------------------------------------------------
# Runner doubles (stand-ins for the browser pipeline)
# ---------------------------------------------------------------------------
def _instant(summary=None):
    """Runner that finishes immediately with a canned summary."""
    def _run(record):
        record.push_progress({"stage": "done"})
        return dict(summary or {"found": 1, "new": 1})
    return _run


def _blocking(summary=None):
    """Runner that works until cancelled (deterministic cancel tests)."""
    def _run(record):
        while not record.should_stop():
            time.sleep(0.01)
        return dict(summary or {"found": 0, "new": 0})
    return _run


def _failing():
    def _run(record):
        raise RuntimeError("boom")
    return _run


# ---------------------------------------------------------------------------
# data.py — filtering, pagination, aggregates
# ---------------------------------------------------------------------------
def test_list_jobs_filters_and_paginates(fresh_db):
    from src.db import upsert_jobs

    upsert_jobs([make_job("11111111", company="Acme", location="Pune",
                          search_location="pune"),
                 make_job("22222222", company="Globex", location="Remote",
                          search_location="pune",
                          title="Senior .NET Engineer")])
    rows, total = list_jobs()
    assert total == 2 and len(rows) == 2
    rows, total = list_jobs(q="acme")
    assert total == 1 and rows[0].company == "Acme"
    rows, total = list_jobs(q="engineer")
    assert total == 1 and rows[0].company == "Globex"
    rows, total = list_jobs(location="pune")  # matches search_location too
    assert total == 2
    rows, total = list_jobs(page=2, page_size=1)
    assert total == 2 and len(rows) == 1
    rows, total = list_jobs(page=9, page_size=10)
    assert total == 2 and rows == []


def test_get_job_found_and_missing(fresh_db):
    from src.db import upsert_jobs

    upsert_jobs([make_job("11111111")])
    assert get_job("11111111").title == "Senior .NET Developer"
    with pytest.raises(ApiError) as ei:
        get_job("nope")
    assert ei.value.status == 404


def test_get_stats_empty_and_seeded(fresh_db):
    from src.db import upsert_jobs

    empty = get_stats()
    assert empty["total_jobs"] == 0 and empty["by_location"] == []
    upsert_jobs([make_job("11111111", company="Acme", location="Pune"),
                 make_job("22222222", company="Acme", location="Hyderabad")])
    full = get_stats()
    assert full["total_jobs"] == 2 and full["new_last_24h"] == 2
    assert full["by_company"][0] == {"name": "Acme", "count": 2}
    assert len(full["by_location"]) == 2


# ---------------------------------------------------------------------------
# orchestrator — runs, cancel, eviction, default runners
# ---------------------------------------------------------------------------
def test_start_and_finish_success():
    orch = Orchestrator(scrape_runner=_instant(), export_runner=_instant())
    s = orch.start_scrape({"keywords": "x"})
    e = orch.start_export({"format": "csv"})
    assert s.run_id.startswith("scrape-") and e.run_id.startswith("export-")
    assert orch.wait_for(s.run_id).status == "succeeded"
    final = orch.wait_for(e.run_id)
    assert final.summary["found"] == 1 and final.summary["log"].endswith(".log")
    assert final.to_dict()["events"][-1]["stage"] == "done"
    assert orch.active_count() == 0
    assert [r.run_id for r in orch.list_runs()] == [e.run_id, s.run_id]
    d = s.to_dict()
    assert d["params"] == {"keywords": "x"} and d["error"] == ""


def test_scrape_lock_and_cancel_flow():
    orch = Orchestrator(scrape_runner=_blocking(), export_runner=_instant())
    rec = orch.start_scrape({})
    assert orch.active_count() == 1
    with pytest.raises(BusyError):
        orch.start_scrape({})  # one polite pass at a time
    out = orch.cancel(rec.run_id)
    assert out.status == "cancelling" and out.cancel_requested
    done = orch.wait_for(rec.run_id, timeout=10)
    assert done.status == "cancelled"  # partials kept, worker landed it
    with pytest.raises(RunNotCancellable):
        orch.cancel(rec.run_id)  # terminal runs reject cancel loudly


def test_unknown_run_errors():
    orch = Orchestrator(scrape_runner=_instant(), export_runner=_instant())
    with pytest.raises(RunNotFound):
        orch.get("scrape-9999")
    with pytest.raises(RunNotFound):
        orch.cancel("scrape-9999")
    with pytest.raises(RunNotFound):
        orch.wait_for("scrape-9999")


def test_failing_runner_marks_failed_and_frees_lock():
    orch = Orchestrator(scrape_runner=_failing(), export_runner=_instant())
    rec = orch.start_scrape({})
    done = orch.wait_for(rec.run_id, timeout=10)
    assert done.status == "failed" and "boom" in done.error
    orch.start_scrape({})  # lock released even on failure
    with pytest.raises(RunNotCancellable):
        orch.cancel(rec.run_id)


def test_run_history_evicts_oldest():
    orch = Orchestrator(scrape_runner=_instant(), export_runner=_instant(),
                        max_runs=3)
    ids = [orch.start_export({}).run_id for _ in range(4)]
    orch.wait_all()
    kept = {r.run_id for r in orch.list_runs()}
    assert len(kept) == 3 and ids[0] not in kept


def test_default_export_runner_writes_files(fresh_db, tmp_path, monkeypatch):
    from src.config import SETTINGS
    from src.db import upsert_jobs

    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    upsert_jobs([make_job("11111111")])
    out = default_export_runner(RunRecord(run_id="e", kind="export", seq=1,
                                          params={"format": "excel",
                                                  "location": ""}))
    assert out["file"].endswith(".xlsx") and (tmp_path / out["file"]).exists()
    out = default_export_runner(RunRecord(run_id="e", kind="export", seq=2,
                                          params={}))
    assert out["file"].endswith(".csv")


class _FakePW:
    """sync_playwright() stand-in yielding a dummy handle."""

    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


def _wire_browser(monkeypatch, page):
    monkeypatch.setattr("playwright.sync_api.sync_playwright", lambda: _FakePW())
    monkeypatch.setattr("src.stealth_browser.launch_context",
                        lambda p: FakeContext(page))
    monkeypatch.setattr(ns, "human_pause", lambda *a, **k: None)


def _tune_web(monkeypatch, tmp_path, **kw):
    from src.config import SETTINGS

    base = dict(keywords="asp.net core", locations=["pune"], experience=6,
                date_filter=7, max_pages_per_search=1, max_jobs_total=10,
                enrich_details=True)
    base.update(kw)
    for k, v in base.items():
        monkeypatch.setattr(SETTINGS, k, v)
    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    return SETTINGS


def test_default_scrape_runner_full_params(fresh_db, tmp_path, monkeypatch):
    from src.config import SETTINGS

    settings = _tune_web(monkeypatch, tmp_path, locations=["pune", "hyderabad"])
    before = (settings.keywords, list(settings.locations), settings.experience,
              settings.date_filter, settings.max_pages_per_search,
              settings.max_jobs_total, settings.enrich_details)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111")], [raw_card("22222222")]]
    page.detail_result = {"skills": ["C#"]}
    _wire_browser(monkeypatch, page)
    rec = RunRecord(run_id="s", kind="scrape", seq=1,
                    params={"keywords": "asp.net core", "locations": "pune,hyderabad",
                            "experience": 6, "days": 7, "pages": 1,
                            "max_jobs": 10, "enrich": True})
    summary = default_scrape_runner(rec)
    assert summary["found"] == 2 and summary["new"] == 2
    assert summary["cancelled"] is False and summary["duration_s"] >= 0
    assert summary["verdict"].startswith("2 new of 2 collected across 2 location(s) in ")
    assert rec.progress["stage"] == "done"
    after = (settings.keywords, list(settings.locations), settings.experience,
             settings.date_filter, settings.max_pages_per_search,
             settings.max_jobs_total, settings.enrich_details)
    assert before == after  # SETTINGS restored for API readers


def test_default_scrape_runner_failure_restores_settings(fresh_db, tmp_path,
                                                         monkeypatch):
    from src.config import SETTINGS

    before_kw = SETTINGS.keywords
    _tune_web(monkeypatch, tmp_path)
    before_kw = SETTINGS.keywords
    _wire_browser(monkeypatch, FakePage())
    monkeypatch.setattr(ns, "run_scrape", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("net down")))
    with pytest.raises(RuntimeError, match="net down"):
        default_scrape_runner(RunRecord(run_id="s", kind="scrape", seq=1,
                                        params={}))
    assert SETTINGS.keywords == before_kw


def test_default_scrape_runner_immediate_stop(fresh_db, tmp_path, monkeypatch):
    _tune_web(monkeypatch, tmp_path)
    _wire_browser(monkeypatch, FakePage())
    rec = RunRecord(run_id="s", kind="scrape", seq=1, params={})
    rec._stop_event.set()
    summary = default_scrape_runner(rec)
    assert summary["found"] == 0 and summary["cancelled"] is True
    assert summary["verdict"].startswith("cancelled after ")


# ---------------------------------------------------------------------------
# REST — full contract via TestClient (lifespan incl. MCP mount)
# ---------------------------------------------------------------------------
@pytest.fixture
def web_env(tmp_path, fresh_db, monkeypatch):
    from src.config import SETTINGS
    from src.db import upsert_jobs

    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    upsert_jobs([make_job("11111111", company="Acme", location="Pune",
                          search_location="pune"),
                 make_job("22222222", company="Globex", location="Remote",
                          search_location="pune",
                          title="Senior .NET Engineer")])
    real_file = tmp_path / "naukri_export.csv"
    real_file.write_text("job_id\n11111111\n")
    orch = Orchestrator(scrape_runner=_instant(),
                        export_runner=lambda rec: {"file": real_file.name,
                                                   "path": str(real_file)})
    with TestClient(create_app(orch)) as client:
        yield client, orch


def test_health_stats_jobs(web_env):
    client, _ = web_env
    h = client.get("/api/health")
    assert h.status_code == 200 and h.json()["jobs"] == 2
    s = client.get("/api/stats").json()
    assert s["total_jobs"] == 2 and len(s["by_location"]) == 2
    pg = client.get("/api/jobs", params={"q": "acme"}).json()
    assert pg["total"] == 1 and pg["data"][0]["company"] == "Acme"
    pg = client.get("/api/jobs", params={"page": 2, "page_size": 1}).json()
    assert pg["total"] == 2 and len(pg["data"]) == 1
    detail = client.get("/api/jobs/11111111")
    assert detail.status_code == 200 and detail.json()["job_id"] == "11111111"
    missing = client.get("/api/jobs/nope")
    assert missing.status_code == 404
    assert missing.json() == {"error": {"code": "JOB_NOT_FOUND",
                                        "message": "no job with id 'nope'"}}


def test_scrape_start_and_run_endpoints(web_env):
    client, orch = web_env
    started = client.post("/api/scrape", json={})
    assert started.status_code == 202
    run_id = started.json()["run_id"]
    orch.wait_for(run_id, timeout=10)
    got = client.get(f"/api/runs/{run_id}").json()
    assert got["status"] == "succeeded" and got["summary"]["found"] == 1
    listed = client.get("/api/runs").json()
    assert run_id in {r["run_id"] for r in listed}
    assert client.get("/api/runs/scrape-9999").status_code == 404


def test_cancel_twins(web_env):
    client, orch = web_env
    exp = client.post("/api/exports", json={"format": "csv"}).json()
    orch.wait_for(exp["run_id"], timeout=10)
    done = client.post(f"/api/runs/{exp['run_id']}/cancel")
    assert done.status_code == 409  # finished runs reject cancel loudly
    assert done.json()["error"]["code"] == "RUN_NOT_CANCELLABLE"
    unknown = client.post("/api/runs/scrape-9999/cancel")
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "RUN_NOT_FOUND"


def test_cancel_running_scrape_via_api(fresh_db, tmp_path, monkeypatch):
    from src.config import SETTINGS

    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    orch = Orchestrator(scrape_runner=_blocking(), export_runner=_instant())
    with TestClient(create_app(orch)) as client:
        first = client.post("/api/scrape", json={}).json()
        assert client.get("/api/stats").json()["active_runs"] == 1
        busy = client.post("/api/scrape", json={})
        assert busy.status_code == 409
        assert busy.json()["error"]["code"] == "SCRAPE_ALREADY_RUNNING"
        cancelled = client.post(f"/api/runs/{first['run_id']}/cancel").json()
        assert cancelled["status"] == "cancelling"
        orch.wait_for(first["run_id"], timeout=10)
        assert client.get(f"/api/runs/{first['run_id']}").json()["status"] == "cancelled"


def test_export_download_states(fresh_db, tmp_path, monkeypatch):
    from src.config import SETTINGS

    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    real = tmp_path / "got.csv"
    real.write_text("job_id\n")
    orch = Orchestrator(scrape_runner=_instant(),
                        export_runner=lambda rec: {"file": real.name,
                                                   "path": str(real)})
    with TestClient(create_app(orch)) as client:
        run_id = client.post("/api/exports", json={}).json()["run_id"]
        orch.wait_for(run_id, timeout=10)
        dl = client.get(f"/api/runs/{run_id}/download")
        assert dl.status_code == 200 and "job_id" in dl.text
        scrape_id = client.post("/api/scrape", json={}).json()["run_id"]
        assert client.get(f"/api/runs/{scrape_id}/download").status_code == 409


def test_export_download_pending_and_missing(fresh_db, tmp_path, monkeypatch):
    from src.config import SETTINGS

    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    orch = Orchestrator(scrape_runner=_instant(), export_runner=_blocking())
    with TestClient(create_app(orch)) as client:
        run_id = client.post("/api/exports", json={}).json()["run_id"]
        pending = client.get(f"/api/runs/{run_id}/download")
        assert pending.status_code == 409  # not succeeded yet
        orch.cancel(run_id)
        orch.wait_for(run_id, timeout=10)
    ghost = Orchestrator(scrape_runner=_instant(),
                         export_runner=lambda rec: {"file": "gone.csv",
                                                    "path": "/nonexistent/gone.csv"})
    with TestClient(create_app(ghost)) as client:
        run_id = client.post("/api/exports", json={}).json()["run_id"]
        ghost.wait_for(run_id, timeout=10)
        assert client.get(f"/api/runs/{run_id}/download").status_code == 404


def test_validation_error_envelope(web_env):
    client, _ = web_env
    bad = client.post("/api/scrape", json={"pages": 0})
    assert bad.status_code == 422
    body = bad.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["details"]


def test_dashboard_scalar_openapi(web_env):
    client, _ = web_env
    page = client.get("/")
    assert page.status_code == 200
    assert "IBM Plex Mono" in page.text and "/api/scrape" in page.text
    assert "database" in page.text and "run logs" in page.text  # req: browse store + logs
    scalar = client.get("/scalar")
    assert scalar.status_code == 200
    spec = client.get("/openapi.json").json()
    assert "/api/scrape" in spec["paths"]
    assert spec["paths"]["/api/runs/{run_id}/cancel"]["post"]["operationId"] == "cancel_run"


def test_app_without_optional_deps(monkeypatch):
    monkeypatch.setitem(sys.modules, "fastmcp", None)
    monkeypatch.setitem(sys.modules, "scalar_fastapi", None)
    orch = Orchestrator(scrape_runner=_instant(), export_runner=_instant())
    assert build_mcp(orch) is None  # MCP layer degrades, REST keeps working
    client = TestClient(create_app(orch))
    assert client.get("/api/health").status_code == 200


# ---------------------------------------------------------------------------
# MCP tools — curated surface via in-memory client
# ---------------------------------------------------------------------------
def _tool(mcp, name, args):
    from fastmcp import Client

    async def _go():
        async with Client(mcp) as c:
            return await c.call_tool(name, args)

    return asyncio.run(_go())


def _payload(result):
    if result.data is not None:
        return result.data
    return json.loads(result.content[0].text)


def test_mcp_read_tools(fresh_db):
    from src.db import upsert_jobs

    upsert_jobs([make_job("11111111", company="Acme")])
    orch = Orchestrator(scrape_runner=_instant(), export_runner=_instant())
    mcp = build_mcp(orch)
    assert {t.name for t in asyncio.run(_tools(mcp))} == {
        "collector_stats", "search_jobs", "start_scrape", "start_skill_scan",
        "run_status", "cancel_run"}
    stats = _payload(_tool(mcp, "collector_stats", {}))
    assert stats["total_jobs"] == 1
    found = _payload(_tool(mcp, "search_jobs", {"query": "acme"}))
    assert found["total"] == 1 and found["jobs"][0]["company"] == "Acme"
    assert _payload(_tool(mcp, "run_status", {"run_id": "x"}))["error"]


async def _tools(mcp):
    from fastmcp import Client

    async with Client(mcp) as c:
        return await c.list_tools()


def test_mcp_start_and_cancel(fresh_db, tmp_path, monkeypatch):
    from src.config import SETTINGS

    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    orch = Orchestrator(scrape_runner=_blocking(), export_runner=_instant(),
                        skills_runner=_instant())
    mcp = build_mcp(orch)
    started = _payload(_tool(mcp, "start_scrape",
                             {"keywords": "x", "locations": "pune"}))
    assert started["status"] in ("running", "cancelling")
    stopped = _payload(_tool(mcp, "cancel_run", {"run_id": started["run_id"]}))
    assert stopped["cancel_requested"] is True
    orch.wait_for(started["run_id"], timeout=10)
    assert _payload(_tool(mcp, "cancel_run",
                          {"run_id": "nope"}))["error"]
    monkeypatch.setattr(orch, "start_scrape",
                        lambda params: (_ for _ in ()).throw(BusyError("busy")))
    assert _payload(_tool(mcp, "start_scrape", {}))["error"] == "busy"
    assert _payload(_tool(mcp, "start_skill_scan",
                          {"keywords": "x"})).get("run_id", "").startswith("skills-")
    monkeypatch.setattr(orch, "start_skills",
                        lambda params: (_ for _ in ()).throw(BusyError("busy")))
    assert _payload(_tool(mcp, "start_skill_scan",
                          {"keywords": "x"}))["error"] == "busy"


# ---------------------------------------------------------------------------
# CLI — `web` command serves on the given host/port
# ---------------------------------------------------------------------------
def test_web_command_serves(monkeypatch, fresh_db):
    import uvicorn

    calls: dict = {}
    monkeypatch.setattr(uvicorn, "run",
                        lambda app, host=None, port=None, **k: calls.update(
                            app=app, host=host, port=port))
    result = CliRunner().invoke(main.app, ["web", "--port", "8123"])
    assert result.exit_code == 0
    assert calls == {"app": calls["app"], "host": "127.0.0.1", "port": 8123}
    assert "8123" in result.output


# ---------------------------------------------------------------------------
# runlog — per-run files, both loggers, timestamped lines
# ---------------------------------------------------------------------------
def test_run_log_captures_python_and_playwright_with_timestamps():
    import logging

    from src.web.runlog import attached_run_log, list_log_files, read_log_file

    logging.getLogger("src.web.test").info("python hello")
    with attached_run_log("scrape", "scrape-0001") as name:
        assert name.startswith("scrape_scrape-0001_") and name.endswith(".log")
        logging.getLogger("src.web.test").info("inside run")
        logging.getLogger("playwright").info("browser hello")
    body = read_log_file(name)
    assert "inside run" in body and "browser hello" in body
    import re as _re
    assert _re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} INFO", body)
    assert "python hello" not in body  # outside the context: not captured
    files = list_log_files()
    assert files[0]["name"] == name and files[0]["size"] > 0
    assert read_log_file(name, max_lines=1).count("\n") == 0  # tail of 1


def test_read_log_file_rejects_bad_names(tmp_path, monkeypatch):
    from src.config import SETTINGS
    from src.web.runlog import LogNotFound, read_log_file

    monkeypatch.setattr(SETTINGS, "log_dir", tmp_path / "logs")
    with pytest.raises(LogNotFound):
        read_log_file("../evil.log")
    with pytest.raises(LogNotFound):
        read_log_file("missing.log")


# ---------------------------------------------------------------------------
# crud explorer — tables + rows over serverless SQLite
# ---------------------------------------------------------------------------
def test_db_explorer_tables_and_rows(fresh_db):
    from src.db import upsert_jobs

    upsert_jobs([make_job("11111111")])
    tables = {t["name"]: t for t in list_tables()}
    assert set(tables) == {"jobs", "scrape_runs"}
    assert "job_id" in tables["jobs"]["columns"] and tables["jobs"]["rows"] == 1
    cols, rows, total = table_rows("jobs", page=1, page_size=10)
    assert total == 1 and rows[0]["job_id"] == "11111111" and "title" in cols
    _, empty, _ = table_rows("jobs", page=9, page_size=10)
    assert empty == []
    with pytest.raises(TableNotFound):
        table_rows("pg_shadow")


# ---------------------------------------------------------------------------
# ops router — /api/db/*, /api/logs/*, dependency override
# ---------------------------------------------------------------------------
def test_ops_db_and_log_endpoints(web_env):
    client, orch = web_env
    tables = client.get("/api/db/tables").json()
    assert {t["name"] for t in tables} == {"jobs", "scrape_runs"}
    page = client.get("/api/db/tables/jobs", params={"page_size": 1}).json()
    assert page["total"] == 2 and len(page["data"]) == 1
    assert client.get("/api/db/tables/nope").status_code == 404
    assert client.get("/api/db/tables/nope").json()["error"]["code"] == "TABLE_NOT_FOUND"
    rec = orch.start_export({})
    orch.wait_for(rec.run_id, timeout=10)
    logs = client.get("/api/logs").json()
    assert rec.run_id in logs[0]["name"]
    tail = client.get(f"/api/logs/{logs[0]['name']}", params={"max_lines": 5})
    assert tail.status_code == 200
    assert client.get("/api/logs/../x").status_code == 404


def test_dependency_override_injects_orchestrator(fresh_db):
    from fastapi.testclient import TestClient

    from src.web.main import create_app

    orch = Orchestrator(scrape_runner=_instant(), export_runner=_instant())
    app = create_app()  # default orchestrator inside...
    app.dependency_overrides[get_orchestrator] = lambda: orch  # ...swapped here
    with TestClient(app) as client:
        run_id = client.post("/api/exports", json={}).json()["run_id"]
        assert orch.wait_for(run_id, timeout=10).status == "succeeded"


def test_run_events_timeline_capped():
    rec = RunRecord(run_id="s", kind="scrape", seq=1)
    for i in range(60):
        rec.push_progress({"stage": "search", "page": i})
    assert len(rec.events) == 60  # deque keeps 500...
    assert len(rec.to_dict()["events"]) == 50  # ...API ships newest 50
    assert rec.to_dict()["events"][-1]["page"] == 59


def test_config_log_dir_default(tmp_path, monkeypatch):
    from src import config

    monkeypatch.delenv("LOG_DIR", raising=False)
    assert config.Settings().log_dir.name == "logs"


# ---------------------------------------------------------------------------
# skills runs — scan kind, report file, API, MCP, dashboard
# ---------------------------------------------------------------------------
def test_start_skills_shares_browser_lock():
    orch = Orchestrator(scrape_runner=_blocking(), export_runner=_instant(),
                        skills_runner=_blocking())
    rec = orch.start_skills({"keywords": "x"})
    assert rec.run_id.startswith("skills-")
    with pytest.raises(BusyError):
        orch.start_skills({"keywords": "y"})
    with pytest.raises(BusyError):
        orch.start_scrape({})  # one browser: skills run holds the lock
    orch.cancel(rec.run_id)
    assert orch.wait_for(rec.run_id, timeout=10).status == "cancelled"


def _force_browser_fallback(monkeypatch):
    from src.web import nkapi as _nk
    from src.web.nkapi import NkApiError as _NkErr

    def _down(*a, **k):
        raise _NkErr("rate limited", status=406)

    monkeypatch.setattr(_nk, "fetch_search_page", _down)


def test_default_skills_runner_full(fresh_db, tmp_path, monkeypatch):
    from src.config import SETTINGS
    from src.web.orchestrator import default_skills_runner

    _force_browser_fallback(monkeypatch)
    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    _tune_web(monkeypatch, tmp_path)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111")], [raw_card("22222222")]]
    page.detail_result = {"skills": ["C#", "SQL"]}
    _wire_browser(monkeypatch, page)
    rec = RunRecord(run_id="k", kind="skills", seq=1,
                    params={"keywords": "asp.net core, web api",
                            "location": "pune", "experience": 6,
                            "days": 7, "pages": 2, "max_jobs": 10})
    summary = default_skills_runner(rec)
    assert summary["jobs_scanned"] == 2 and summary["unique_skills"] == 2
    assert summary["count_mode"] == "companies"  # new default
    assert summary["top"][0]["skill"] == "C#" and summary["top"][0]["count"] == 1
    assert summary["top"][0]["companies"] == [{"name": "Acme", "count": 2}]
    assert summary["cancelled"] is False and "top: C#, SQL" in summary["verdict"]
    assert summary["source"] == "browser"  # API refused -> browser fallback
    dest = tmp_path / summary["file"]
    assert dest.suffix == ".txt" and "1x (100.0%)  C#" in dest.read_text()
    assert "Acme x2" in dest.read_text() and "distinct companies" in dest.read_text()


def test_default_skills_runner_empty(fresh_db, tmp_path, monkeypatch):
    from src.config import SETTINGS
    from src.web.orchestrator import default_skills_runner, render_skills_text

    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    _force_browser_fallback(monkeypatch)
    _tune_web(monkeypatch, tmp_path)
    _wire_browser(monkeypatch, FakePage())
    rec = RunRecord(run_id="k", kind="skills", seq=1,
                    params={"keywords": "zzz-no-such-title"})
    summary = default_skills_runner(rec)
    assert summary["jobs_scanned"] == 0 and summary["top"] == []
    assert summary["verdict"].startswith("no postings found")
    assert "Unique skills: 0" in render_skills_text(summary, rec.params)


def test_skills_api_flow(fresh_db, tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from src.config import SETTINGS
    from src.web.main import create_app

    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    report = tmp_path / "skills_demo.txt"
    report.write_text("  12x (60.0%)  C#\n")
    orch = Orchestrator(scrape_runner=_instant(), export_runner=_instant(),
                        skills_runner=_instant({"jobs_scanned": 20,
                                                "with_skills": 18,
                                                "unique_skills": 9,
                                                "top": [{"skill": "C#",
                                                         "count": 12,
                                                         "pct": 60.0}],
                                                "file": report.name,
                                                "path": str(report)}))
    with TestClient(create_app(orch)) as client:
        started = client.post("/api/skills", json={"keywords": "asp.net core"})
        assert started.status_code == 202
        run_id = started.json()["run_id"]
        assert orch.wait_for(run_id, timeout=10).status == "succeeded"
        dl = client.get(f"/api/runs/{run_id}/download")
        assert dl.status_code == 200 and "C#" in dl.text
        assert client.post("/api/skills", json={}).status_code == 422
        assert client.post("/api/skills",
                           json={"keywords": "x", "max_jobs": 0}).status_code == 422
        assert client.post("/api/skills",
                           json={"keywords": "x",
                                 "count_mode": "bogus"}).status_code == 422


def test_skills_api_busy(fresh_db, tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from src.config import SETTINGS
    from src.web.main import create_app

    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    orch = Orchestrator(scrape_runner=_instant(), export_runner=_instant(),
                        skills_runner=_blocking())
    with TestClient(create_app(orch)) as client:
        first = client.post("/api/skills", json={"keywords": "x"}).json()
        busy = client.post("/api/skills", json={"keywords": "y"})
        assert busy.status_code == 409
        assert busy.json()["error"]["code"] == "SCRAPE_ALREADY_RUNNING"
        client.post(f"/api/runs/{first['run_id']}/cancel")
        assert orch.wait_for(first["run_id"], timeout=10).status == "cancelled"


def test_dashboard_has_skills_section(web_env):
    client, _ = web_env
    resp = client.get("/")
    page = resp.text
    assert "key skills" in page
    assert 'role="switch"' in page and 'aria-checked="true"' in page  # default on
    assert "distinct companies" in page and "skillsView" in page
    assert resp.headers["cache-control"] == "no-store"


# ---------------------------------------------------------------------------
# nkapi — direct search API fast path (mocked HTTP, no network)
# ---------------------------------------------------------------------------
def _api_job(job_id, skills="C#, SQL", title="Senior .NET Developer",
             company="Acme"):
    return {"jobId": job_id, "title": title, "companyName": company,
            "experienceText": "6-8 Yrs", "tagsAndSkills": skills,
            "jdURL": f"/job-listings-dev-{job_id}",
            "jobDescription": "asp.net core c# fullstack"}


class _Resp:
    def __init__(self, status, payload=None):
        self.status_code = status
        self._payload = payload or {}

    def json(self):
        return self._payload


def test_generate_nkparam_shape():
    from src.web.nkapi import _read_der, generate_nkparam

    tok = generate_nkparam()
    assert len(tok) == 88  # 64-byte RSA-512 ciphertext, like the HAR value
    import base64 as _b64
    assert len(_b64.b64decode(tok)) == 64
    assert generate_nkparam() != tok  # random PKCS#1 v1.5 padding
    assert _read_der(b"\x30\x81\x05hello", 0) == (b"hello", 8)  # long form


def test_fetch_search_page_outcomes(monkeypatch):
    import src.web.nkapi as nk

    calls = {}

    def _ok(url, params=None, headers=None, timeout=None):
        calls["params"] = params
        assert headers["appid"] == "109" and len(headers["nkparam"]) == 88
        assert params["pageNo"] == 1 and params["jobAge"] == 7
        return _Resp(200, {"jobDetails": [_api_job("100001")], "noOfJobs": 45})

    monkeypatch.setattr(nk.httpx, "get", _ok)
    rows, total = nk.fetch_search_page("x", "pune", 6, 7, 1)
    assert total == 45 and rows[0]["jobId"] == "100001"
    monkeypatch.setattr(nk.httpx, "get", lambda *a, **k: _Resp(400))
    assert nk.fetch_search_page("x", "pune", 6, 7, 9) == ([], None)
    monkeypatch.setattr(nk.httpx, "get", lambda *a, **k: _Resp(406))
    with pytest.raises(nk.NkApiError) as ei:
        nk.fetch_search_page("x", "pune", 6, 7, 1)
    assert ei.value.status == 406

    def _down(*a, **k):
        raise RuntimeError("net down")

    monkeypatch.setattr(nk.httpx, "get", _down)
    with pytest.raises(nk.NkApiError):
        nk.fetch_search_page("x", "pune", 6, 7, 1)


def test_api_job_to_raw_mapping():
    from src.web.nkapi import api_job_to_raw

    raw = api_job_to_raw(_api_job("11111111"))
    assert raw["jobId"] == "11111111" and raw["company"] == "Acme"
    assert raw["skills"] == ["C#", "SQL"]
    assert raw["url"] == "https://www.naukri.com/job-listings-dev-11111111"
    bare = api_job_to_raw({"jobId": "1"})
    assert bare["url"] == "" and bare["skills"] == []  # missing -> droppable


def _api_params(**over):
    base = {"keywords": "asp.net core", "location": "pune", "experience": 6,
            "days": 7, "pages": 5, "max_jobs": 100}
    base.update(over)
    return base


def test_api_scan_skills_pages_and_caps(monkeypatch):
    import src.web.nkapi as nk

    monkeypatch.setattr(nk, "human_pause", lambda *a, **k: None)
    seen = []

    def _pages(url, params=None, headers=None, timeout=None):
        n = params["pageNo"]
        assert params["keyword"] == "asp.net core"
        jobs = [_api_job(f"200{i:03d}", skills="C#, SQL") for i in range(20)] if n == 1 \
            else [_api_job("200999", skills="Go", company="Globex")]
        return _Resp(200, {"jobDetails": jobs, "noOfJobs": 100})

    monkeypatch.setattr(nk.httpx, "get", _pages)
    rec = RunRecord(run_id="k", kind="skills", seq=1,
                    params=_api_params(max_jobs=25))
    rep = nk.api_scan_skills(rec.params, rec.should_stop, seen.append)
    assert rep["jobs_scanned"] == 21  # 20 + 1, then max reached
    assert rep["count_mode"] == "companies" and rep["companies_total"] == 2
    assert rep["top"][0] == {"skill": "C#", "count": 1, "pct": 50.0,
                             "companies": [{"name": "Acme", "count": 20}]}
    assert seen[-1]["source"] == "api" and seen[-1]["found"] == 21
    rep = nk.api_scan_skills({**rec.params, "count_mode": "postings"},
                             rec.should_stop, lambda p: None)
    assert rep["count_mode"] == "postings"  # legacy behavior kept
    assert rep["top"][0]["count"] == 20 and rep["top"][0]["pct"] == 95.2


def test_api_scan_skills_stops_and_breaks(monkeypatch):
    import src.web.nkapi as nk

    monkeypatch.setattr(nk, "human_pause", lambda *a, **k: None)
    calls = []

    def _one(url, params=None, headers=None, timeout=None):
        calls.append(params["pageNo"])
        return _Resp(200, {"jobDetails": [_api_job("100001")], "noOfJobs": 1})

    monkeypatch.setattr(nk.httpx, "get", _one)
    rec = RunRecord(run_id="k", kind="skills", seq=1, params=_api_params())
    rep = nk.api_scan_skills(rec.params, rec.should_stop, lambda p: None)
    assert rep["jobs_scanned"] == 1 and calls == [1]  # total hit: one request
    stopped = RunRecord(run_id="k", kind="skills", seq=2, params=_api_params())
    stopped._stop_event.set()
    rep = nk.api_scan_skills(stopped.params, stopped.should_stop, lambda p: None)
    assert rep["jobs_scanned"] == 0 and calls == [1]  # cancelled pre-fetch
    monkeypatch.setattr(nk.httpx, "get", lambda *a, **k: _Resp(200, {"jobDetails": []}))
    rep = nk.api_scan_skills(rec.params, rec.should_stop, lambda p: None)
    assert rep["jobs_scanned"] == 0  # empty page ends the scan


def test_api_scan_skills_skips_bad_rows(monkeypatch):
    import src.web.nkapi as nk

    monkeypatch.setattr(nk, "human_pause", lambda *a, **k: None)
    rows = [_api_job("11111111"), _api_job("11111111"),  # dup skipped
            {"jobId": "1", "title": "AB"}]  # invalid (short title) dropped
    monkeypatch.setattr(nk.httpx, "get",
                        lambda *a, **k: _Resp(200, {"jobDetails": rows,
                                                    "noOfJobs": 3}))
    rec = RunRecord(run_id="k", kind="skills", seq=1,
                    params=_api_params(max_jobs=10))
    rep = nk.api_scan_skills(rec.params, rec.should_stop, lambda p: None)
    assert rep["jobs_scanned"] == 1


def test_skills_runner_prefers_api(fresh_db, tmp_path, monkeypatch):
    from src.config import SETTINGS
    import src.web.nkapi as nk
    from src.web.orchestrator import default_skills_runner

    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    monkeypatch.setattr(nk, "human_pause", lambda *a, **k: None)
    monkeypatch.setattr(nk.httpx, "get", lambda *a, **k: _Resp(
        200, {"jobDetails": [_api_job("11111111")], "noOfJobs": 1}))
    rec = RunRecord(run_id="k", kind="skills", seq=1,
                    params=_api_params(max_jobs=10))
    summary = default_skills_runner(rec)
    assert summary["source"] == "api" and summary["jobs_scanned"] == 1
    assert summary["verdict"].startswith("2 unique skills across 1 postings")
    assert (tmp_path / summary["file"]).exists()


def test_api_scan_skills_cap_and_exhaustion(monkeypatch):
    import src.web.nkapi as nk

    monkeypatch.setattr(nk, "human_pause", lambda *a, **k: None)
    calls = []

    def _fresh(url, params=None, headers=None, timeout=None):
        calls.append(params["pageNo"])
        n = params["pageNo"]
        return _Resp(200, {"jobDetails": [_api_job(f"90{n:04d}")],
                           "noOfJobs": 10 ** 9})

    monkeypatch.setattr(nk.httpx, "get", _fresh)
    rec = RunRecord(run_id="k", kind="skills", seq=1,
                    params=_api_params(max_jobs=1))
    rep = nk.api_scan_skills(rec.params, rec.should_stop, lambda p: None)
    assert rep["jobs_scanned"] == 1 and calls == [1]  # cap hit on first row
    rec = RunRecord(run_id="k", kind="skills", seq=2,
                    params=_api_params(max_jobs=100))
    rep = nk.api_scan_skills(rec.params, rec.should_stop, lambda p: None)
    assert rep["jobs_scanned"] == 7 and len(calls) == 1 + 7  # range exhausted


def test_skills_runner_postings_mode(fresh_db, tmp_path, monkeypatch):
    from src.config import SETTINGS
    from src.web.orchestrator import default_skills_runner

    _force_browser_fallback(monkeypatch)
    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    _tune_web(monkeypatch, tmp_path)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111")], [raw_card("22222222")]]
    page.detail_result = {"skills": ["C#"]}
    _wire_browser(monkeypatch, page)
    rec = RunRecord(run_id="k", kind="skills", seq=1,
                    params={"keywords": "x", "count_mode": "postings",
                            "pages": 2, "max_jobs": 10})
    summary = default_skills_runner(rec)
    assert summary["count_mode"] == "postings"  # legacy toggle-off behavior
    assert summary["top"][0]["count"] == 2  # two postings, one company
    assert "per posting" in (tmp_path / summary["file"]).read_text()
