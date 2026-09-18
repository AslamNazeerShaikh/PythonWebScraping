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
