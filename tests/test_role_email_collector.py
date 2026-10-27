"""Offline tests for the role-targeted LinkedIn email collector."""
from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

import pytest

import src.linkedin_role_email as mod
from src.linkedin_role_email import (
    DEFAULT_DOMAINS,
    RoleEmailContact,
    build_contacts,
    build_post_rows,
    build_search_url,
    clean_post_id,
    clean_text,
    collect_domain,
    domain_email_matches,
    email_context,
    extract_cards,
    location_hint,
    merge_cards,
    open_search,
    parse_domains,
    phrase_context,
    phrase_matches,
    phrase_pattern,
    role_hint,
    run_role_collect,
    same_section,
    section_breaks,
    write_role_workbook,
)
from tests.conftest import FakeContext, FakePage


@pytest.fixture(autouse=True)
def quiet(monkeypatch):
    """No real pauses in the loop tests."""
    monkeypatch.setattr(mod, "human_pause", lambda *a, **k: None)


class _Broken:
    """Page double whose evaluate always raises."""

    def evaluate(self, js: str):
        raise RuntimeError("detached")


def _card(text: str, post_id: str = "p1", **over) -> dict:
    card = {
        "text": text,
        "post_id": post_id,
        "author": "Recruiter",
        "headline": "Talent Acquisition at Acme",
        "posted": "2d",
        "url": "",
    }
    card.update(over)
    return card


VALID_TEXT = (
    "Hiring: ASP.NET Core Developer\n"
    "Location: Pune\n"
    "Skills: C#, .NET, Web API\n"
    "Share your resume to recruiter@ltm.com"
)


# -- pure helpers ---------------------------------------------------------------
def test_build_search_url_uses_native_array_sort():
    url = build_search_url("asp.net core", "@LTM.com")
    assert url.startswith("https://www.linkedin.com/search/results/content/?")
    assert "keywords=asp.net%20core%20%40ltm.com" in url
    assert "origin=FACETED_SEARCH" in url
    assert "sortBy=%5B%22date_posted%22%5D" in url
    assert "datePosted" not in url


def test_parse_domains_defaults_strips_and_dedupes():
    assert parse_domains("") == list(DEFAULT_DOMAINS)
    assert parse_domains("@LTM.com, tcs.com,ltm.com") == ["ltm.com", "tcs.com"]


def test_clean_text_normalises_zero_width_and_email_obfuscation():
    text = "asp.net\u200b core [at] ltm [dot] com\u00a0(x)"
    assert clean_text(text) == "asp.net core@ltm.com (x)"


def test_phrase_matching_rejects_hashtags_and_unrelated_dotnet():
    assert phrase_matches("We need ASP.NET Core", "asp.net core")
    assert phrase_matches("asp.netcore developer", "asp.net core")
    assert phrase_matches("ASPNET Core developer", "asp.net core")
    assert phrase_matches("asp net core developer", "asp.net core")
    assert not phrase_matches("#ASPNETCore is a hashtag", "asp.net core")
    assert not phrase_matches("ASP.NET MVC / .NET Core", "asp.net core")
    assert phrase_pattern("").pattern  # empty phrase branch


def test_section_guard_detects_separator_between_positions():
    text = "BPO email bpo@wipro.com\n━━━━━━━━\nASP.NET Core role\nDotNet email dev@wipro.com"
    bpo = text.index("bpo@wipro.com")
    asp = text.index("ASP.NET Core")
    dotnet = text.index("dev@wipro.com")
    assert section_breaks(text)
    assert same_section(text, asp, dotnet) is True
    assert same_section(text, bpo, asp) is False


def test_domain_email_matches_exact_domain_spacing_and_junk():
    text = ("a@LTM.com, b @ ltm . com, c@other.com, "
            "...@ltm.com, logo@ltm.png")
    assert [e for e, _s, _e in domain_email_matches(text, "ltm.com")] == [
        "a@ltm.com", "b@ltm.com"]
    assert domain_email_matches(text, "ltm.png") == []


