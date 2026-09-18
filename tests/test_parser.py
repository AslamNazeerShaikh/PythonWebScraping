"""Tests for src.parser — honeypot guards, card fallbacks, detail merge."""
from __future__ import annotations

from src.parser import _card_text, _is_trap, parse_detail_html, parse_search_html
from bs4 import BeautifulSoup


def _anchor(html: str):
    return BeautifulSoup(html, "lxml").select_one("a")


# -- _is_trap: every guard branch -------------------------------------------
def test_trap_empty_hash_and_javascript_hrefs():
    assert _is_trap(_anchor("<a>No href</a>")) is True
    assert _is_trap(_anchor("<a href='#'>hash</a>")) is True
    assert _is_trap(_anchor("<a href='javascript:void(0)'>js</a>")) is True


def test_trap_aria_hidden_and_inline_style():
    assert _is_trap(_anchor(
        "<a href='/job-listings-a-12345678' aria-hidden='true'>x</a>")) is True
    assert _is_trap(_anchor(
        "<a href='/job-listings-a-12345678' style='display:none'>x</a>")) is True
    assert _is_trap(_anchor(
        "<a href='/job-listings-a-12345678'>visible</a>")) is False


def test_trap_hidden_ancestor_and_bare_top():
    hidden = _anchor(
        "<div style='display:none'><a href='/job-listings-a-12345678'>x</a></div>")
    assert _is_trap(hidden) is True
    aria = _anchor(
        "<div aria-hidden='true'><span><a href='/job-listings-a-12345678'>x</a></span></div>")
    assert _is_trap(aria) is True


def test_card_text_none_card():
    assert _card_text(None, ["a"]) == ""


# -- parse_search_html --------------------------------------------------------
def test_parse_search_filters_traps_and_dupes():
    html = """<html><body>
    <article><a href="/job-listings-dotnet-dev-11111111">.NET Developer</a>
      <a class="comp" href="/c">XCorp</a><span class="loc">Pune</span>
      <span class="exp">6 Yrs</span><span class="sal">10 Lacs</span>
      <span class="posted">today</span><div class="desc">asp.net core</div></article>
    <a href="#">trap</a>
    <a href="/job-listings-hidden-22222222" style="display:none">Hidden</a>
    <div style="display:none"><a href="/job-listings-nested-33333333">Nested</a></div>
    <a href="/job-listings-nojd">No digits, no match</a>
    <a href="/job-listings-short-44444444">AB</a>
    <a href="/job-listings-dotnet-dev-11111111">dup</a>
    </body></html>"""
    cards = parse_search_html(html)
    assert len(cards) == 1
    c = cards[0]
    assert c["job_id"] == "11111111"
    assert (c["company"], c["location"], c["experience"], c["salary"],
            c["posted"]) == ("XCorp", "Pune", "6 Yrs", "10 Lacs", "today")
    assert c["url"] == "https://www.naukri.com/job-listings-dotnet-dev-11111111"
    assert c["apply_url"] == c["url"]


def test_parse_search_anchor_outside_card_and_title_fallback():
    html = ("<html><body>"
            "<a href='/job-listings-solo-55555555'>Solo .NET Developer Role</a>"
            "</body></html>")
    cards = parse_search_html(html)
    assert len(cards) == 1
    assert cards[0]["company"] == ""  # no card -> _card_text(None) guards


def test_parse_search_card_title_fallback():
    html = """<html><body><article>
    <h2><a href="/job-listings-h2title-66666666">H2 Card .NET Title</a></h2>
    </article></body></html>"""
    assert parse_search_html(html)[0]["title"] == "H2 Card .NET Title"


# -- parse_detail_html ---------------------------------------------------------
def test_parse_detail_external_apply_wins_over_traps():
    html = """<html><body>
    <section class="job-desc">Great .NET role</section>
    <a class="skill" href="/s">C#</a><span class="skill">SQL</span>
    <a href="https://evil.test/apply" style="display:none">Apply trap</a>
    <a href="https://company.test/careers/123">Apply on company site</a>
    </body></html>"""
    d = parse_detail_html(html, "https://www.naukri.com/job-listings-x-77777777?a=1")
    assert d["description"] == "Great .NET role"
    assert d["skills"] == ["C#", "SQL"]
    assert d["apply_url"] == "https://company.test/careers/123"


def test_parse_detail_internal_apply_keeps_canonical():
    html = """<html><body><div class="job-desc">Desc</div>
    <a href="https://www.naukri.com/apply/1">Apply now</a></body></html>"""
    d = parse_detail_html(html, "https://www.naukri.com/job-listings-x-88888888")
    assert d["apply_url"] == "https://www.naukri.com/job-listings-x-88888888"


def test_parse_detail_no_desc_no_skills_no_apply():
    d = parse_detail_html("<html><body><p>bare</p></body></html>",
                          "https://www.naukri.com/job-listings-x-99999999?x=1")
    assert d == {"description": "", "skills": [],
                 "apply_url": "https://www.naukri.com/job-listings-x-99999999"}
