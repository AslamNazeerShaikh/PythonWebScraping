"""Tests for src.models — Pydantic validation gate + ORM converters."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models import EmailContact, EmailRow, Job, JobRow


def test_job_url_canonicalisation():
    j = Job(job_id="12345678", title="Senior .NET Developer",
            url="https://www.naukri.com/job-listings-a-12345678?src=srp&x=1",
            apply_url="  https://company.com/apply?ref=1  ")
    assert j.url == "https://www.naukri.com/job-listings-a-12345678"
    assert j.apply_url == "https://company.com/apply"


def test_job_title_squeezed():
    j = Job(job_id="12345678", title="  Senior\n  .NET   Developer  ",
            company="  Acme\nCorp ")
    assert j.title == "Senior .NET Developer"
    assert j.company == "Acme Corp"


def test_job_rejects_short_title_and_id():
    with pytest.raises(ValidationError):
        Job(job_id="12345678", title="AB")  # title min_length=4
    with pytest.raises(ValidationError):
        Job(job_id="12", title="Valid Title Here")  # job_id min_length=3


def test_skill_text_joins():
    j = Job(job_id="12345678", title="Senior .NET Developer",
            skills=["C#", "ASP.NET Core"])
    assert j.skill_text() == "C#, ASP.NET Core"
    assert Job(job_id="12345678", title="Senior .NET Developer").skill_text() == ""


def test_jobrow_round_trip():
    j = Job(job_id="12345678", title="Senior .NET Developer", company="Acme",
            location="Pune", search_location="pune", skills=["C#", "SQL"],
            url="https://www.naukri.com/job-listings-a-12345678",
            apply_url="https://www.naukri.com/job-listings-a-12345678")
    row = JobRow.from_job(j)
    assert row.job_id == "12345678"
    assert row.skills == "C#, SQL"
    assert row.apply_url == j.url  # empty apply_url falls back to url
    back = row.to_job()
    assert back == j


def test_jobrow_from_job_empty_apply_falls_back_to_url():
    j = Job(job_id="12345678", title="Senior .NET Developer",
            url="https://www.naukri.com/job-listings-a-12345678", apply_url="")
    assert JobRow.from_job(j).apply_url == j.url


def test_jobrow_to_job_empty_skills():
    row = JobRow.from_job(Job(job_id="12345678", title="Senior .NET Developer"))
    row.skills = ""
    assert row.to_job().skills == []


# ---------------------------------------------------------------------------
# EmailContact / EmailRow — LinkedIn email collector contract (Task 1)
# ---------------------------------------------------------------------------
def test_email_contact_normalises_email_and_snippet():
    c = EmailContact(
        email="  Neha.Pandey@LTM.com ",
        domain="ltm.com",
        snippet="  We are\nhiring — write to me at  neha.pandey@ltm.com  ",
    )
    assert c.email == "neha.pandey@ltm.com"      # lowercased + stripped
    assert c.snippet == "We are hiring — write to me at neha.pandey@ltm.com"


def test_email_contact_rejects_malformed_email():
    with pytest.raises(ValidationError):
        EmailContact(email="not-an-email", domain="ltm.com")
    with pytest.raises(ValidationError):
        EmailContact(email="name@localhost", domain="ltm.com")  # no TLD


def test_email_contact_snippet_capped():
    c = EmailContact(email="a.b@tcs.com", domain="tcs.com", snippet="x" * 500)
    assert len(c.snippet) <= 300


def test_email_contact_defaults_are_empty():
    c = EmailContact(email="hr@wipro.com")
    assert c.domain == "" and c.post_url == "" and c.author == ""
    assert c.posted == "" and c.keyword == ""
    assert c.first_seen is None and c.last_seen is None


def test_emailrow_round_trip():
    c = EmailContact(
        email="recruiter@infosys.com", domain="infosys.com",
        post_url="https://www.linkedin.com/feed/update/urn:li:activity:1/",
        author="Jane Doe", posted="2d", keyword="@infosys.com",
        snippet="apply at recruiter@infosys.com",
    )
    row = EmailRow.from_contact(c)
    assert row.email == "recruiter@infosys.com"
    assert row.domain == "infosys.com"
    back = row.to_contact()
    assert back == c
