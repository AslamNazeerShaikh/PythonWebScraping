"""Tests for src.export — Pandas frames, filters, CSV/Excel snapshots."""
from __future__ import annotations

from src import export
from src.config import SETTINGS
from tests.conftest import make_job


def _seed(fresh_db):
    from src.db import upsert_jobs
    upsert_jobs([make_job("11111111", location="Pune", search_location="pune"),
                 make_job("22222222", location="Hyderabad",
                          search_location="hyderabad")])


def test_load_frame_columns_and_limit(fresh_db):
    _seed(fresh_db)
    df = export.load_frame()
    assert list(df.columns) == export.COLUMNS
    assert len(df) == 2
    assert len(export.load_frame(limit=1)) == 1


def test_load_frame_location_matches_either_column(fresh_db):
    _seed(fresh_db)
    assert len(export.load_frame(location="pune")) == 1
    assert len(export.load_frame(location="HYDERABAD")) == 1  # case-insensitive
    assert len(export.load_frame(location="chennai")) == 0


def _seed_search_locations(fresh_db):
    """Realistic API-collected mix: a Pune-only search hit vs a 3-city hit.

    ``location`` is blank on both — the search fast path never captures the
    job's own city, so ``search_location`` is the only city signal.
    """
    from src.db import upsert_jobs
    upsert_jobs([make_job("55555555", location="",
                          search_location="pune"),
                 make_job("66666666", location="",
                          search_location="pune,hyderabad,bengaluru")])


def test_load_frame_location_match_exact(fresh_db):
    _seed_search_locations(fresh_db)
    # default stays substring: the multi-city search passes "pune" too
    assert len(export.load_frame(location="pune")) == 2
    strict = export.load_frame(location="pune", location_match="exact")
    assert len(strict) == 1
    assert strict["job_id"].tolist() == ["55555555"]
    # exact stays case- and whitespace-insensitive, and still checks both cols
    assert len(export.load_frame(location=" PUNE ",
                                 location_match="exact")) == 1
    assert len(export.load_frame(location="pune", location_match="exact")) == \
        len(export.load_frame(location="pune", location_match="contains")) - 1
    assert len(export.load_frame(location="chennai",
                                 location_match="exact")) == 0
    # no needle: the mode never filters (back-compat)
    assert len(export.load_frame(location_match="exact")) == 2


def _seed_backdated(fresh_db):
    """Two rows: ``11111111`` seen now, ``22222222`` first seen 3 days ago.

    ``first_seen`` is written by SQLite's ``CURRENT_TIMESTAMP`` (UTC), so the
    backdate uses ``datetime('now','-3 day')`` to stay in the same clock.
    """
    from sqlalchemy import text

    _seed(fresh_db)
    with fresh_db.get_engine().begin() as conn:
        conn.execute(text("UPDATE jobs SET first_seen = "
                          "datetime('now','-3 day') "
                          "WHERE job_id = '22222222'"))


def test_load_frame_days_window(fresh_db):
    _seed_backdated(fresh_db)
    assert len(export.load_frame()) == 2  # no window: the whole DB
    fresh = export.load_frame(days=1)
    assert len(fresh) == 1  # only the <24h posting
    assert fresh["job_id"].tolist() == ["11111111"]
    assert len(export.load_frame(days=7)) == 2  # 3-day-old row is inside


def test_export_jobs_days_forwarded(fresh_db, tmp_path, monkeypatch):
    _seed_backdated(fresh_db)
    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    import pandas as pd

    assert len(pd.read_csv(export.export_jobs(fmt="csv"))) == 2
    assert len(pd.read_csv(export.export_jobs(fmt="csv", days=1))) == 1


def test_export_jobs_location_match_forwarded(fresh_db, tmp_path, monkeypatch):
    _seed_search_locations(fresh_db)
    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    import pandas as pd

    broad = pd.read_csv(export.export_jobs(fmt="csv", location="pune"))
    strict = pd.read_csv(export.export_jobs(fmt="csv", location="pune",
                                            location_match="exact"))
    assert len(broad) == 2 and len(strict) == 1
    assert strict["job_id"].astype(str).tolist() == ["55555555"]


def test_export_csv_default_path(fresh_db, tmp_path, monkeypatch):
    _seed(fresh_db)
    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    dest = export.export_jobs(fmt="csv")
    assert dest.suffix == ".csv" and dest.exists()
    import pandas as pd
    assert len(pd.read_csv(dest)) == 2


def test_export_excel_and_explicit_path(fresh_db, tmp_path, monkeypatch):
    _seed(fresh_db)
    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    dest = export.export_jobs(fmt="excel", location="pune")
    assert dest.suffix == ".xlsx"
    import pandas as pd
    assert len(pd.read_excel(dest)) == 1
    explicit = tmp_path / "custom.csv"
    assert export.export_jobs(fmt="csv", out_path=str(explicit)) == explicit
    assert explicit.exists()


def _seed_java(fresh_db):
    from src.db import upsert_jobs
    _seed(fresh_db)
    upsert_jobs([make_job("33333333", title="Java Developer",
                          skills=["Java", "Spring Boot"],
                          snippet="spring boot microservices",
                          search_location="pune"),
                 make_job("44444444", title="Sr java/.net Full Stack Developer",
                          skills=["Java", "C#"],
                          snippet="java plus dotnet team",
                          search_location="pune")])


def test_load_frame_excludes_pure_java_by_default(fresh_db):
    _seed_java(fresh_db)
    titles = set(export.load_frame()["title"])
    assert "Java Developer" not in titles  # pure-Java dropped
    assert "Sr java/.net Full Stack Developer" in titles  # anchor rescues it
    assert "Senior .NET Developer" in titles


def test_load_frame_include_java_keeps_everything(fresh_db):
    _seed_java(fresh_db)
    assert len(export.load_frame(exclude_java=False)) == 4


def test_load_frame_empty_db_with_filter(fresh_db):
    assert export.load_frame().empty  # no rows: filter is a no-op, still COLUMNS
    assert list(export.load_frame().columns) == export.COLUMNS


def test_export_jobs_respects_include_java(fresh_db, tmp_path, monkeypatch):
    _seed_java(fresh_db)
    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    import pandas as pd
    assert len(pd.read_csv(export.export_jobs(fmt="csv"))) == 3
    assert len(pd.read_csv(export.export_jobs(fmt="csv",
                                              exclude_java=False))) == 4
