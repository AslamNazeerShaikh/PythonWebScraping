"""Tests for src.models — Pydantic validation gate + ORM converters."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models import Job, JobRow


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
