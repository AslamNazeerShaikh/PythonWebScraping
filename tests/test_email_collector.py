"""Tests for src.linkedin_email_scraper — URL builder, extraction, collect loop.

Offline only: FakePage/FakeContext drive every path (no live LinkedIn).
"""
from __future__ import annotations

import pytest

import src.linkedin_email_scraper as mod
from src.linkedin_email_scraper import (
    CONTENT_EXTRACT_JS,
    _apply_content_filters,
    _body_text,
    _check_bot_wall,
    _click_filter_button,
    _collect_view,
    _contacts_from_cards,
    _count_posts,
    _expand_show_more,
    _extract_fresh,
    _on_login_wall,
    _open_feed,
    _open_posts_view,
    _prompt_manual_login,
    _safe_goto,
    _scroll_to_bottom,
    _select_filter_radio,
    _show_filter_results,
    _submit_search,
    _wait_for_login,
    _wait_for_results,
    _wheel_feed,
    build_all_search_url,
    build_content_search_url,
    extract_emails,
    run_collect,
)
from src.models import EmailContact
from tests.conftest import FakeContext, FakeMouse, FakePage


@pytest.fixture(autouse=True)
def no_pauses(monkeypatch):
    """Neutralise politeness sleeps (they exist for live runs, not CI)."""
    import src.naukri_scraper as nk

    monkeypatch.setattr(mod, "human_pause", lambda *a, **k: None)
    monkeypatch.setattr(nk, "human_pause", lambda *a, **k: None)


class _BrokenPage:
    """Page whose evaluate() always raises (sensing failures must be safe)."""

    url = "https://www.linkedin.com/feed/"

    def evaluate(self, js: str):
        raise RuntimeError("detached")

    def wait_for_timeout(self, ms: int) -> None:  # pragma: no cover - no-op
        pass


# -- URL builders ---------------------------------------------------------------
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


def test_build_content_search_url_all_time():
    url = build_content_search_url("@tcs.com", date_facet=None)
    assert "datePosted" not in url
    url2 = build_content_search_url("@tcs.com", date_facet="")
    assert "datePosted" not in url2


def test_build_all_search_url_shape():
    url = build_all_search_url("@epam.com")
    assert url.startswith("https://www.linkedin.com/search/results/all/?")
    assert "keywords=%40epam.com" in url
    assert "origin=TYPEAHEAD_HISTORY" in url


# -- email extraction ------------------------------------------------------------
def test_extract_emails_finds_dedupes_and_lowercases():
    text = ("Hiring! Contact NEHA.Pandey@LTM.com or neha.pandey@ltm.com "
            "or hr@tcs.com.")
    assert extract_emails(text) == ["neha.pandey@ltm.com", "hr@tcs.com"]


def test_extract_emails_ignores_filename_false_positives():
    assert extract_emails("see logo@2x.png and bg@1x.jpg icons") == []
    assert extract_emails("no emails here") == []
    assert extract_emails("") == []


# -- card → contacts --------------------------------------------------------------
CARD = {
    "text": "We are hiring Cognizant! Mail your CV to neha.pandey@ltm.com today",
    "author": "Neha Pandey",
    "posted": "2d",
    "url": "https://www.linkedin.com/feed/update/urn:li:activity:123/",
    "post_id": "HDxQP1-hash",
}


def test_contacts_from_cards_maps_fields_and_snippet():
    out = _contacts_from_cards([CARD], domain="ltm.com", keyword="@ltm.com")
    assert len(out) == 1
    c = out[0]
    assert c.email == "neha.pandey@ltm.com"
    assert c.domain == "ltm.com" and c.keyword == "@ltm.com"
    assert c.author == "Neha Pandey" and c.posted == "2d"
    assert c.post_id == "HDxQP1-hash"
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
    assert out[0].post_id.startswith("||")


def test_contacts_from_cards_snippet_window_is_bounded():
    text = "x" * 400 + " apply@epam.com " + "y" * 400
    c = _contacts_from_cards([{"text": text}], domain="epam.com",
                             keyword="@epam.com")[0]
    assert "apply@epam.com" in c.snippet
    assert len(c.snippet) <= 300