def test_context_helpers_cover_found_and_missing():
    text = "x " * 300 + "ASP.NET Core " + "y " * 300 + "a@ltm.com"
    assert "ASP.NET Core" in phrase_context(text, "asp.net core")
    assert phrase_context("nothing", "asp.net core") == ""
    assert "a@ltm.com" in email_context(text, "a@ltm.com")
    assert email_context(text, "missing@ltm.com") == ""


def test_role_and_location_hints_cover_all_paths():
    assert role_hint("Role: .NET Developer\nLocation: Pune") == ".NET Developer"
    assert role_hint("Role Summary -\nAzure Senior Developer") == "Azure Senior Developer"
    assert role_hint("Senior .NET Developer\nSkills: C#\nLocation: Pune") == "Senior .NET Developer"
    assert role_hint("Hello\nSkills: C#") == "Hello"
    assert role_hint("") == ""
    assert location_hint("Location: Pune\nExperience: 5") == "Pune"
    assert location_hint("📍 Bangalore") == "Bangalore"
    assert location_hint("no place") == ""


def test_clean_post_id_variants():
    assert clean_post_id("") == ""
    assert clean_post_id("nan") == ""
    assert clean_post_id("expandedABCFeedType_FLAGSHIP_SEARCH") == "ABC"
    assert clean_post_id("plain-id") == "plain-id"


def test_role_contact_rejects_bad_values_and_normalises():
    with pytest.raises(ValueError):
        RoleEmailContact(email="not-an-email", company="X", company_domain="ltm.com")
    with pytest.raises(ValueError):
        RoleEmailContact(email="a@ltm.com", company="X", company_domain="nope")
    contact = RoleEmailContact(
        email="A@LTM.COM", company="X", company_domain="@LTM.com",
        author="  A  B ", posted=" 2d ", role=" Dev ", location=" Pune ",
        post_url="  https://x  ")
    assert contact.email == "a@ltm.com"
    assert contact.company_domain == "ltm.com"
    assert contact.author == "A B" and contact.posted == "2d"
    assert contact.role == "Dev" and contact.location == "Pune"
    assert contact.post_url == "https://x"


# -- card → contacts ------------------------------------------------------------
def test_build_contacts_maps_evidence_and_section_guard():
    cards = [
        _card(VALID_TEXT, "p1"),
        _card(VALID_TEXT, "p2", url="https://www.linkedin.com/posts/x"),
        _card("no phrase here; mail a@ltm.com", "p3"),
        _card("ASP.NET Core but no email", "p4"),
        _card("We are hiring a developer without the phrase", "p5"),
    ]
    out = build_contacts(cards, "LTIMindtree", "ltm.com", "asp.net core",
                         collected_at="2026-10-27T00:00:00")
    assert [c.email for c in out] == ["recruiter@ltm.com", "recruiter@ltm.com"]
    assert out[0].post_rank == 1
    assert out[0].post_id == "p1" and out[0].post_reference == "p1"
    assert out[1].post_reference.startswith("https://www.linkedin.com/posts/")
    assert out[0].role == "ASP.NET Core Developer"
    assert out[0].location == "Pune"
    assert "ASP.NET Core" in out[0].phrase_evidence
    assert "recruiter@ltm.com" in out[0].email_context
    assert out[0].search_query == "asp.net core @ltm.com"
    assert out[0].search_url == build_search_url("asp.net core", "ltm.com")
    assert out[0].collected_at == "2026-10-27T00:00:00"


def test_build_contacts_drops_wrong_section_email():
    text = (
        "We are hiring a Procurement Professional\n"
        "Mail bpo@wipro.com\n"
        "━━━━━━━━\n"
        "We are hiring a .NET Developer\n"
        "ASP.NET Core and C# required\n"
        "Mail dev@wipro.com"
    )
    out = build_contacts([_card(text, "w1")], "Wipro", "wipro.com",
                         "asp.net core")
    assert [c.email for c in out] == ["dev@wipro.com"]


def test_build_contacts_skips_empty_and_uses_default_timestamp():
    assert build_contacts([_card("")], "X", "x.com", "asp.net core") == []
    out = build_contacts([_card(VALID_TEXT)], "X", "ltm.com", "asp.net core")
    assert out[0].collected_at


