"""Tests for src.linkedin_email_scraper — URL builder, extraction, collect loop.

Offline only: FakePage/FakeContext drive every path (no live LinkedIn).
"""
from __future__ import annotations

import pytest

from src.linkedin_email_scraper import (
    CONTENT_EXTRACT_JS,
    _contacts_from_cards,
    _expand_show_more,
    _safe_goto,
    _wait_for_login,
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
        [dict(CARD, text="@ltm.com also apply@epam.com", author="A")],
    ]
    from src import config
    config.SETTINGS.email_target_min = 0
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


# -- login wall (root cause of the 0-email live run: authwall redirect) --------
def test_on_login_wall_detects_auth_redirect():
    from src.linkedin_email_scraper import _on_login_wall

    page = FakePage()
    page.url = ("https://www.linkedin.com/uas/login?session_redirect=%2Fsearch"
                "&skipRedirect=true")
    assert _on_login_wall(page) is True
    page.url = "https://www.linkedin.com/search/results/content/?keywords=x"
    assert _on_login_wall(page) is False


def test_run_collect_stops_when_signed_out_and_noninteractive(
        monkeypatch, fresh_db):
    """No TTY (background runs): EOF at the prompt → stop with guidance."""
    from src.linkedin_email_scraper import run_collect

    page = FakePage()
    page.url = ("https://www.linkedin.com/uas/login?session_redirect=%2Fsearch"
                "&skipRedirect=true")
    ctx = FakeContext(page)
    prompted: list[bool] = []

    def _eof(*a, **k):
        prompted.append(True)
        raise EOFError

    monkeypatch.setattr("builtins.input", _eof)
    out = run_collect(ctx, domains=["ltm.com"], max_scrolls=1)
    assert out == []
    assert prompted == [True]              # manual-login prompt WAS attempted
    assert len(page.goto_urls) == 1        # never searched while signed out


def test_run_collect_logs_in_manually_then_proceeds(monkeypatch, fresh_db):
    """User logs in at the prompt → re-goto lands on search → collects."""
    from src.linkedin_email_scraper import run_collect
    from src.models import EmailContact  # noqa: F401

    page = FakePage()
    page.url = "https://www.linkedin.com/uas/login?session_redirect=%2Fsearch"
    ctx = FakeContext(page)
    page.cards_queue = [[CARD]]
    from src import config
    config.SETTINGS.email_target_min = 0

    def _logged_in(*a, **k):               # ENTER pressed after real login
        page.url = "https://www.linkedin.com/feed/"
        return ""

    monkeypatch.setattr("builtins.input", _logged_in)
    out = run_collect(ctx, domains=["ltm.com"], max_scrolls=1)
    assert [c.email for c in out] == ["neha.pandey@ltm.com"]
    assert len(page.goto_urls) == 2        # initial + post-login re-goto


def test_run_collect_gives_up_when_login_never_completes(monkeypatch, fresh_db):
    """ENTER pressed but the wall never clears → STOP; never re-navigate.

    Regression for "page refreshes at login": the fix must NOT reload the
    sign-in page. After the prompt it waits passively for the URL to leave
    the wall; on timeout it bails, so the login page is left untouched for
    the human to finish.
    """
    from src.linkedin_email_scraper import run_collect

    page = FakePage()
    page.url = ("https://www.linkedin.com/uas/login?session_redirect=%2Fsearch"
                "&skipRedirect=true")
    ctx = FakeContext(page)
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")  # pressed ENTER
    monkeypatch.setattr("src.linkedin_email_scraper.LOGIN_GRACE_S", 0.06)
    monkeypatch.setattr("src.linkedin_email_scraper.LOGIN_POLL_S", 0.03)

    out = run_collect(ctx, domains=["tcs.com"], max_scrolls=1)
    assert out == []
    assert len(page.goto_urls) == 1        # initial only — NO post-login reload


def test_run_collect_stops_if_bounced_back_to_wall_after_login(monkeypatch, fresh_db):
    """Login clears the wall, then the target navigation lands back on it."""
    from src.linkedin_email_scraper import run_collect

    wall = ("https://www.linkedin.com/uas/login?session_redirect=%2Fsearch"
            "&skipRedirect=true")
    page = FakePage()
    page.url = wall
    # initial goto stays on the wall; post-login goto bounces back to it
    page.goto_set_url = [None, wall]
    ctx = FakeContext(page)

    def _signed_in(*a, **k):               # human completes login before ENTER
        page.url = "https://www.linkedin.com/feed/"
        return ""

    monkeypatch.setattr("builtins.input", _signed_in)
    out = run_collect(ctx, domains=["ltm.com"], max_scrolls=1)
    assert out == []
    assert len(page.goto_urls) == 2        # initial + post-login, then stop


