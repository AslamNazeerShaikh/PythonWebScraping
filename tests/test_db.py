"""Tests for src.db — URL resolution, init, upsert/dedupe, fetch, audit."""
from __future__ import annotations

from src import db
from src.config import SETTINGS
from tests.conftest import make_job


def test_resolve_url_relative_absolute_and_server():
    assert db._resolve_url("sqlite:///jobs.db").endswith("/jobs.db")
    assert db._resolve_url("sqlite:////abs/path.db") == "sqlite:////abs/path.db"
    assert db._resolve_url("postgresql://u@h/db") == "postgresql://u@h/db"


def test_get_engine_caches_singleton(fresh_db):
    assert db.get_engine() is db.get_engine()


def test_upsert_empty_short_circuits(fresh_db):
    assert db.upsert_jobs([]) == (0, 0)


def test_upsert_insert_then_dedupe_refresh(fresh_db):
    new, total = db.upsert_jobs([make_job("11111111"), make_job("22222222")])
    assert (new, total) == (2, 2)
    # Second run: same ids -> 0 new, fields refreshed, last_seen bumped.
    updated = make_job("11111111", title="Senior .NET Developer II",
                       description="new desc")
    new2, total2 = db.upsert_jobs([updated])
    assert (new2, total2) == (0, 1)
    fetched = {j.job_id: j for j in db.fetch_all_jobs()}
    assert fetched["11111111"].title == "Senior .NET Developer II"
    assert fetched["11111111"].description == "new desc"
    assert db.count_jobs() == 2


def test_upsert_empty_apply_url_falls_back(fresh_db):
    job = make_job("33333333", apply_url="")
    db.upsert_jobs([job])
    assert db.fetch_all_jobs()[0].apply_url == job.url


def test_record_run_and_fetch_limit(fresh_db):
    db.upsert_jobs([make_job("11111111")])
    db.record_run("kw", "pune", 2, 5, 1)
    with db.get_session() as s:
        from sqlalchemy import select
        from src.models import ScrapeRun
        runs = s.scalars(select(ScrapeRun)).all()
    assert len(runs) == 1
    assert (runs[0].keywords, runs[0].locations, runs[0].pages,
            runs[0].found, runs[0].new_jobs) == ("kw", "pune", 2, 5, 1)
    assert len(db.fetch_all_jobs(limit=1)) == 1


def test_count_empty_db(fresh_db):
    assert db.count_jobs() == 0
    assert db.fetch_all_jobs() == []


def test_settings_database_url_default_shape():
    assert SETTINGS.database_url.startswith("sqlite:///")
