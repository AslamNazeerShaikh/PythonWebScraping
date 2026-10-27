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
    seen: dict = {}

    def _fake(**kwargs):
        seen.update(kwargs)
        return tmp_path / "e.csv"

    monkeypatch.setattr(main, "export_jobs", _fake)
    result = runner.invoke(main.app, ["export", "--format", "csv"])
    assert result.exit_code == 0
    assert seen["days"] is None  # no --days: whole DB (back-compat)
    windowed = runner.invoke(main.app, ["export", "--days", "1"])
    assert windowed.exit_code == 0 and seen["days"] == 1
    strict = runner.invoke(main.app, ["export", "--location", "pune",
                                      "--location-match", "exact"])
    assert strict.exit_code == 0 and seen["location_match"] == "exact"
    bad = runner.invoke(main.app, ["export", "--location-match", "fuzzy"])
    assert bad.exit_code == 2  # rejected before export_jobs runs
    assert seen["exclude_unwanted"] is True  # lane gates default on
    opt_out = runner.invoke(main.app, ["export", "--include-unwanted"])
    assert opt_out.exit_code == 0 and seen["exclude_unwanted"] is False


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


# -- collect-emails / export-emails (LinkedIn email collector, Task 6) --------
def _wire_email_pipeline(monkeypatch, contacts, captured: dict | None = None):
    monkeypatch.setattr(main, "sync_playwright", lambda: _FakePW(object()))
    monkeypatch.setattr(main, "launch_context", lambda p: FakeContext())
    captured = captured if captured is not None else {}

    def _run(ctx, **kw):
        captured.update(kw)
        return contacts

    monkeypatch.setattr(main, "run_collect", _run)
    return captured


def test_collect_emails_empty_result_returns_zero(monkeypatch, fresh_db):
    _wire_email_pipeline(monkeypatch, [])
    res = runner.invoke(main.app,
                        ["collect-emails", "--domains", "ltm.com"])
    assert res.exit_code == 0
    assert "No emails" in res.output


def test_collect_emails_upserts_exports_and_reports(monkeypatch, fresh_db,
                                                    tmp_path):
    from src.models import EmailContact
    captured = _wire_email_pipeline(monkeypatch, [
        EmailContact(email="neha.pandey@ltm.com", domain="ltm.com",
                     keyword="@ltm.com", author="Neha Pandey")
    ])
    monkeypatch.setattr(main.SETTINGS, "output_dir", tmp_path)
    res = runner.invoke(main.app, [
        "collect-emails", "--domains", "ltm.com", "--max-scrolls", "2",
        "--headless"])
    assert res.exit_code == 0
    assert captured["domains"] == ["ltm.com"]
    assert captured["targets"] == {"ltm.com": main.SETTINGS.email_default_target}
    assert captured["max_scrolls"] == 2
    assert callable(captured["on_batch"])
    assert fresh_db.count_emails() == 1
    assert "(1 new)" in res.output
    written = list(tmp_path.glob("linkedin_emails_*.xlsx"))
    assert len(written) == 2                      # checkpoint + final snapshot
    assert any(p.name == "linkedin_emails_partial.xlsx" for p in written)


def test_collect_emails_defaults_to_settings_domains(monkeypatch, fresh_db):
    captured = _wire_email_pipeline(monkeypatch, [])
    res = runner.invoke(main.app, ["collect-emails"])
    assert res.exit_code == 0
    assert captured["domains"] == main.SETTINGS.email_domains
    assert captured["targets"] == {
        d: main.SETTINGS.email_default_target
        for d in main.SETTINGS.email_domains
    }
    assert captured["max_scrolls"] is None        # SETTINGS.email_max_scrolls


def test_collect_emails_checkpoint_skips_empty_and_duplicate_batches(
        monkeypatch, fresh_db, tmp_path):
    """Checkpoint hook ignores empty/duplicate batches (no redundant exports)."""
    from src.models import EmailContact

    contact = EmailContact(email="neha.pandey@ltm.com", domain="ltm.com",
                           keyword="@ltm.com", author="Neha Pandey")

    def _run(_ctx, **kw):
        kw["on_batch"]([])
        kw["on_batch"]([contact])
        kw["on_batch"]([contact])       # same (email, post_id) → skip
        return [contact]

    monkeypatch.setattr(main, "sync_playwright", lambda: _FakePW(object()))
    monkeypatch.setattr(main, "launch_context", lambda p: FakeContext())
    monkeypatch.setattr(main, "run_collect", _run)
    monkeypatch.setattr(main.SETTINGS, "output_dir", tmp_path)
    res = runner.invoke(main.app, ["collect-emails", "--domains", "ltm.com"])
    assert res.exit_code == 0
    assert fresh_db.count_emails() == 1
    assert "(1 new)" in res.output


