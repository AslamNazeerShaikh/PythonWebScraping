"""Tests for src.main — startup setup, pipeline wiring, all 5 commands."""
from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

import src.main as main
from tests.conftest import FakeContext, make_job

runner = CliRunner()


# -- _ensure_env ---------------------------------------------------------------
def test_ensure_env_first_run_copies_example(tmp_path, fresh_db):
    (tmp_path / ".env.example").write_text("LOG_LEVEL=INFO\n")
    main._ensure_env(base_dir=tmp_path)  # covers the copy branch
    assert (tmp_path / ".env").exists()


def test_ensure_env_default_base_no_copy(fresh_db):
    main._ensure_env()  # real BASE_DIR already has .env -> skip copy


# -- do_scrape -------------------------------------------------------------------
class _FakePW:
    """sync_playwright() stand-in (context manager yielding a fake handle)."""

    def __init__(self, handle) -> None:
        self.handle = handle

    def __enter__(self):
        return self.handle

    def __exit__(self, *a):
        return False


def _wire_pipeline(monkeypatch, jobs):
    monkeypatch.setattr(main, "sync_playwright", lambda: _FakePW(object()))
    monkeypatch.setattr(main, "launch_context", lambda p: FakeContext())
    monkeypatch.setattr(main, "run_scrape", lambda ctx: jobs)


def test_do_scrape_empty_returns_zero(monkeypatch, fresh_db):
    _wire_pipeline(monkeypatch, [])
    assert main.do_scrape() == 0


def test_do_scrape_found_persists_and_snapshots(monkeypatch, fresh_db, tmp_path):
    from src.config import SETTINGS
    _wire_pipeline(monkeypatch, [make_job("11111111")])
    calls: dict = {}

    def _up(js):
        calls["up"] = js
        return (1, 1)

    def _saved(js):
        calls["saved"] = True
        return (Path("a"), Path("b"))

    monkeypatch.setattr(main, "upsert_jobs", _up)
    monkeypatch.setattr(main, "record_run", lambda *a, **k: calls.setdefault("rec", True))
    monkeypatch.setattr(main, "save_results", _saved)
    monkeypatch.setattr(SETTINGS, "keywords", "kw")
    monkeypatch.setattr(SETTINGS, "locations", ["pune"])
    assert main.do_scrape() == 0
    assert calls["up"][0].job_id == "11111111"
    assert calls["rec"] and calls["saved"]


# -- CLI commands ------------------------------------------------------------------
def test_scrape_command_delegates_to_pipeline(monkeypatch, fresh_db):
    monkeypatch.setattr(main, "do_scrape", lambda: 3)
    result = runner.invoke(main.app, ["scrape", "--locations", "pune",
                                      "--pages", "1", "--no-enrich"])
    assert result.exit_code == 3


def test_export_command_rejects_bad_format(fresh_db):
    assert runner.invoke(main.app, ["export", "--format", "xml"]).exit_code == 2


def test_export_command_ok(monkeypatch, fresh_db, tmp_path):
    monkeypatch.setattr(main, "export_jobs", lambda **k: tmp_path / "e.csv")
    result = runner.invoke(main.app, ["export", "--format", "csv"])
    assert result.exit_code == 0


def test_stats_command(fresh_db):
    from src.db import upsert_jobs
    upsert_jobs([make_job("11111111")])
    result = runner.invoke(main.app, ["stats"])
    assert result.exit_code == 0 and "Jobs in DB:" in result.output


def test_parse_command_offline(tmp_path, fresh_db):
    html = ("<html><body><article>"
            "<a href='/job-listings-dotnet-dev-12345678'>Senior .NET Developer</a>"
            "</article></body></html>")
    f = tmp_path / "saved.html"
    f.write_text(html)
    result = runner.invoke(main.app, ["parse", str(f)])
    assert result.exit_code == 0
    assert "1 valid Jobs" in result.output


def test_parse_command_all_invalid_yields_no_upsert(tmp_path, fresh_db):
    # Card passes the HTML parser (long title) but fails Pydantic (2-digit id
    # < min_length 3) -> `if j:` False branch + `if jobs:` False branch.
    html = ("<html><body><article>"
            "<a href='/job-listings-short-id-12'>A Long Enough Job Title</a>"
            "</article></body></html>")
    f = tmp_path / "bad.html"
    f.write_text(html)
    result = runner.invoke(main.app, ["parse", str(f)])
    assert result.exit_code == 0
    assert "0 valid Jobs" in result.output


def test_schedule_command_rejects_garbage(fresh_db):
    assert runner.invoke(main.app, ["schedule", "--hours", "abc"]).exit_code == 2


def test_schedule_command_ok(monkeypatch, fresh_db):
    seen: dict = {}
    import src.scheduler as sched_mod
    monkeypatch.setattr(sched_mod, "run_scheduled",
                        lambda hours: seen.setdefault("h", hours))
    result = runner.invoke(main.app, ["schedule", "--hours", "8,20"])
    assert result.exit_code == 0 and seen["h"] == [8, 20]
