"""Tests for src.export — Pandas frames, filters, CSV/Excel snapshots."""
from __future__ import annotations

import pandas as pd

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
    job's own city, so ``search_location`` is the only city signal. Titles
    differ so the (title, company, location, experience) dedupe leaves both.
    """
    from src.db import upsert_jobs
    upsert_jobs([make_job("55555555", title="Pune Only .NET Developer",
                          location="", search_location="pune"),
                 make_job("66666666", title="Three City .NET Developer",
                          location="", search_location="pune,hyderabad,bengaluru")])


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


# -- lane job-quality gates (spec: docs/SPEC-lane-job-quality-gates.md) ---------
def _seed_quality_gates(fresh_db):
    """One row per gate outcome, all under the combined-lane search string."""
    from src.db import upsert_jobs

    common = dict(search_location="pune,hyderabad,bengaluru")
    upsert_jobs([
        make_job("71000001", title="AI Engineer", skills=["Python", "LLM"],
                 snippet="rag pipelines built with langchain", **common),
        make_job("71000002", title="Product Owner", skills=["Agile", "Jira"],
                 snippet="roadmap prioritisation", **common),
        make_job("71000003", title="React Developer",
                 skills=["React", "JavaScript", "HTML", "CSS"],
                 snippet="responsive UIs", **common),
        make_job("71000004", title="Gen AI Engineer", skills=["LangChain"],
                 snippet="llm integrations",
                 apply_url="https://careers.acme.example/jobs/123", **common),
    ])


def test_load_frame_drops_unwanted_rows_by_default(fresh_db):
    _seed_quality_gates(fresh_db)
    titles = set(export.load_frame()["title"])
    assert titles == {"AI Engineer"}  # unrelated + frontend + external-apply gone


def test_load_frame_exclude_unwanted_false_keeps_raw_pool(fresh_db):
    _seed_quality_gates(fresh_db)
    titles = set(export.load_frame(exclude_unwanted=False)["title"])
    assert titles == {"AI Engineer", "Product Owner", "React Developer",
                      "Gen AI Engineer"}  # java gate stays on, only new gates opt out


def test_load_frame_external_apply_dropped_only_under_gates(fresh_db):
    _seed_quality_gates(fresh_db)
    kept = set(export.load_frame(exclude_unwanted=False)["title"])
    assert "Gen AI Engineer" not in set(export.load_frame()["title"])
    assert "Gen AI Engineer" in kept


def test_load_frame_dedupes_same_title_company_reposts(fresh_db):
    from src.db import upsert_jobs

    upsert_jobs([make_job("72000001", title="Sr. SW Engineer", company="Visa",
                          skills=["Python"], snippet="agentic automation"),
                 make_job("72000002", title="  sr. sw   engineer ",
                          company="VISA", skills=["Python"],
                          snippet="agentic automation")])
    df = export.load_frame()
    assert len(df) == 1  # near-identical repost collapses (freshest kept)


def test_load_frame_dedupe_keeps_distinct_openings(fresh_db):
    from src.db import upsert_jobs

    upsert_jobs([make_job("73000001", title="Sr. SW Engineer", company="Visa",
                          experience="1-3 Yrs"),
                 make_job("73000002", title="Sr. SW Engineer", company="Visa",
                          experience="5-8 Yrs")])
    assert len(export.load_frame()) == 2  # same title, different band = 2 jobs


# ---------------------------------------------------------------------------
# Email collector export (Task 5)
# ---------------------------------------------------------------------------
def _seed_emails():
    from src.db import upsert_emails
    from src.models import EmailContact

    upsert_emails([
        EmailContact(email="b@tcs.com", domain="tcs.com", keyword="@tcs.com",
                     author="B", snippet="mail b@tcs.com"),
        EmailContact(email="a@tcs.com", domain="tcs.com", keyword="@tcs.com"),
        EmailContact(email="c@wipro.com", domain="wipro.com",
                     keyword="@wipro.com", post_url="https://lnkd.in/x"),
    ])


def test_load_email_frame_columns_and_sort(fresh_db):
    _seed_emails()
    df = export.load_email_frame()
    assert list(df.columns) == export.EMAIL_COLUMNS
    # sorted domain -> email
    assert list(df["email"]) == ["a@tcs.com", "b@tcs.com", "c@wipro.com"]


def test_load_email_frame_empty_db(fresh_db):
    df = export.load_email_frame()
    assert df.empty
    assert list(df.columns) == export.EMAIL_COLUMNS


def test_export_emails_explicit_paths_both_formats(fresh_db, tmp_path):
    _seed_emails()
    xlsx = export.export_emails(fmt="excel", out_path=tmp_path / "e.xlsx")
    csvf = export.export_emails(fmt="csv", out_path=tmp_path / "e.csv")
    assert xlsx.exists() and xlsx.suffix == ".xlsx"
    assert csvf.exists() and csvf.suffix == ".csv"
    assert len(pd.read_excel(xlsx)) == 3


def test_export_emails_default_path_is_timestamped(fresh_db, tmp_path,
                                                   monkeypatch):
    from src.config import SETTINGS as S
    monkeypatch.setattr(S, "output_dir", tmp_path)
    _seed_emails()
    p = export.export_emails(fmt="excel")
    assert p.name.startswith("linkedin_emails_") and p.suffix == ".xlsx"
    assert p.parent == tmp_path
    pc = export.export_emails(fmt="csv")
    assert pc.suffix == ".csv"


# -- email export: domain purity, latest-post dedupe, sorting ----------------
def _seed_mixed_emails():
    from src.db import upsert_emails
    from src.models import EmailContact

    contacts = [
        EmailContact(email="zeta@tcs.com", domain="tcs.com", posted="2d",
                     post_id="tcs-new", author="New"),
        EmailContact(email="zeta@tcs.com", domain="tcs.com", posted="1mo",
                     post_id="tcs-old", author="Old"),
        EmailContact(email="zeta@tcs.com", domain="tcs.com", posted="5d",
                     post_id="tcs-mid", author="Mid"),
        EmailContact(email="alpha@tcs.com", domain="tcs.com", posted="3h",
                     post_id="tcs-alpha"),
        EmailContact(email="beta@wipro.com", domain="wipro.com", posted="1w",
                     post_id="wipro-beta"),
        # Contamination: searched tcs.com but the post also had a Gmail.
        EmailContact(email="outsider@gmail.com", domain="tcs.com",
                     posted="1h", post_id="junk"),
    ]
    upsert_emails(contacts)


def test_email_export_drops_other_domains_and_keeps_latest_post(fresh_db):
    _seed_mixed_emails()
    df = export.load_email_frame()
    assert list(df["email"]) == ["alpha@tcs.com", "zeta@tcs.com",
                                 "beta@wipro.com"]
    assert "outsider@gmail.com" not in set(df["email"])
    assert list(df["domain"]) == ["tcs.com", "tcs.com", "wipro.com"]
    zeta = df[df["email"] == "zeta@tcs.com"].iloc[0]
    assert zeta["post_id"] == "tcs-new"       # 2d beats 5d and 1mo
    assert zeta["author"] == "New"


def test_email_export_returns_columns_when_all_rows_are_mismatched(fresh_db):
    from src.db import upsert_emails
    from src.models import EmailContact

    upsert_emails([EmailContact(email="x@gmail.com", domain="tcs.com",
                                posted="1h", post_id="bad")])
    df = export.load_email_frame()
    assert df.empty
    assert list(df.columns) == export.EMAIL_COLUMNS


def test_email_export_domain_falls_back_to_keyword(fresh_db):
    from src.db import upsert_emails
    from src.models import EmailContact

    upsert_emails([EmailContact(email="a@tcs.com", domain="",
                                keyword="@tcs.com", posted="1d",
                                post_id="p")])
    df = export.load_email_frame()
    assert list(df["email"]) == ["a@tcs.com"]
    assert list(df["domain"]) == ["tcs.com"]


def test_email_export_ignores_rows_without_any_domain(fresh_db):
    from src.db import upsert_emails
    from src.models import EmailContact

    upsert_emails([EmailContact(email="a@tcs.com", domain="", keyword="",
                                posted="1d", post_id="p")])
    assert export.load_email_frame().empty


def test_posted_timestamp_relative_and_absolute_labels():
    ref = pd.Timestamp("2026-10-25 12:00:00")
    assert export._posted_timestamp("19h", ref) == ref - pd.Timedelta(hours=19)
    assert export._posted_timestamp("2d", ref) == ref - pd.Timedelta(days=2)
    assert export._posted_timestamp("1w", ref) == ref - pd.Timedelta(days=7)
    assert export._posted_timestamp("3mo", ref) == ref - pd.Timedelta(days=90)
    assert export._posted_timestamp("1yr", ref) == ref - pd.Timedelta(days=365)
    assert export._posted_timestamp("45m", ref) == ref - pd.Timedelta(minutes=45)
    assert export._posted_timestamp("30s", ref) == ref - pd.Timedelta(seconds=30)
    assert export._posted_timestamp("just now", ref) == ref
    assert export._posted_timestamp("Oct 13", ref) == pd.Timestamp("2026-10-13")
    assert export._posted_timestamp("Dec 31", pd.Timestamp("2026-01-05")) == \
        pd.Timestamp("2025-12-31")
    assert export._posted_timestamp("Oct 13, 2025", ref) == \
        pd.Timestamp("2025-10-13")
    assert export._posted_timestamp("2026-10-01", ref) == \
        pd.Timestamp("2026-10-01")


def test_posted_timestamp_fallbacks_never_raise():
    ref = pd.Timestamp("2026-10-25 12:00:00")
    assert pd.isna(export._posted_timestamp("", ref))
    assert pd.isna(export._posted_timestamp("yesterday-ish", ref))
    assert pd.isna(export._posted_timestamp("Feb 30", ref))
    assert pd.isna(export._posted_timestamp("Feb 29",
                                            pd.Timestamp("2026-01-01")))
    assert export._posted_timestamp("Dec 31", pd.Timestamp("2025-01-01")) == \
        pd.Timestamp("2024-12-31")


def test_posted_timestamp_handles_missing_reference_and_timezone():
    now = export._posted_timestamp("2d", None)
    assert not pd.isna(now)
    aware = pd.Timestamp("2026-10-25T12:00:00+00:00")
    assert export._posted_timestamp("1d", aware) == \
        pd.Timestamp("2026-10-24 12:00:00")
    assert export._posted_timestamp("2026-10-01T00:00:00+00:00", aware) == \
        pd.Timestamp("2026-10-01 00:00:00")


def test_email_domain_and_naive_timestamp_helpers():
    assert export._email_domain("A@TCS.com") == "tcs.com"
    assert export._email_domain("malformed") == "malformed"
    assert export._email_domain("") == ""
    assert export._naive_timestamp(
        pd.Timestamp("2026-10-25T12:00:00+05:30")) == \
        pd.Timestamp("2026-10-25 12:00:00")


def test_posted_timestamp_invalid_month_and_leap_year_fallback():
    ref = pd.Timestamp("2026-10-25 12:00:00")
    assert pd.isna(export._posted_timestamp("Foo 13", ref))
    assert pd.isna(export._posted_timestamp("Feb 29, 2024",
                                            pd.Timestamp("2023-01-01")))


def test_latest_email_frame_empty_input_returns_empty():
    empty = pd.DataFrame(columns=export.EMAIL_COLUMNS)
    out = export._latest_email_frame(empty)
    assert out.empty
    assert list(out.columns) == export.EMAIL_COLUMNS


def test_hyperlink_titles_skips_rows_without_apply_url(fresh_db, tmp_path):
    from src.db import upsert_jobs
    upsert_jobs([make_job("11111111"),
                 make_job("22222222", title="Data Engineer",
                          apply_url="")])
    dest = export.export_jobs(fmt="excel", out_path=tmp_path / "jobs.xlsx")
    assert dest.exists()


def test_hyperlink_titles_directly_skips_empty_target(tmp_path):
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["title", "apply_url"])
    ws.append(["No link", ""])
    ws.append(["Has link", "https://example.com/job"])
    path = tmp_path / "direct.xlsx"
    wb.save(path)
    export._hyperlink_titles(path)
    assert path.exists()


def test_posted_timestamp_rejects_non_iso_numbers_and_invalid_iso():
    ref = pd.Timestamp("2026-10-25 12:00:00")
    assert pd.isna(export._posted_timestamp("5", ref))
    assert pd.isna(export._posted_timestamp("2026-13-40", ref))


def test_email_export_limit_applies_after_dedupe(fresh_db):
    _seed_mixed_emails()
    df = export.load_email_frame(limit=2)
    assert list(df["email"]) == ["alpha@tcs.com", "zeta@tcs.com"]
