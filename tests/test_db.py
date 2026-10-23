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


# ---------------------------------------------------------------------------
# Email collector — contact_emails upserts (Task 2)
# ---------------------------------------------------------------------------
from src.models import EmailContact  # noqa: E402


def _contact(**over) -> EmailContact:
    base = dict(email="neha.pandey@ltm.com", domain="ltm.com",
                keyword="@ltm.com", author="Neha Pandey", posted="2d",
                post_url="https://www.linkedin.com/feed/update/urn:li:activity:1/",
                snippet="Hiring! write to neha.pandey@ltm.com")
    base.update(over)
    return EmailContact(**base)


def test_upsert_emails_empty_short_circuits(fresh_db):
    assert db.upsert_emails([]) == (0, 0)
    assert db.count_emails() == 0


def test_upsert_emails_inserts_and_counts(fresh_db):
    new, total = db.upsert_emails([_contact(), _contact(email="hr@tcs.com")])
    assert (new, total) == (2, 2)
    assert db.count_emails() == 2


def test_upsert_emails_resighting_no_duplicate_bumps_last_seen(fresh_db):
    db.upsert_emails([_contact()])
    new, total = db.upsert_emails([_contact(post_url="")])  # same email again
    assert (new, total) == (0, 1)
    assert db.count_emails() == 1
    from src.models import EmailRow
    with db.get_session() as s:
        row = s.get(EmailRow, "neha.pandey@ltm.com")
    assert row.last_seen is not None


def test_upsert_emails_backfills_empty_evidence(fresh_db):
    db.upsert_emails([_contact(post_url="", author="")])  # first sighting: thin
    # richer evidence on re-sighting
    db.upsert_emails([_contact(author="Neha P.", post_url="https://lnkd.in/x")])
    from src.models import EmailRow
    with db.get_session() as s:
        row = s.get(EmailRow, "neha.pandey@ltm.com")
    assert row.author == "Neha P."
    assert row.post_url == "https://lnkd.in/x"


def test_upsert_emails_keeps_existing_evidence_when_new_is_empty(fresh_db):
    db.upsert_emails([_contact()])
    db.upsert_emails([_contact(post_url="", author="", snippet="")])
    from src.models import EmailRow
    with db.get_session() as s:
        row = s.get(EmailRow, "neha.pandey@ltm.com")
    assert row.author == "Neha Pandey"          # not clobbered by empties
    assert row.post_url.endswith("urn:li:activity:1/")


def test_upsert_emails_domain_tag_newest_wins(fresh_db):
    db.upsert_emails([_contact()])
    db.upsert_emails([_contact(domain="cognizant.com", keyword="@cognizant.com")])
    from src.models import EmailRow
    with db.get_session() as s:
        row = s.get(EmailRow, "neha.pandey@ltm.com")
    assert row.domain == "cognizant.com"        # newest search's tag wins
    assert row.keyword == "@cognizant.com"


def test_upsert_emails_resighting_without_tag_keeps_old_tag(fresh_db):
    db.upsert_emails([_contact(domain="ltm.com", keyword="@ltm.com")])
    db.upsert_emails([_contact(domain="", keyword="")])  # tag-less re-sighting
    from src.models import EmailRow
    with db.get_session() as s:
        row = s.get(EmailRow, "neha.pandey@ltm.com")
    assert row.domain == "ltm.com" and row.keyword == "@ltm.com"