# -- navigation / extraction ---------------------------------------------------
def test_open_search_success_and_selector_timeout():
    page = FakePage()
    assert open_search(page, "https://x") is True
    page.selector_fail = True
    assert open_search(page, "https://x") is True


def test_open_search_retries_then_succeeds():
    page = FakePage()
    page.goto_plan = [RuntimeError("slow"), None]
    assert open_search(page, "https://x") is True
    assert len(page.goto_urls) == 2


def test_open_search_all_attempts_fail_and_stop_error_is_swallowed():
    class _StopBroken(FakePage):
        def evaluate(self, js):
            if "window.stop" in js:
                raise RuntimeError("stop failed")
            return super().evaluate(js)

    page = _StopBroken()
    page.goto_plan = [RuntimeError("a"), RuntimeError("b"), RuntimeError("c")]
    assert open_search(page, "https://x") is False
    assert len(page.goto_urls) == 3


def test_extract_cards_and_merge_cards():
    page = FakePage()
    page.js_returns["/*role-content-cards*/"] = [{"post_id": "1", "text": "x"}]
    assert extract_cards(page)[0]["post_id"] == "1"
    assert extract_cards(_Broken()) == []
    target: OrderedDict[str, dict] = OrderedDict()
    merge_cards(target, [{"post_id": ""}, {"post_id": "1", "text": "x"}])
    merge_cards(target, [{"post_id": "1", "text": "changed"}])
    assert len(target) == 1 and target["1"]["text"] == "x"


# -- domain loop ----------------------------------------------------------------
def _wire_loop(monkeypatch, cards, counts=None):
    monkeypatch.setattr(mod, "open_search", lambda page, url: True)
    monkeypatch.setattr(mod, "_on_login_wall", lambda page: False)
    monkeypatch.setattr(mod, "_check_bot_wall", lambda page: False)
    monkeypatch.setattr(mod, "_expand_show_more", lambda page: 0)
    monkeypatch.setattr(mod, "_wheel_feed", lambda page: None)
    monkeypatch.setattr(mod, "_scroll_to_bottom", lambda page: True)
    monkeypatch.setattr(mod, "extract_cards", lambda page: cards)
    if counts is None:
        monkeypatch.setattr(mod, "_count_posts", lambda page: 1)
    elif len(counts) == 1:
        monkeypatch.setattr(mod, "_count_posts", lambda page: counts[0])
    else:
        seq = iter(counts)
        monkeypatch.setattr(mod, "_count_posts", lambda page: next(seq))


def test_collect_domain_nav_wall_login_and_bot_walls(monkeypatch):
    monkeypatch.setattr(mod, "open_search", lambda page, url: False)
    assert collect_domain(FakePage(), "X", "x.com", "asp.net core")[2] == "nav_timeout"
    monkeypatch.setattr(mod, "open_search", lambda page, url: True)
    monkeypatch.setattr(mod, "_on_login_wall", lambda page: True)
    assert collect_domain(FakePage(), "X", "x.com", "asp.net core")[2] == "login_wall"
    monkeypatch.setattr(mod, "_on_login_wall", lambda page: False)
    monkeypatch.setattr(mod, "_check_bot_wall", lambda page: True)
    assert collect_domain(FakePage(), "X", "x.com", "asp.net core")[2] == "wall"


def test_collect_domain_stops_at_twenty_when_target_met(monkeypatch):
    cards = [_card(VALID_TEXT.replace("recruiter@ltm.com", f"u{i}@ltm.com"),
                   f"p{i}") for i in range(20)]
    _wire_loop(monkeypatch, cards)
    contacts, posts, status = collect_domain(
        FakePage(), "LTIMindtree", "ltm.com", "asp.net core", target=10)
    assert len(posts) == 20 and len(contacts) == 20 and status == "ok"


