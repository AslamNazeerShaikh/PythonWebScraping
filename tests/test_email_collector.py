"""Tests for src.linkedin_email_scraper — URL builder, extraction, collect loop.

Offline only: FakePage/FakeContext drive every path (no live LinkedIn).
"""
from __future__ import annotations

import pytest

from src.linkedin_email_scraper import (
    CONTENT_EXTRACT_JS,
    _contacts_from_cards,
    _safe_goto,
    build_content_search_url,
    extract_emails,
)
from tests.conftest import FakeContext, FakePage


@pytest.fixture(autouse=True)
def no_pauses(monkeypatch):
    """Neutralise politeness sleeps (they exist for live runs, not CI)."""
    import src.linkedin_email_scraper as mod
    import src.naukri_scraper as nk

    monkeypatch.setattr(mod, "human_pause", lambda *a, **k: None)
    monkeypatch.setattr(nk, "human_pause", lambda *a, **k: None)


# -- URL builder ---------------------------------------------------------------
def test_build_content_search_url_shape():
    url = build_content_search_url("@cognizant.com")
    assert url.startswith("https://www.linkedin.com/search/results/content/?")
    assert "keywords=%40cognizant.com" in url
    assert "datePosted=%5B%22past-month%22%5D" in url   # ["past-month"]
    assert 'sortBy=%22date_posted%22' in url            # newest first
    assert "origin=FACETED_SEARCH" in url


def test_build_content_search_url_rejects_unknown_facet():
    # LinkedIn SILENTLY IGNORES unknown facets — fail loudly instead.
    with pytest.raises(ValueError):
        build_content_search_url("@tcs.com", date_facet="past-year")


# -- email extraction ------------------------------------------------------------
def test_extract_emails_finds_dedupes_and_lowercases():
    text = ("Hiring! Contact NEHA.Pandey@LTM.com or neha.pandey@ltm.com "
            "or hr@tcs.com.")
    assert extract_emails(text) == ["neha.pandey@ltm.com", "hr@tcs.com"]


def test_extract_emails_ignores_filename_false_positives():
    assert extract_emails("see logo@2x.png and bg@1x.jpg icons") == []
    assert extract_emails("no emails here") == []


# -- card → contacts --------------------------------------------------------------
CARD = {
    "text": "We are hiring Cognizant! Mail your CV to neha.pandey@ltm.com today",
    "author": "Neha Pandey",
    "posted": "2d",
    "url": "https://www.linkedin.com/feed/update/urn:li:activity:123/",
}


def test_contacts_from_cards_maps_fields_and_snippet():
    out = _contacts_from_cards([CARD], domain="ltm.com", keyword="@ltm.com")
    assert len(out) == 1
    c = out[0]
    assert c.email == "neha.pandey@ltm.com"
    assert c.domain == "ltm.com" and c.keyword == "@ltm.com"
    assert c.author == "Neha Pandey" and c.posted == "2d"
    assert c.post_url.endswith("urn:li:activity:123/")
    assert "neha.pandey@ltm.com" in c.snippet and len(c.snippet) <= 300


def test_contacts_from_cards_skips_cards_without_email():
    assert _contacts_from_cards([{"text": "no address here", "author": "X"}],
                                domain="tcs.com", keyword="@tcs.com") == []


def test_contacts_from_cards_tolerates_missing_fields():
    out = _contacts_from_cards([{"text": "write to hr@wipro.com"}],
                               domain="wipro.com", keyword="@wipro.com")
    assert len(out) == 1
    assert out[0].author == "" and out[0].post_url == "" and out[0].posted == ""


def test_contacts_from_cards_snippet_window_is_bounded():
    text = "x" * 400 + " apply@epam.com " + "y" * 400
    c = _contacts_from_cards([{"text": text}], domain="epam.com",
                             keyword="@epam.com")[0]
    assert "apply@epam.com" in c.snippet
    assert len(c.snippet) <= 300


# -- navigation guard ---------------------------------------------------------
def test_safe_goto_retries_transient_timeout():
    page = FakePage()
    page.goto_plan = [TimeoutError("slow"), None]  # transient once, then OK
    _safe_goto(page, "https://www.linkedin.com/search/results/content/?x=1")
    assert len(page.goto_urls) == 2


def test_safe_goto_does_not_retry_non_transient():
    page = FakePage()
    page.goto_plan = [RuntimeError("403 forbidden")]
    with pytest.raises(RuntimeError):
        _safe_goto(page, "https://www.linkedin.com/")
    assert len(page.goto_urls) == 1  # never hammers a block page


# -- collect loop ---------------------------------------------------------------
def test_run_collect_happy_path_scrolls_and_dedupes():
    from src.linkedin_email_scraper import run_collect

    page = FakePage()
    ctx = FakeContext(page)
    # pass 1: two cards (same email twice); pass 2: one new email
    page.cards_queue = [
        [CARD, dict(CARD)],
        [dict(CARD, text="also apply@epam.com", author="A")],
    ]
    out = run_collect(ctx, domains=["ltm.com"], max_scrolls=2,
                      date_facet="past-month")
    emails = [c.email for c in out]
    assert emails == ["neha.pandey@ltm.com", "apply@epam.com"]  # deduped
    assert "%40ltm.com" in page.goto_urls[0]                    # @-keyword
    assert any(CONTENT_EXTRACT_JS in js for js in page.evals)
    assert ctx.closed is False                                  # caller closes


def test_run_collect_stops_on_bot_wall():
    from src.linkedin_email_scraper import run_collect

    page = FakePage()
    page.body_text = "Pardon the interruption — verify you are human"
    ctx = FakeContext(page)
    out = run_collect(ctx, domains=["tcs.com", "wipro.com"], max_scrolls=3)
    assert out == []                       # stopped before any extraction
    assert len(page.goto_urls) == 1        # second domain never attempted


def test_check_bot_wall_swallows_evaluate_errors():
    from src.linkedin_email_scraper import _check_bot_wall

    class _BrokenPage:
        def evaluate(self, js: str):
            raise RuntimeError("detached")

    assert _check_bot_wall(_BrokenPage()) is False  # sensing failed ≠ wall


def test_run_collect_uses_settings_defaults(monkeypatch):
    from src import config
    from src.linkedin_email_scraper import run_collect

    monkeypatch.setattr(config.SETTINGS, "email_domains", ["one.com"])
    monkeypatch.setattr(config.SETTINGS, "email_max_scrolls", 1)
    monkeypatch.setattr(config.SETTINGS, "email_date_facet", "past-week")
    page = FakePage()
    ctx = FakeContext(page)
    out = run_collect(ctx)                       # all defaults resolved here
    assert out == []
    assert "datePosted=%5B%22past-week%22%5D" in page.goto_urls[0]
