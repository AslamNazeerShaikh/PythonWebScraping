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