def test_export_emails_command_excel(monkeypatch, fresh_db, tmp_path):
    from src.db import upsert_emails
    from src.models import EmailContact

    upsert_emails([EmailContact(email="hr@tcs.com", domain="tcs.com")])
    res = runner.invoke(main.app, [
        "export-emails", "--format", "excel", "--out", str(tmp_path / "e.xlsx")])
    assert res.exit_code == 0
    assert (tmp_path / "e.xlsx").exists()
    assert "Exported" in res.output


def test_export_emails_command_rejects_bad_fmt(fresh_db):
    res = runner.invoke(main.app, ["export-emails", "--format", "pdf"])
    assert res.exit_code == 2
    assert "--format must be csv or excel" in res.output


def test_collect_emails_reads_csv_targets_in_order(monkeypatch, fresh_db,
                                                   tmp_path):
    csv_path = tmp_path / "targets.csv"
    csv_path.write_text("@cognizant.com:5,@capgemini.com:2\n", encoding="utf-8")
    captured = _wire_email_pipeline(monkeypatch, [])
    res = runner.invoke(main.app, ["collect-emails",
                                   "--input-csv", str(csv_path)])
    assert res.exit_code == 0
    assert captured["domains"] == ["cognizant.com", "capgemini.com"]
    assert captured["targets"] == {"cognizant.com": 5,
                                   "capgemini.com": 2}
    assert "cognizant.com:5" in res.output
    assert "capgemini.com:2" in res.output


def test_collect_emails_csv_missing_file_exits_2(monkeypatch, fresh_db,
                                                 tmp_path):
    res = runner.invoke(main.app, [
        "collect-emails", "--input-csv", str(tmp_path / "missing.csv")])
    assert res.exit_code == 2
    assert "Invalid --input-csv" in res.output


def test_collect_emails_csv_without_domains_exits_2(monkeypatch, fresh_db,
                                                    tmp_path):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("domain,target\n", encoding="utf-8")
    res = runner.invoke(main.app, ["collect-emails",
                                   "--input-csv", str(csv_path)])
    assert res.exit_code == 2
    assert "no company domains" in res.output


def test_collect_emails_csv_end_to_end_writes_clean_deduped_workbook(
        monkeypatch, fresh_db, tmp_path):
    """CSV targets → checkpoint hook → domain-pure, one-row-per-email Excel."""
    import pandas as pd
    from src.models import EmailContact

    csv_path = tmp_path / "targets.csv"
    csv_path.write_text("@tcs.com:2,@wipro.com:1\n", encoding="utf-8")
    contacts = [
        EmailContact(email="a@tcs.com", domain="tcs.com", posted="2d",
                     post_id="new"),
        EmailContact(email="a@tcs.com", domain="tcs.com", posted="1mo",
                     post_id="old"),
        EmailContact(email="b@tcs.com", domain="tcs.com", posted="5d",
                     post_id="b"),
        EmailContact(email="c@wipro.com", domain="wipro.com", posted="1w",
                     post_id="c"),
        EmailContact(email="outsider@gmail.com", domain="tcs.com",
                     posted="1h", post_id="junk"),
    ]

    def _run(_ctx, **kw):
        kw["on_batch"](contacts)
        return contacts

    monkeypatch.setattr(main, "sync_playwright", lambda: _FakePW(object()))
    monkeypatch.setattr(main, "launch_context", lambda p: FakeContext())
    monkeypatch.setattr(main, "run_collect", _run)
    monkeypatch.setattr(main.SETTINGS, "output_dir", tmp_path)
    res = runner.invoke(main.app, ["collect-emails",
                                   "--input-csv", str(csv_path)])
    assert res.exit_code == 0
    written = sorted(tmp_path.glob("linkedin_emails_*.xlsx"))
    assert any(p.name == "linkedin_emails_partial.xlsx" for p in written)
    final = [p for p in written if p.name != "linkedin_emails_partial.xlsx"][0]
    df = pd.read_excel(final)
    assert list(df["email"]) == ["a@tcs.com", "b@tcs.com", "c@wipro.com"]
    assert df[df.email == "a@tcs.com"].iloc[0]["post_id"] == "new"
    assert "outsider@gmail.com" not in set(df["email"])