def test_collect_domain_extends_to_thirty_when_under_target(monkeypatch):
    first = [_card(VALID_TEXT.replace("recruiter@ltm.com", "a@ltm.com"), "p1")]
    more = first + [
        _card(VALID_TEXT.replace("recruiter@ltm.com", f"u{i}@ltm.com"), f"p{i}")
        for i in range(2, 21)
    ]
    calls = {"n": 0}

    def _cards(page):
        calls["n"] += 1
        return first if calls["n"] == 1 else more

    monkeypatch.setattr(mod, "open_search", lambda page, url: True)
    monkeypatch.setattr(mod, "_on_login_wall", lambda page: False)
    monkeypatch.setattr(mod, "_check_bot_wall", lambda page: False)
    monkeypatch.setattr(mod, "_expand_show_more", lambda page: 0)
    monkeypatch.setattr(mod, "_wheel_feed", lambda page: None)
    monkeypatch.setattr(mod, "_scroll_to_bottom", lambda page: True)
    monkeypatch.setattr(mod, "extract_cards", _cards)
    seq = iter([1, 1, 20, 20])
    monkeypatch.setattr(mod, "_count_posts", lambda page: next(seq))
    contacts, posts, status = collect_domain(
        FakePage(), "LTIMindtree", "ltm.com", "asp.net core", target=10)
    assert len(posts) == 20 and len(contacts) == 20 and status == "ok"


def test_collect_domain_no_results_below_target_and_max_posts(monkeypatch):
    _wire_loop(monkeypatch, [], [0])
    monkeypatch.setattr(mod, "MAX_ROUNDS", 1)
    contacts, posts, status = collect_domain(FakePage(), "X", "x.com", "asp.net core")
    assert (contacts, posts, status) == ([], [], "no_results")

    _wire_loop(monkeypatch, [_card(VALID_TEXT, "p1")], [1])
    monkeypatch.setattr(mod, "MAX_ROUNDS", 2)
    contacts, posts, status = collect_domain(
        FakePage(), "X", "ltm.com", "asp.net core", target=10)
    assert len(contacts) == 1 and len(posts) == 1 and status == "below_target"

    cards = [_card(VALID_TEXT.replace("recruiter@ltm.com", f"u{i}@ltm.com"),
                   f"p{i}") for i in range(30)]
    _wire_loop(monkeypatch, cards)
    contacts, posts, status = collect_domain(
        FakePage(), "X", "ltm.com", "asp.net core", target=10, max_posts=30)
    assert len(posts) == 30 and len(contacts) == 30 and status == "ok"


def test_collect_domain_stall_and_duplicate_dedupe(monkeypatch):
    cards = [_card(VALID_TEXT, "p1"), _card(VALID_TEXT, "p2")]
    _wire_loop(monkeypatch, cards, [2])
    monkeypatch.setattr(mod, "MAX_ROUNDS", 6)
    contacts, posts, status = collect_domain(
        FakePage(), "X", "ltm.com", "asp.net core", target=10)
    assert len(contacts) == 1 and len(posts) == 2 and status == "below_target"


# -- run loop -------------------------------------------------------------------
def test_run_role_collect_stops_when_feed_unavailable(monkeypatch):
    monkeypatch.setattr(mod, "_open_feed", lambda page: False)
    assert run_role_collect(FakeContext(), ["ltm.com"]) == ([], [], [])


def test_run_role_collect_happy_path_callback_and_fallback_company(monkeypatch):
    monkeypatch.setattr(mod, "_open_feed", lambda page: True)
    calls: list[tuple] = []

    def _collect(page, company, domain, phrase, target, checkpoint, maximum):
        contact = RoleEmailContact(email="a@ltm.com", company=company,
                                   company_domain=domain, post_id="p1")
        return [contact], [{"post_id": "p1", "text": VALID_TEXT}], "ok"

    monkeypatch.setattr(mod, "collect_domain", _collect)
    monkeypatch.setattr(mod, "human_pause", lambda *a: calls.append(("pause", a)))
    contacts, posts, summary = run_role_collect(
        FakeContext(), ["ltm.com", "unknown.test"], target=1,
        on_domain=lambda *a: calls.append(("callback", len(a))))
    assert len(contacts) == 2 and len(posts) == 2 and len(summary) == 2
    assert summary[0]["company"] == "LTIMindtree"
    assert summary[1]["company"] == "unknown.test"
    assert ("callback", 3) in calls and any(c[0] == "pause" for c in calls)


