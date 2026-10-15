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
from src.web.app import create_app
from src.web.data import get_job, get_stats, list_jobs
from src.web.errors import ApiError
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
    assert orch.wait_for(e.run_id).summary == {"found": 1, "new": 1}
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
    assert summary == {"found": 2, "new": 2, "cancelled": False}
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
    assert summary == {"found": 0, "new": 0, "cancelled": True}


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
        "collector_stats", "search_jobs", "start_scrape",
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
    orch = Orchestrator(scrape_runner=_blocking(), export_runner=_instant())
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