# -- collect-role-emails (targeted LinkedIn collector) -------------------------
def test_do_collect_role_emails_writes_checkpoint_and_final(monkeypatch,
                                                            fresh_db, tmp_path):
    from src.linkedin_role_email import RoleEmailContact

    captured: dict = {}

    def _run(ctx, domains, phrase, target, checkpoint, maximum, pause, on_domain=None):
        contact = RoleEmailContact(email="a@ltm.com", company="LTIMindtree",
                                   company_domain="ltm.com", post_id="p1")
        captured.update({
            "domains": domains, "phrase": phrase, "target": target,
            "checkpoint": checkpoint, "maximum": maximum, "pause": pause,
        })
        on_domain([contact], [{"post_id": "p1", "text": "ASP.NET Core"}],
                  [{"company": "LTIMindtree", "company_domain": "ltm.com"}])
        return [contact], [{"post_id": "p1", "text": "ASP.NET Core"}], [
            {"company": "LTIMindtree", "company_domain": "ltm.com"}]

    monkeypatch.setattr(main, "sync_playwright", lambda: _FakePW(object()))
    monkeypatch.setattr(main, "launch_context", lambda p: FakeContext())
    monkeypatch.setattr(main, "run_role_collect", _run)
    monkeypatch.setattr(main.SETTINGS, "output_dir", tmp_path)
    code = main.do_collect_role_emails(
        ["ltm.com"], "asp.net core", 10, 20, 30, 0, None, False)
    assert code == 0
    assert captured["domains"] == ["ltm.com"]
    assert list(tmp_path.glob("linkedin_role_emails_*.xlsx"))


def test_do_collect_role_emails_explicit_out_and_empty(monkeypatch, fresh_db,
                                                       tmp_path):
    path = tmp_path / "chosen.xlsx"

    def _run(*args, **kwargs):
        return [], [], []

    monkeypatch.setattr(main, "sync_playwright", lambda: _FakePW(object()))
    monkeypatch.setattr(main, "launch_context", lambda p: FakeContext())
    monkeypatch.setattr(main, "run_role_collect", _run)
    code = main.do_collect_role_emails(
        ["x.com"], "asp.net core", 10, 20, 30, 0, str(path), False)
    assert code == 0 and path.exists()


def test_collect_role_emails_command_delegates_and_validates(monkeypatch,
                                                             fresh_db):
    seen: dict = {}

    def _do(*args):
        seen["args"] = args
        return 7

    monkeypatch.setattr(main, "do_collect_role_emails", _do)
    res = runner.invoke(main.app, [
        "collect-role-emails", "--phrase", "asp.net core",
        "--domains", "ltm.com,tcs.com", "--target", "3",
        "--checkpoint-posts", "10", "--max-posts", "20", "--pause", "0",
        "--out", "x.xlsx", "--headless"])
    assert res.exit_code == 7
    assert seen["args"][0] == ["ltm.com", "tcs.com"]
    assert seen["args"][1] == "asp.net core"
    assert seen["args"][2:6] == (3, 10, 20, 0)
    assert seen["args"][6] == "x.xlsx"
    assert main.SETTINGS.headless is True

    bad = runner.invoke(main.app, [
        "collect-role-emails", "--checkpoint-posts", "30", "--max-posts", "20"])
    assert bad.exit_code == 2
    assert "cannot exceed" in bad.output


def test_collect_role_emails_command_empty_phrase_uses_default(monkeypatch,
                                                               fresh_db):
    seen: dict = {}

    def _do(*args):
        seen["args"] = args
        return 0

    monkeypatch.setattr(main, "do_collect_role_emails", _do)
    res = runner.invoke(main.app, [
        "collect-role-emails", "--phrase", "", "--domains", "ltm.com"])
    assert res.exit_code == 0
    assert seen["args"][1] == main.DEFAULT_PHRASE