def test_contacts_from_cards_drops_unrelated_posts():
    card = {"text": "random post with spam@other.com", "author": "X"}
    out = _contacts_from_cards([card], domain="tcs.com", keyword="@tcs.com")
    assert out == []


def test_contacts_from_cards_keeps_target_domain_even_without_keyword():
    card = {"text": "reach me at recruiter@tcs.com", "author": "X"}
    out = _contacts_from_cards([card], domain="tcs.com", keyword="@tcs.com")
    assert [c.email for c in out] == ["recruiter@tcs.com"]


def test_contacts_from_cards_uses_urn_then_url_as_post_id():
    card = {"text": "write to hr@wipro.com", "urn": "urn:li:activity:999",
            "author": "X", "posted": "1d", "url": "https://lnkd.in/y"}
    out = _contacts_from_cards([card], domain="wipro.com", keyword="@wipro.com")
    assert out[0].post_id == "urn:li:activity:999"
    card.pop("urn")
    out = _contacts_from_cards([card], domain="wipro.com", keyword="@wipro.com")
    assert out[0].post_id == "https://lnkd.in/y"


def test_contacts_from_cards_emits_one_contact_per_email():
    card = {"text": "@ltm.com: a@ltm.com and b@ltm.com", "post_id": "x"}
    out = _contacts_from_cards([card], domain="ltm.com", keyword="@ltm.com")
    assert [c.email for c in out] == ["a@ltm.com", "b@ltm.com"]


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


# -- sensing -------------------------------------------------------------------
def test_body_text_returns_visible_text_and_swallows_errors():
    page = FakePage()
    page.body_text = "hello"
    assert _body_text(page) == "hello"
    assert _body_text(_BrokenPage()) == ""


def test_check_bot_wall_detects_captcha_and_search_pause():
    page = FakePage()
    page.body_text = "Pardon the interruption — verify you are human"
    assert _check_bot_wall(page) is True
    page.body_text = ("Our systems have detected unusual search traffic. "
                      "Search activity on your account has been paused.")
    assert _check_bot_wall(page) is True
    page.body_text = "normal results"
    assert _check_bot_wall(page) is False
    assert _check_bot_wall(_BrokenPage()) is False


def test_expand_show_more_swallows_errors():
    _expand_show_more(_BrokenPage())  # must not raise
    page = FakePage()
    _expand_show_more(page)
    assert any("expandable-text-button" in js for js in page.evals)


# -- login wall (root cause of the 0-email live run: authwall redirect) --------
def test_on_login_wall_detects_auth_redirect():
    page = FakePage()
    page.url = ("https://www.linkedin.com/uas/login?session_redirect=%2Fsearch"
                "&skipRedirect=true")
    assert _on_login_wall(page) is True
    page.url = "https://www.linkedin.com/search/results/content/?keywords=x"
    assert _on_login_wall(page) is False