def test_run_role_collect_wall_stops_and_nav_timeout_continues(monkeypatch):
    monkeypatch.setattr(mod, "_open_feed", lambda page: True)
    statuses = iter(["nav_timeout", "wall"])
    seen: list[str] = []

    def _collect(page, company, domain, phrase, target, checkpoint, maximum):
        seen.append(domain)
        return [], [], next(statuses)

    monkeypatch.setattr(mod, "collect_domain", _collect)
    contacts, posts, summary = run_role_collect(FakeContext(), ["a.com", "b.com", "c.com"])
    assert seen == ["a.com", "b.com"]
    assert [s["status"] for s in summary] == ["nav_timeout", "wall"]


# -- workbook -------------------------------------------------------------------
def test_write_role_workbook_all_sheets(tmp_path):
    contact = RoleEmailContact(
        email="a@ltm.com", company="LTIMindtree", company_domain="ltm.com",
        role=".NET Developer", location="Pune", post_rank=1,
        post_id="p1", post_reference="p1", phrase_evidence="ASP.NET Core",
        email_context="a@ltm.com", post_excerpt=VALID_TEXT,
        search_query="asp.net core @ltm.com",
        search_url=build_search_url("asp.net core", "ltm.com"),
        collected_at="2026-10-27T00:00:00")
    posts = build_post_rows(
        [{"post_id": "p1", "text": VALID_TEXT, "author": "R"}],
        [contact], "LTIMindtree", "ltm.com", "asp.net core")
    summary = [{
        "company": "LTIMindtree", "company_domain": "ltm.com",
        "posts_scanned": 1, "phrase_posts": 1, "qualified_posts": 1,
        "unique_emails": 1, "target_met": False, "status": "below_target",
        "search_url": build_search_url("asp.net core", "ltm.com"),
    }]
    dest = write_role_workbook(tmp_path / "nested" / "out.xlsx", [contact],
                               posts, summary)
    assert dest.exists()
    import pandas as pd
    assert pd.ExcelFile(dest).sheet_names == [
        "Email List", "Emails", "Summary", "Posts Scanned", "Method"]
    assert pd.read_excel(dest, sheet_name="Email List").iloc[0]["email"] == "a@ltm.com"


def test_write_role_workbook_empty_is_safe(tmp_path):
    dest = write_role_workbook(tmp_path / "empty.xlsx", [], [], [])
    assert dest.exists()


def test_build_post_rows_marks_qualified_and_domain_emails():
    contact = RoleEmailContact(email="a@ltm.com", company="LTIMindtree",
                               company_domain="ltm.com", post_id="p1")
    rows = build_post_rows([{"post_id": "p1", "text": VALID_TEXT}],
                           [contact], "LTIMindtree", "ltm.com", "asp.net core")
    assert rows[0]["phrase_match"] is True
    assert rows[0]["hiring"] is True and rows[0]["role"] is True
    assert rows[0]["domain_emails"] == "recruiter@ltm.com"
    assert rows[0]["qualified_emails"] == "a@ltm.com"


def test_build_contacts_skips_phrase_post_with_only_foreign_email():
    text = "We are hiring an ASP.NET Core developer. Mail other@example.com"
    assert build_contacts([_card(text)], "X", "ltm.com", "asp.net core") == []


def test_collect_domain_zero_rounds_and_growth_resets_stalls(monkeypatch):
    monkeypatch.setattr(mod, "open_search", lambda page, url: True)
    monkeypatch.setattr(mod, "_on_login_wall", lambda page: False)
    monkeypatch.setattr(mod, "_check_bot_wall", lambda page: False)
    monkeypatch.setattr(mod, "_expand_show_more", lambda page: 0)
    monkeypatch.setattr(mod, "_wheel_feed", lambda page: None)
    monkeypatch.setattr(mod, "_scroll_to_bottom", lambda page: True)
    monkeypatch.setattr(mod, "MAX_ROUNDS", 0)
    contacts, posts, status = collect_domain(
        FakePage(), "X", "ltm.com", "asp.net core")
    assert (contacts, posts, status) == ([], [], "no_results")

    monkeypatch.setattr(mod, "MAX_ROUNDS", 2)
    monkeypatch.setattr(mod, "extract_cards", lambda page: [
        _card(VALID_TEXT, "p1"),
        _card(VALID_TEXT.replace("recruiter@ltm.com", "b@ltm.com"), "p2"),
    ])
    seq = iter([1, 2])
    monkeypatch.setattr(mod, "_count_posts", lambda page: next(seq))
    contacts, posts, status = collect_domain(
        FakePage(), "X", "ltm.com", "asp.net core", target=1)
    assert len(contacts) == 2 and len(posts) == 2 and status == "ok"