# -- passive login wait (never reloads the sign-in page) ---------------------
def test_wait_for_login_true_when_already_signed_in():
    from src.linkedin_email_scraper import _wait_for_login

    page = FakePage()
    page.url = "https://www.linkedin.com/feed/"
    assert _wait_for_login(page, grace_s=5, poll_s=1) is True
    assert page.timeouts == []             # signed in → no waiting at all


def test_wait_for_login_waits_until_wall_clears():
    from src.linkedin_email_scraper import _wait_for_login

    class _FlipPage:
        """Wall that clears after the first passive poll (human logs in)."""
        url = "https://www.linkedin.com/uas/login?x=1"

        def __init__(self):
            self.waits = 0

        def wait_for_timeout(self, ms):
            self.waits += 1
            self.url = "https://www.linkedin.com/feed/"   # login completed

    fp = _FlipPage()
    assert _wait_for_login(fp, grace_s=30, poll_s=2) is True
    assert fp.waits == 1                   # waited once, then proceeded


def test_wait_for_login_gives_up_after_grace():
    from src.linkedin_email_scraper import _wait_for_login

    page = FakePage()
    page.url = "https://www.linkedin.com/uas/login?x=1"   # never clears
    assert _wait_for_login(page, grace_s=0.06, poll_s=0.03) is False


# -- coverage: all-time URL builder -------------------------------------------
def test_build_content_search_url_all_time():
    url = build_content_search_url("@tcs.com", date_facet=None)
    assert "datePosted" not in url
    url2 = build_content_search_url("@tcs.com", date_facet="")
    assert "datePosted" not in url2


# -- coverage: relevance gate drops unrelated posts -----------------------------
def test_contacts_from_cards_drops_unrelated_posts():
    card = {"text": "random post with spam@other.com", "author": "X"}
    out = _contacts_from_cards([card], domain="tcs.com", keyword="@tcs.com")
    assert out == []


# -- coverage: post_id taken from urn -----------------------------------------
def test_contacts_from_cards_uses_urn_as_post_id():
    card = {"text": "write to hr@wipro.com", "urn": "urn:li:activity:999",
            "author": "X", "posted": "1d", "url": "https://lnkd.in/y"}
    out = _contacts_from_cards([card], domain="wipro.com", keyword="@wipro.com")
    assert len(out) == 1
    assert out[0].post_id == "urn:li:activity:999"


# -- coverage: show-more expansion swallows errors ------------------------------
def test_expand_show_more_swallows_errors():
    class _BrokenPage:
        def evaluate(self, js):
            raise RuntimeError("boom")
    _expand_show_more(_BrokenPage())  # must not raise


# -- coverage: sparse results trigger the all-time fallback ---------------------
def test_run_collect_fallback_to_all_time(monkeypatch):
    from src import config
    config.SETTINGS.email_target_min = 5
    config.SETTINGS.email_fallback_scrolls = 1
    page = FakePage()
    ctx = FakeContext(page)
    page.cards_queue = [[CARD]]
    from src.linkedin_email_scraper import run_collect
    out = run_collect(ctx, domains=["ltm.com"], max_scrolls=1,
                      date_facet="past-month")
    assert len(page.goto_urls) == 2  # primary + fallback


# -- coverage: fallback aborted by a bot wall ---------------------------------
def test_run_collect_fallback_aborted_by_bot_wall(monkeypatch):
    from src import config
    from src.linkedin_email_scraper import run_collect
    config.SETTINGS.email_target_min = 5
    config.SETTINGS.email_fallback_scrolls = 1
    page = FakePage()
    ctx = FakeContext(page)
    page.cards_queue = [[CARD]]
    import src.linkedin_email_scraper as mod
    calls = {"n": 0}

    def fake_wall(p):
        calls["n"] += 1
        return calls["n"] >= 2

    monkeypatch.setattr(mod, "_check_bot_wall", fake_wall)
    monkeypatch.setattr(mod, "human_pause", lambda *a, **k: None)
    import src.naukri_scraper as nk
    monkeypatch.setattr(nk, "human_pause", lambda *a, **k: None)
    out = run_collect(ctx, domains=["ltm.com"], max_scrolls=1,
                      date_facet="past-month")
    assert len(page.goto_urls) == 2  # primary + fallback attempt