def test_prompt_manual_login_enter_and_eof(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")
    assert _prompt_manual_login() is True

    def _eof(*a, **k):
        raise EOFError

    monkeypatch.setattr("builtins.input", _eof)
    assert _prompt_manual_login() is False


def test_wait_for_login_true_when_already_signed_in():
    page = FakePage()
    page.url = "https://www.linkedin.com/feed/"
    assert _wait_for_login(page, grace_s=5, poll_s=1) is True
    assert page.timeouts == []             # signed in → no waiting at all


def test_wait_for_login_waits_until_wall_clears():
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
    page = FakePage()
    page.url = "https://www.linkedin.com/uas/login?x=1"   # never clears
    assert _wait_for_login(page, grace_s=0.06, poll_s=0.03) is False


def test_open_feed_handles_non_transient_navigation_error():
    page = FakePage()
    page.url = "https://www.linkedin.com/feed/"
    page.goto_plan = [RuntimeError("boom")]
    assert _open_feed(page) is True
    assert len(page.goto_urls) == 1


def test_open_feed_stops_when_signed_out_and_noninteractive(monkeypatch):
    page = FakePage()
    page.url = "https://www.linkedin.com/uas/login?session_redirect=%2Fsearch"
    monkeypatch.setattr("builtins.input", lambda *a, **k: (_ for _ in ()).throw(EOFError))
    assert _open_feed(page) is False
    assert len(page.goto_urls) == 1


def test_open_feed_stops_when_login_never_completes(monkeypatch):
    page = FakePage()
    page.url = "https://www.linkedin.com/uas/login?session_redirect=%2Fsearch"
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")
    monkeypatch.setattr(mod, "LOGIN_GRACE_S", 0.06)
    monkeypatch.setattr(mod, "LOGIN_POLL_S", 0.03)
    assert _open_feed(page) is False
    assert len(page.goto_urls) == 1        # initial only — NO post-login reload


def test_open_feed_logs_in_then_tolerates_reopen_error(monkeypatch):
    page = FakePage()
    page.url = "https://www.linkedin.com/uas/login?session_redirect=%2Fsearch"
    page.goto_plan = [None, RuntimeError("reopen failed")]
    # First probe sees the wall; after login the URL is clean.
    monkeypatch.setattr(mod, "_on_login_wall", _wall_then_clear())
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")
    assert _open_feed(page) is True
    assert len(page.goto_urls) == 2


def test_open_feed_stops_if_bounced_back_to_wall_after_login(monkeypatch):
    page = FakePage()
    page.url = "https://www.linkedin.com/uas/login?session_redirect=%2Fsearch"
    monkeypatch.setattr(mod, "_on_login_wall", lambda _p: True)
    monkeypatch.setattr(mod, "_wait_for_login", lambda _p: True)
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")
    assert _open_feed(page) is False
    assert len(page.goto_urls) == 2


def _wall_then_clear():
    """True on the first probe, False for every later probe."""
    calls = {"n": 0}

    def _probe(_page):
        calls["n"] += 1
        return calls["n"] == 1

    return _probe


def _sequence(*values):
    """Return a callable yielding ``values`` on successive calls."""
    it = iter(values)

    def _next(*_a, **_k):
        return next(it)

    return _next


# -- search box ----------------------------------------------------------------
def test_submit_search_types_in_page_and_waits_for_results():
    page = FakePage()
    page.url = ("https://www.linkedin.com/search/results/all/"
                "?keywords=%40ltm.com&origin=GLOBAL_SEARCH_HEADER")
    page.body_text = "results for @ltm.com"
    page.js_returns["/*results-ready*/"] = True
    assert _submit_search(page, "@ltm.com") is True
    assert page.locator_fills == [('input[placeholder="Search"]', "")]
    assert page.locator_types[-1][1] == "@ltm.com"
    assert page.locator_presses[-1][-1] == "Enter"


def test_submit_search_returns_false_when_locator_fails():
    class _NoLocator(FakePage):
        def locator(self, selector):  # type: ignore[override]
            raise RuntimeError("detached")

    assert _submit_search(_NoLocator(), "@tcs.com") is False


def test_wait_for_results_times_out_with_warning():
    page = FakePage()
    page.body_text = "nothing useful"
    assert _wait_for_results(page, "@tcs.com") is False
    assert len(page.timeouts) >= 1


def test_wait_for_results_accepts_no_results_page():
    page = FakePage()
    page.url = ("https://www.linkedin.com/search/results/all/"
                "?keywords=%40tcs.com&origin=GLOBAL_SEARCH_HEADER")
    page.body_text = "No results found for @tcs.com"
    page.js_returns["/*results-ready*/"] = True
    assert _wait_for_results(page, "@tcs.com") is True


def test_wait_for_results_uses_the_landed_keyword_url():
    page = FakePage()
    page.url = ("https://www.linkedin.com/search/results/all/"
                "?keywords=%40ltm.com&origin=GLOBAL_SEARCH_HEADER")
    page.body_text = "posts mentioning @ltm.com"
    page.js_returns["/*results-ready*/"] = True
    assert _wait_for_results(page, "@ltm.com") is True


def test_results_ui_ready_true_false_and_error():
    page = FakePage()
    page.js_returns["/*results-ready*/"] = True
    assert mod._results_ui_ready(page) is True
    page.js_returns["/*results-ready*/"] = False
    assert mod._results_ui_ready(page) is False
    assert mod._results_ui_ready(_BrokenPage()) is False


def test_wait_for_results_swallows_url_read_errors():
    class _UrlBroken(FakePage):
        @property
        def url(self):  # type: ignore[override]
            raise RuntimeError("detached")

        @url.setter
        def url(self, value):  # pragma: no cover - setter not used
            pass

    page = _UrlBroken()
    page.body_text = "nothing useful"
    assert _wait_for_results(page, "@tcs.com") is False


# -- native Posts tab + filters -------------------------------------------------
def test_open_posts_view_clicks_tab():
    page = FakePage()
    page.js_returns["/*open-posts*/"] = True
    assert _open_posts_view(page) is True
    assert any("/*open-posts*/" in js for js in page.evals)


def test_open_posts_view_returns_false_without_tab():
    page = FakePage()
    page.js_returns["/*open-posts*/"] = False
    assert _open_posts_view(page) is False
    assert _open_posts_view(_BrokenPage()) is False


def test_open_posts_view_tolerates_selector_timeout():
    page = FakePage()
    page.js_returns["/*open-posts*/"] = True
    page.selector_fail = True
    assert _open_posts_view(page) is True


def test_click_filter_button_branches():
    page = FakePage()
    page.js_returns["/*click-filter*/"] = True
    assert _click_filter_button(page, "Sort by") is True
    page.js_returns["/*click-filter*/"] = False
    assert _click_filter_button(page, "Sort by") is False
    assert _click_filter_button(_BrokenPage(), "Sort by") is False


def test_select_filter_radio_branches():
    page = FakePage()
    page.js_returns["/*select-radio*/"] = True
    assert _select_filter_radio(page, "Latest") is True
    page.js_returns["/*select-radio*/"] = False
    assert _select_filter_radio(page, "Latest") is False
    assert _select_filter_radio(_BrokenPage(), "Latest") is False


def test_show_filter_results_branches():
    page = FakePage()
    page.js_returns["/*show-results*/"] = True
    assert _show_filter_results(page) is True
    page.js_returns["/*show-results*/"] = False
    assert _show_filter_results(page) is False
    assert _show_filter_results(_BrokenPage()) is False


def test_apply_content_filters_happy_path_applies_sort_and_date():
    page = FakePage()
    page.js_returns.update({
        "/*click-filter*/": True,
        "/*select-radio*/": True,
        "/*show-results*/": True,
    })
    assert _apply_content_filters(page, "past-month") is True
    assert sum("/*click-filter*/" in js for js in page.evals) == 2
    assert sum("/*select-radio*/" in js for js in page.evals) == 2
    assert sum("/*show-results*/" in js for js in page.evals) == 2


def test_apply_content_filters_without_date():
    page = FakePage()
    page.js_returns.update({
        "/*click-filter*/": True,
        "/*select-radio*/": True,
        "/*show-results*/": True,
    })
    assert _apply_content_filters(page, None) is True
    assert sum("/*click-filter*/" in js for js in page.evals) == 1


def test_apply_content_filters_reports_missing_controls():
    page = FakePage()
    page.js_returns.update({
        "/*click-filter*/": False,
        "/*select-radio*/": False,
        "/*show-results*/": False,
    })
    assert _apply_content_filters(page, "past-month") is False


def test_apply_content_filters_radio_and_show_results_failures():
    page = FakePage()
    page.js_returns.update({
        "/*click-filter*/": True,
        "/*select-radio*/": False,
        "/*show-results*/": True,
    })
    assert _apply_content_filters(page, "past-week") is False

    page2 = FakePage()
    page2.js_returns.update({
        "/*click-filter*/": True,
        "/*select-radio*/": True,
        "/*show-results*/": False,
    })
    assert _apply_content_filters(page2, "past-week") is False


# -- feed scrolling -------------------------------------------------------------
def test_count_posts_and_scroll_bottom_branches():
    page = FakePage()
    page.js_returns["/*count-posts*/"] = 7
    page.js_returns["/*scroll-bottom*/"] = True
    assert _count_posts(page) == 7
    assert _scroll_to_bottom(page) is True
    assert _count_posts(_BrokenPage()) == 0
    assert _scroll_to_bottom(_BrokenPage()) is False


def test_wheel_feed_moves_mouse_over_column_and_wheels():
    page = FakePage()
    page.js_returns["/*feed-rect*/"] = {
        "x": 100, "y": 50, "width": 800, "height": 2000,
    }
    _wheel_feed(page)
    assert page.mouse.moved and len(page.mouse.wheeled) == mod.WHEEL_STEPS


def test_wheel_feed_falls_back_when_rect_missing():
    page = FakePage()
    page.js_returns["/*feed-rect*/"] = None
    _wheel_feed(page)
    assert page.mouse.wheeled == [mod.WHEEL_DY * mod.WHEEL_STEPS]


def test_wheel_feed_swallows_mouse_failures():
    page = FakePage()
    page.mouse = FakeMouse(fail=True)
    page.js_returns["/*feed-rect*/"] = {
        "x": 0, "y": 0, "width": 500, "height": 900,
    }
    _wheel_feed(page)                       # move + fallback both raise
    page.js_returns["/*feed-rect*/"] = None
    _wheel_feed(page)                       # fallback raise
    assert page.mouse.wheeled == []


def test_wheel_feed_swallows_rect_probe_error():
    _wheel_feed(_BrokenPage())              # rect probe raises → no-op


# -- extraction checkpoints ------------------------------------------------------
def test_extract_fresh_dedupes_and_calls_hook():
    page = FakePage()
    page.cards_queue = [[CARD, dict(CARD)], [CARD]]
    seen: set[tuple[str, str]] = set()
    batches: list[list[EmailContact]] = []
    out = _extract_fresh(page, "ltm.com", "@ltm.com", seen, batches.append)
    assert [c.email for c in out] == ["neha.pandey@ltm.com"]
    assert batches and batches[0] == out
    # Second extraction sees the same post → nothing new, no second hook.
    assert _extract_fresh(page, "ltm.com", "@ltm.com", seen, batches.append) == []
    assert len(batches) == 1
    assert any(CONTENT_EXTRACT_JS in js for js in page.evals)


def test_extract_fresh_survives_extractor_error_without_hook():
    class _CardBroken(FakePage):
        def evaluate(self, js):  # type: ignore[override]
            if "/*content-email-cards*/" in js:
                raise RuntimeError("detached")
            return super().evaluate(js)

    assert _extract_fresh(_CardBroken(), "ltm.com", "@ltm.com", set(), None) == []


def test_collect_view_grows_until_target():
    page = FakePage()
    counts = iter([6, 12, 18, 24])
    contacts = [EmailContact(email="a@ltm.com", post_id="a", domain="ltm.com")]
    extracted: list[list[EmailContact]] = []
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(mod, "_count_posts", lambda p: next(counts))
        monkeypatch.setattr(mod, "_extract_fresh",
                            lambda *a, **k: extracted.append(list(contacts))
                            or list(contacts))
        out = _collect_view(page, "@ltm.com", "ltm.com", rounds=5, target=24,
                            seen=set(), on_batch=None)
    finally:
        monkeypatch.undo()
    assert len(out) == 3                    # round 0 + target round + final
    assert len(extracted) == 3


def test_collect_view_stops_after_three_stalls():
    page = FakePage()
    extracted: list[int] = []
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(mod, "_count_posts", lambda p: 6)
        monkeypatch.setattr(mod, "_scroll_to_bottom", lambda p: True)
        monkeypatch.setattr(mod, "_extract_fresh",
                            lambda *a, **k: extracted.append(1) or [])
        _collect_view(page, "@ltm.com", "ltm.com", rounds=10, target=100,
                      seen=set(), on_batch=None)
    finally:
        monkeypatch.undo()
    # Checkpoint on round 0, each stalled round, and the final extraction.
    assert len(extracted) == 4


def test_collect_view_breaks_on_empty_feed_and_zero_rounds():
    page = FakePage()
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(mod, "_count_posts", lambda p: 0)
        monkeypatch.setattr(mod, "_extract_fresh", lambda *a, **k: [])
        assert _collect_view(page, "@ltm.com", "ltm.com", 5, 100,
                             set(), None) == []
        assert _collect_view(page, "@ltm.com", "ltm.com", 0, 100,
                             set(), None) == []
    finally:
        monkeypatch.undo()


def test_collect_view_growth_without_checkpoint_branch():
    page = FakePage()
    counts = iter([6, 12, 18, 24, 30, 36])
    extracted: list[int] = []
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(mod, "_count_posts", lambda p: next(counts))
        monkeypatch.setattr(mod, "_extract_fresh",
                            lambda *a, **k: extracted.append(1) or [])
        # rounds=2 → round 0 checkpoint, round 1 growth with no checkpoint,
        # then the final extraction after the loop.
        _collect_view(page, "@ltm.com", "ltm.com", 2, 100, set(), None)
    finally:
        monkeypatch.undo()
    assert len(extracted) == 2


# -- collect loop ---------------------------------------------------------------
def _wire_run(monkeypatch, batches, *, feed=True, search=True, posts=True,
              wall_values=None, filter_result=True):
    """Monkeypatch run_collect's collaborators; record important calls."""
    calls: dict = {"collect": [], "filters": []}
    monkeypatch.setattr(mod, "_open_feed", lambda p: feed)
    monkeypatch.setattr(mod, "_submit_search",
                        lambda p, kw: calls.setdefault("searched", []).append(kw)
                        or search)
    walls = _sequence(*(wall_values or [False, False, False, False]))

    def _wall(_p):
        try:
            return walls()
        except StopIteration:
            return False

    monkeypatch.setattr(mod, "_check_bot_wall", _wall)
    monkeypatch.setattr(mod, "_open_posts_view", lambda p: posts)

    def _filters(_p, facet):
        calls["filters"].append(facet)
        return filter_result

    monkeypatch.setattr(mod, "_apply_content_filters", _filters)
    queue = list(batches)

    def _collect(_p, keyword, domain, rounds, target, seen, on_batch):
        calls["collect"].append((domain, rounds, target))
        batch = queue.pop(0) if queue else []
        if batch and on_batch:
            new = [c for c in batch
                   if (c.email, c.post_id) not in seen]
            seen.update((c.email, c.post_id) for c in new)
            if new:
                on_batch(new)
        return batch

    monkeypatch.setattr(mod, "_collect_view", _collect)
    return calls


def test_run_collect_happy_path_two_views_and_dedupes(monkeypatch):
    c1 = EmailContact(email="a@ltm.com", post_id="p1", domain="ltm.com")
    c2 = EmailContact(email="b@ltm.com", post_id="p2", domain="ltm.com")
    calls = _wire_run(monkeypatch, [[c1], [c1, c2], [c2]])
    batches: list[list[EmailContact]] = []
    page = FakePage()
    ctx = FakeContext(page)
    out = run_collect(ctx, domains=["ltm.com"], max_scrolls=3,
                      date_facet="past-month", on_batch=batches.append)
    assert {c.email for c in out} == {"a@ltm.com", "b@ltm.com"}
    assert calls["searched"] == ["@ltm.com"]
    assert calls["filters"] == ["past-month"]
    assert calls["collect"] == [("ltm.com", 3, mod.SETTINGS.email_target_posts)] * 2
    assert batches and all(b for b in batches)
    assert ctx.closed is False                    # caller owns close()


def test_run_collect_defaults_from_settings(monkeypatch):
    from src import config
    monkeypatch.setattr(config.SETTINGS, "email_domains", ["one.com"])
    monkeypatch.setattr(config.SETTINGS, "email_max_scrolls", 7)
    monkeypatch.setattr(config.SETTINGS, "email_date_facet", "past-week")
    monkeypatch.setattr(config.SETTINGS, "email_target_posts", 55)
    calls = _wire_run(monkeypatch, [])
    out = run_collect(FakeContext(FakePage()))
    assert out == []
    assert calls["searched"] == ["@one.com"]
    assert calls["filters"] == ["past-week"]
    assert calls["collect"] == [("one.com", 7, 55), ("one.com", 7, 55)]


def test_run_collect_rejects_unknown_facet():
    with pytest.raises(ValueError):
        run_collect(FakeContext(FakePage()), domains=["tcs.com"],
                    date_facet="past-year")


def test_run_collect_stops_when_feed_cannot_open(monkeypatch):
    _wire_run(monkeypatch, [], feed=False)
    assert run_collect(FakeContext(FakePage()), domains=["tcs.com"]) == []


def test_run_collect_stops_when_search_box_fails(monkeypatch):
    calls = _wire_run(monkeypatch, [], search=False)
    assert run_collect(FakeContext(FakePage()), domains=["tcs.com"]) == []
    assert calls["searched"] == ["@tcs.com"]


def test_run_collect_stops_on_search_wall(monkeypatch):
    calls = _wire_run(monkeypatch, [], wall_values=[True, False])
    assert run_collect(FakeContext(FakePage()), domains=["tcs.com"]) == []
    assert calls["collect"] == []


def test_run_collect_skips_content_view_without_posts_tab(monkeypatch):
    c1 = EmailContact(email="a@ltm.com", post_id="p1", domain="ltm.com")
    calls = _wire_run(monkeypatch, [[c1], []], posts=False)
    out = run_collect(FakeContext(FakePage()), domains=["ltm.com"])
    assert [c.email for c in out] == ["a@ltm.com"]
    assert calls["filters"] == []                 # content view skipped


def test_run_collect_still_scrapes_when_filters_unavailable(monkeypatch):
    c1 = EmailContact(email="a@ltm.com", post_id="p1", domain="ltm.com")
    c2 = EmailContact(email="b@ltm.com", post_id="p2", domain="ltm.com")
    calls = _wire_run(monkeypatch, [[c1], [c2]], filter_result=False)
    out = run_collect(FakeContext(FakePage()), domains=["ltm.com"],
                      max_scrolls=2)
    assert [c.email for c in out] == ["a@ltm.com", "b@ltm.com"]
    assert calls["filters"] == ["past-month"]      # attempted, not applied


def test_run_collect_stops_on_wall_after_filters(monkeypatch):
    c1 = EmailContact(email="a@ltm.com", post_id="p1", domain="ltm.com")
    # wall sequence: search-check False, filter-check True
    calls = _wire_run(monkeypatch, [[c1], []], wall_values=[False, True])
    out = run_collect(FakeContext(FakePage()), domains=["ltm.com"])
    assert [c.email for c in out] == ["a@ltm.com"]
    assert calls["collect"] == [("ltm.com", 40, 100)]   # URL2 never collected


def test_run_collect_continues_after_one_domain_and_respects_wall(monkeypatch):
    c1 = EmailContact(email="a@ltm.com", post_id="p1", domain="ltm.com")
    c2 = EmailContact(email="b@tcs.com", post_id="p2", domain="tcs.com")
    # domain 1: search wall False, filters wall False; domain 2: search wall True
    calls = _wire_run(monkeypatch, [[c1], [c1], [c2], [c2]],
                      wall_values=[False, False, True])
    out = run_collect(FakeContext(FakePage()),
                      domains=["ltm.com", "tcs.com"], max_scrolls=2)
    assert [c.email for c in out] == ["a@ltm.com"]
    assert calls["searched"] == ["@ltm.com", "@tcs.com"]
    assert calls["filters"] == ["past-month"]     # second domain never filters