def test_read_role_workbook_absent_corrupt_and_roundtrip(tmp_path):
    assert mod.read_role_workbook(tmp_path / "missing.xlsx") == ([], [], [])
    bad = tmp_path / "bad.xlsx"
    bad.write_text("not an excel file")
    assert mod.read_role_workbook(bad) == ([], [], [])

    contact = RoleEmailContact(
        email="a@ltm.com", company="LTIMindtree", company_domain="ltm.com",
        post_id="p1", post_reference="p1", post_rank=1)
    posts = [{"company_domain": "ltm.com", "post_id": "p1",
              "phrase_match": True, "qualified_emails": "a@ltm.com"}]
    summary = [{"company_domain": "ltm.com", "unique_emails": 1}]
    dest = write_role_workbook(tmp_path / "roundtrip.xlsx", [contact],
                               posts, summary)
    got_contacts, got_posts, got_summary = mod.read_role_workbook(dest)
    assert [c.email for c in got_contacts] == ["a@ltm.com"]
    assert got_posts[0]["post_id"] == "p1"
    assert got_summary[0]["company_domain"] == "ltm.com"


def test_read_role_workbook_skips_invalid_email_rows(tmp_path):
    import pandas as pd
    path = tmp_path / "invalid.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame([{"email": "bad", "company_domain": "ltm.com"},
                      {"email": "good@ltm.com", "company_domain": "ltm.com"}]
                     ).to_excel(writer, index=False, sheet_name="Emails")
        pd.DataFrame(columns=["post_id"]).to_excel(
            writer, index=False, sheet_name="Posts Scanned")
        pd.DataFrame(columns=["company_domain"]).to_excel(
            writer, index=False, sheet_name="Summary")
    contacts, _posts, _summary = mod.read_role_workbook(path)
    assert [c.email for c in contacts] == ["good@ltm.com"]


def test_run_role_collect_resume_replaces_success_and_keeps_failed(monkeypatch):
    monkeypatch.setattr(mod, "_open_feed", lambda page: True)
    old = RoleEmailContact(email="old@ltm.com", company="LTIMindtree",
                           company_domain="ltm.com", post_id="old")
    new = RoleEmailContact(email="new@ltm.com", company="LTIMindtree",
                           company_domain="ltm.com", post_id="new")
    old_summary = [{"company_domain": "ltm.com", "unique_emails": 1,
                    "company": "LTIMindtree", "status": "below_target"}]

    def _ok(page, company, domain, phrase, target, checkpoint, maximum):
        return [new], [{"post_id": "new", "text": VALID_TEXT}], "ok"

    monkeypatch.setattr(mod, "collect_domain", _ok)
    contacts, posts, summary = run_role_collect(
        FakeContext(), ["ltm.com"], initial_contacts=[old],
        initial_posts=[{"company_domain": "ltm.com", "post_id": "old"}],
        initial_summary=old_summary)
    assert [c.email for c in contacts] == ["new@ltm.com"]
    assert posts[0]["post_id"] == "new"
    assert summary[0]["unique_emails"] == 1

    def _wall(page, company, domain, phrase, target, checkpoint, maximum):
        return [], [], "wall"

    monkeypatch.setattr(mod, "collect_domain", _wall)
    contacts, posts, summary = run_role_collect(
        FakeContext(), ["ltm.com"], initial_contacts=[old],
        initial_posts=[{"company_domain": "ltm.com", "post_id": "old"}],
        initial_summary=old_summary)
    assert [c.email for c in contacts] == ["old@ltm.com"]
    assert posts[0]["post_id"] == "old"
    assert summary[0]["unique_emails"] == 1
