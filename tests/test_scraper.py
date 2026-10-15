"""Tests for src.naukri_scraper — URLs, guards, extraction, full fake runs."""
from __future__ import annotations

import pytest

import src.naukri_scraper as ns
from src.config import SETTINGS
from src.models import Job
from tests.conftest import FakeContext, FakeMouse, FakePage, raw_card


# -- pure helpers -------------------------------------------------------------
# -- in-page JS hygiene ---------------------------------------------------------
def test_listing_js_has_no_location_shadowing():
    # Regression (found live): a `const location` in the extractor scope puts
    # `location.origin` in the temporal dead zone -> ReferenceError per card,
    # swallowed by the inner try/catch -> every result silently dropped.
    # The field var must be named `loc`; origin must use window.location.
    assert "const location" not in ns.LISTING_EXTRACT_JS
    assert "window.location.origin" in ns.LISTING_EXTRACT_JS
    assert "location: loc" in ns.LISTING_EXTRACT_JS


def test_build_search_url_encodes_params():
    url = ns.build_search_url("asp.net core c#", "pune", 6, 7, 2)
    assert url.startswith("https://www.naukri.com/jobs?")
    assert "experience=6" in url and "jobPostDate=7" in url and "page=2" in url
    assert "l=pune" in url and "c%23" in url  # '#' encoded, location present


def test_is_relevant():
    assert ns.is_relevant("Senior .NET Developer") is True
    assert ns.is_relevant("Java Developer", "asp.net core experience") is True
    assert ns.is_relevant("Java Developer", "spring boot only") is False
    assert ns.is_relevant("Fullstack Engineer (Angular, .NET)") is True


def test_normalize_raw_camel_and_snake_shapes():
    n = ns.normalize_raw(raw_card("12345678"), "pune")
    assert n["job_id"] == "12345678"
    assert n["search_location"] == "pune"
    assert n["apply_url"] == n["url"]  # default fallback
    snake = {"job_id": "99999999", "title": "X .NET Y",
             "url": "https://h/job-listings-x-99999999?a=1",
             "apply_url": "https://co.test/a?b=1",
             "snippet": "s" * 900, "description": "d" * 9000, "skills": ["C#"]}
    n2 = ns.normalize_raw(snake)
    assert n2["apply_url"] == "https://co.test/a"
    assert len(n2["snippet"]) == 600 and len(n2["description"]) == 6000


def test_coerce_job_valid_and_dropped(caplog):
    job = ns.coerce_job(raw_card("12345678"), "pune")
    assert isinstance(job, Job) and job.job_id == "12345678"
    assert ns.coerce_job({"jobId": "1", "title": "AB",
                          "url": "https://x"}, "pune") is None


# -- bot-wall handling ----------------------------------------------------------
def test_check_bot_wall_clean_and_blocked():
    assert ns.check_bot_wall(FakePage()) is False  # normal page
    wall = FakePage()
    wall.body_text = "Please verify you are human, captcha required"
    wall.anchor_count = 0
    assert ns.check_bot_wall(wall) is True
    # Block text BUT job anchors present -> not a wall (avoids false +ves).
    wall.anchor_count = 5
    assert ns.check_bot_wall(wall) is False


def test_check_bot_wall_evaluate_failure_is_safe():
    class Boom:
        def evaluate(self, js): raise RuntimeError("js dead")
        def title(self): raise RuntimeError("no title")

    assert ns.check_bot_wall(Boom()) is False


def test_handle_block_noop_never_prompts(monkeypatch):
    def _explode(*a, **k):
        raise AssertionError("input must not be called on clean pages")

    monkeypatch.setattr("builtins.input", _explode)
    ns.handle_possible_block(FakePage())  # no block -> returns quietly


def test_handle_block_prompts_then_continues(monkeypatch):
    wall = FakePage()
    wall.body_text = "Access Denied - unusual traffic detected"
    wall.anchor_count = 0
    monkeypatch.setattr("builtins.input", lambda *a, **k: "")
    monkeypatch.setattr(ns, "human_pause", lambda *a, **k: None)
    ns.handle_possible_block(wall)  # ENTER pressed -> continues


def test_handle_block_eoferror_in_noninteractive(monkeypatch):
    wall = FakePage()
    wall.body_text = "captcha - are you a robot?"
    wall.anchor_count = 0

    def _eof(*a, **k):
        raise EOFError

    monkeypatch.setattr("builtins.input", _eof)
    monkeypatch.setattr(ns, "human_pause", lambda *a, **k: None)
    ns.handle_possible_block(wall)  # EOF swallowed, run continues


# -- scrolling -------------------------------------------------------------------
def test_human_scroll_wheels_and_wiggles():
    page = FakePage()
    ns.human_scroll(page, rounds=2)
    assert len(page.mouse.wheeled) == 2 and len(page.mouse.moved) == 1
    assert page.timeouts  # small settle pauses recorded


def test_human_scroll_mouse_failure_falls_back():
    page = FakePage()
    page.mouse = FakeMouse(fail=True)
    ns.human_scroll(page, rounds=1)  # wheel->evaluate, move->swallowed


# -- tenacity-guarded navigation ----------------------------------------------------
def test_safe_goto_success():
    page = FakePage()
    ns._safe_goto(page, "https://example.test")
    assert page.goto_urls == ["https://example.test"]


def test_safe_goto_retries_playwright_timeout_error():
    # Regression: page.goto raises playwright's TimeoutError (not builtin);
    # tenacity must catch it or live retries silently never fire.
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    page = FakePage()
    page.goto_plan = [PlaywrightTimeoutError("slow"), None]
    ns._safe_goto(page, "https://example.test")
    assert len(page.goto_urls) == 2


def test_safe_goto_retries_then_reraises():
    page = FakePage()
    page.goto_plan = [TimeoutError("t1"), TimeoutError("t2"), TimeoutError("t3")]
    with pytest.raises(TimeoutError):
        ns._safe_goto(page, "https://example.test")
    assert len(page.goto_urls) == 3  # stop_after_attempt(3), then give up


# -- search page ----------------------------------------------------------------------
def test_scrape_search_page_returns_cards(monkeypatch, tmp_path):
    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111"), raw_card("22222222")]]
    assert len(ns.scrape_search_page(page, "https://u")) == 2


def test_scrape_search_page_empty_saves_debug(monkeypatch, tmp_path):
    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    page = FakePage()
    page.selector_fail = True  # forces the selector-timeout warning branch
    assert ns.scrape_search_page(page, "https://u") == []
    dbg = tmp_path / "debug_last_search.html"
    assert dbg.exists() and "jobs" in dbg.read_text()


def test_scrape_search_page_debug_save_failure_swallowed(monkeypatch, tmp_path):
    monkeypatch.setattr(SETTINGS, "output_dir", tmp_path)
    page = FakePage()
    page.content_fail = True
    assert ns.scrape_search_page(page, "https://u") == []


# -- enrichment --------------------------------------------------------------------------
def test_enrich_job_merges_detail():
    from tests.conftest import make_job
    page = FakePage()
    page.detail_result = {"company": "DCorp", "posted": "",
                          "pageTitle": "H1 ignored", "skills": ["C#"],
                          "applyUrl": "https://co.test/apply",
                          "description": "Full desc"}
    out = ns.enrich_job(page, make_job("12345678"))
    assert out.company == "DCorp" and out.skills == ["C#"]
    assert out.apply_url == "https://co.test/apply"
    assert out.description == "Full desc"


def test_enrich_job_ignores_unknown_detail_keys():
    from tests.conftest import make_job
    page = FakePage()
    page.detail_result = {"zzz_unknown_field": "v", "skills": ["C#"]}
    out = ns.enrich_job(page, make_job("12345678"))
    assert out.skills == ["C#"] and not hasattr(out, "zzz_unknown_field")


def test_enrich_job_empty_apply_url_falls_back_to_job_url():
    from tests.conftest import make_job
    page = FakePage()
    page.detail_result = {}  # nothing merged; both urls empty -> fallback line
    job = make_job("12345678", url="", apply_url="")
    assert ns.enrich_job(page, job).apply_url == ""


def test_enrich_job_timeout_returns_original(monkeypatch):
    from tests.conftest import make_job
    job = make_job("12345678")
    monkeypatch.setattr(ns, "_safe_goto",
                        lambda *a, **k: (_ for _ in ()).throw(TimeoutError("slow")))
    assert ns.enrich_job(FakePage(), job) == job


def test_enrich_job_validation_failure_returns_original():
    from tests.conftest import make_job
    page = FakePage()
    page.detail_result = {"title": "x"}  # merged title too short -> invalid
    job = make_job("12345678")
    assert ns.enrich_job(page, job) == job


def test_enrich_job_unexpected_error_returns_original():
    from tests.conftest import make_job
    page = FakePage()
    page.detail_result = ValueError("dom exploded")
    job = make_job("12345678")
    assert ns.enrich_job(page, job) == job


# -- full runs ------------------------------------------------------------------------------
def _tune(monkeypatch, **kw):
    monkeypatch.setattr(ns, "human_pause", lambda *a, **k: None)
    defaults = dict(keywords="asp.net core", locations=["pune"], experience=6,
                    date_filter=7, max_pages_per_search=2, max_jobs_total=10,
                    enrich_details=True)
    defaults.update(kw)
    for k, v in defaults.items():
        monkeypatch.setattr(SETTINGS, k, v)


def test_run_scrape_full_flow(monkeypatch):
    _tune(monkeypatch)
    page = FakePage()
    irrelevant = raw_card("99999991", "Java Spring Developer")
    irrelevant["snippet"] = "spring boot microservices only"  # no .NET -> filtered
    page.listing_queue = [
        [raw_card("11111111"),                       # valid
         {"jobId": "1", "title": "AB", "url": "https://x"},  # invalid -> dropped
         irrelevant,                                 # filtered out
         raw_card("11111111")],                      # duplicate -> skipped
        [raw_card("22222222")],                      # page 2
    ]
    page.detail_result = {"skills": ["C#"]}
    jobs = ns.run_scrape(FakeContext(page))
    assert sorted(j.job_id for j in jobs) == ["11111111", "22222222"]
    assert all(j.skills == ["C#"] for j in jobs)  # enriched
    assert len(page.goto_urls) == 2 + 2  # 2 searches + 2 details


def test_run_scrape_no_enrich_and_cap(monkeypatch):
    _tune(monkeypatch, max_jobs_total=1, enrich_details=False, max_pages_per_search=1)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111"), raw_card("22222222")]]
    jobs = ns.run_scrape(FakeContext(page))
    assert [j.job_id for j in jobs] == ["11111111"]  # cap stops collection
    assert len(page.goto_urls) == 1  # no detail visits


def test_run_scrape_cap_breaks_next_page_loop(monkeypatch):
    # Cap fills on page 1 -> the NEXT page iteration hits the top-of-loop
    # `break` (line 372) without even building a goto.
    _tune(monkeypatch, max_jobs_total=1, enrich_details=False,
          max_pages_per_search=3)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111")], [raw_card("22222222")]]
    jobs = ns.run_scrape(FakeContext(page))
    assert [j.job_id for j in jobs] == ["11111111"]
    assert len(page.goto_urls) == 1


def test_run_scrape_search_error_continues(monkeypatch):
    _tune(monkeypatch, max_pages_per_search=2, enrich_details=False)
    page = FakePage()
    page.goto_plan = [RuntimeError("boom"), None]  # p1 fails, p2 ok
    page.listing_queue = [[raw_card("11111111")]]
    jobs = ns.run_scrape(FakeContext(page))
    assert [j.job_id for j in jobs] == ["11111111"]


def test_run_scrape_close_failure_swallowed(monkeypatch):
    _tune(monkeypatch, max_pages_per_search=1, enrich_details=False)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111")]]
    page.close_fail = True
    assert len(ns.run_scrape(FakeContext(page))) == 1


# -- file snapshots ----------------------------------------------------------------------------
def test_save_results_writes_json_and_csv(tmp_path):
    from tests.conftest import make_job
    jobs = [make_job("11111111"), make_job("22222222", search_location="hyd")]
    jp, cp = ns.save_results(jobs, output_dir=tmp_path)
    assert jp.exists() and cp.exists()
    import csv as _csv
    import json as _json
    assert len(_json.loads(jp.read_text())) == 2
    rows = list(_csv.DictReader(cp.read_text().splitlines()))
    assert [r["job_id"] for r in rows] == ["11111111", "22222222"]
    assert "apply_url" in rows[0]


# -- cooperative hooks (web orchestrator: cancel + progress) -----------------------------------
def test_run_scrape_stop_during_enrich_keeps_partial(monkeypatch):
    _tune(monkeypatch, max_pages_per_search=3, enrich_details=True)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111")], [raw_card("22222222")],
                          [raw_card("33333333")]]
    page.detail_result = {"skills": ["C#"]}
    calls = [0]

    def _stop():
        calls[0] += 1
        return calls[0] > 3  # three page polls pass; enrich poll stops it

    seen: list = []
    jobs = ns.run_scrape(FakeContext(page), should_stop=_stop,
                         on_progress=seen.append)
    assert sorted(j.job_id for j in jobs) == ["11111111", "22222222", "33333333"]
    assert all(j.skills == [] for j in jobs)  # details skipped after stop
    assert [s["stage"] for s in seen] == ["search", "search", "search", "done"]


def test_run_scrape_stop_before_first_page_reports_done(monkeypatch):
    _tune(monkeypatch, max_pages_per_search=2, enrich_details=False)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111")]]
    seen: list = []
    jobs = ns.run_scrape(FakeContext(page), should_stop=lambda: True,
                         on_progress=seen.append)
    assert jobs == []  # cancelled early: nothing collected, nothing lost
    assert [s["stage"] for s in seen] == ["done"]
    assert page.goto_urls == []  # no navigation happened


# -- key-skills scan -------------------------------------------------------------------------------
def _tune_skills(monkeypatch, **kw):
    monkeypatch.setattr(ns, "human_pause", lambda *a, **k: None)
    return kw


def _detail_skills(*skills):
    return {"skills": list(skills)}


def test_build_skills_report_counts_postings_once(monkeypatch):
    from tests.conftest import make_job

    _tune_skills(monkeypatch)
    jobs = [make_job("11111111", skills=["C#", "c#", "ASP.NET", "C#", "", "  "]),  # dupes + blanks collapse
            make_job("22222222", company="Globex", skills=["c#", "SQL"]),
            make_job("33333333", company="Initech")]  # no skills
    rep = ns.build_skills_report(jobs)
    assert rep["jobs_scanned"] == 3 and rep["with_skills"] == 2
    assert rep["unique_skills"] == 3
    top = {t["skill"]: t for t in rep["top"]}
    assert top["C#"]["count"] == 2 and top["C#"]["pct"] == round(200 / 3, 1)
    assert top["C#"]["companies"] == [{"name": "Acme", "count": 1},
                                      {"name": "Globex", "count": 1}]  # tie -> alpha
    assert top["SQL"]["companies"] == [{"name": "Globex", "count": 1}]
    assert len(rep["top"]) <= 30


def test_build_skills_report_unknown_company():
    from tests.conftest import make_job

    rep = ns.build_skills_report([make_job("11111111", company="",
                                           skills=["Go"])])
    assert rep["top"][0]["companies"] == [{"name": "Unknown", "count": 1}]


def test_build_skills_report_empty():
    assert ns.build_skills_report([]) == {"jobs_scanned": 0, "with_skills": 0,
                                          "unique_skills": 0, "top": []}


def test_run_skills_scan_full_flow(monkeypatch):
    _tune_skills(monkeypatch)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111")],
                          [raw_card("22222222"), raw_card("11111111"),  # dup skipped
                           {"jobId": "1", "title": "AB", "url": "https://x"}]]  # invalid dropped
    page.detail_result = _detail_skills("C#", "SQL")
    seen: list = []
    rep = ns.run_skills_scan(FakeContext(page), "asp.net core", "pune",
                             6, 7, 2, 10, on_progress=seen.append)
    assert rep["jobs_scanned"] == 2 and rep["unique_skills"] == 2
    assert [s["stage"] for s in seen] == ["search", "search", "detail",
                                          "detail", "done"]
    assert len(page.goto_urls) == 2 + 2  # 2 searches + 2 details


def test_run_skills_scan_cap_breaks_page_loop(monkeypatch):
    _tune_skills(monkeypatch)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111"), raw_card("22222222")],
                          [raw_card("33333333")]]
    rep = ns.run_skills_scan(FakeContext(page), "asp.net core", "pune",
                             6, 7, 3, 1)
    assert rep["jobs_scanned"] == 1
    searches = [u for u in page.goto_urls if "/jobs?" in u]
    assert searches == []  # p1 goes through the search bar (homepage), not /jobs?


def test_run_skills_scan_stop_mid_pass_keeps_partial(monkeypatch):
    _tune_skills(monkeypatch)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111")], [raw_card("22222222")]]
    calls = [0]

    def _stop():
        calls[0] += 1
        return calls[0] > 3  # two pages pass; third page poll + enrich stop it

    seen: list = []
    rep = ns.run_skills_scan(FakeContext(page), "a", "pune", 6, 7, 3,
                             10, should_stop=_stop, on_progress=seen.append)
    assert rep["jobs_scanned"] == 2  # both pages done, details skipped
    assert [s["stage"] for s in seen] == ["search", "search", "search", "done"]


def test_run_skills_scan_stop_before_first_title(monkeypatch):
    _tune_skills(monkeypatch)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111")]]
    seen: list = []
    rep = ns.run_skills_scan(FakeContext(page), "a", "pune", 6, 7, 2, 10,
                             should_stop=lambda: True,
                             on_progress=seen.append)
    assert rep["jobs_scanned"] == 0
    assert [s["stage"] for s in seen] == ["done"]
    assert page.goto_urls == []


def test_run_skills_scan_search_error_continues(monkeypatch):
    _tune_skills(monkeypatch)
    page = FakePage()
    # p1: bar submit AND url fallback both fail -> outer handler continues;
    # p2 succeeds.
    page.goto_plan = [RuntimeError("boom"), RuntimeError("boom"), None]
    page.listing_queue = [[raw_card("11111111")]]
    rep = ns.run_skills_scan(FakeContext(page), "a", "pune", 6, 7, 2, 10)
    assert rep["jobs_scanned"] == 1


def test_run_skills_scan_close_failure_swallowed(monkeypatch):
    _tune_skills(monkeypatch)
    page = FakePage()
    page.listing_queue = [[]]
    page.close_fail = True
    rep = ns.run_skills_scan(FakeContext(page), "a", "pune", 6, 7, 1, 10)
    assert rep["jobs_scanned"] == 0  # empty page -> empty report, close ignored


# -- search-bar driving ----------------------------------------------------------------------------
def test_submit_searchbar_drives_bar_inputs(monkeypatch):
    _tune_skills(monkeypatch)
    page = FakePage()
    landed = ns.submit_searchbar(page, "C#, ASP.Net Core", "pune", 6)
    assert landed == page.url == "https://www.naukri.com/"
    assert (ns.SEARCHBAR["keywords"], "C#, ASP.Net Core") in page.fills
    assert (ns.SEARCHBAR["location"], "pune") in page.fills
    assert (ns.SEARCHBAR["experience"], "6 years") in page.fills
    assert ns.SEARCHBAR["search_btn"] in page.clicks
    assert "Enter" in page.keyboard.presses
    assert page.goto_urls == ["https://www.naukri.com/"]


def test_submit_searchbar_experience_fallback(monkeypatch):
    _tune_skills(monkeypatch)
    page = FakePage()
    page.click_plan = [None, RuntimeError("dropdown stuck")]
    landed = ns.submit_searchbar(page, "x", "pune", 6)
    assert landed == page.url  # dropdown skipped, typed search still submitted
    assert ns.SEARCHBAR["search_btn"] in page.clicks


def test_skills_scan_bar_failure_uses_url_fallback(monkeypatch):
    _tune_skills(monkeypatch)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111")]]
    page.selector_fail = True  # no suggestions, no cards -> submit raises
    rep = ns.run_skills_scan(FakeContext(page), "a", "pune", 6, 7, 1, 10)
    assert rep["jobs_scanned"] == 1  # fallback found the card, run survived
    assert any("/jobs?" in u for u in page.goto_urls)  # URL fallback was taken


def test_with_page_param_sets_page():
    assert ns.with_page_param("https://www.naukri.com/x?k=a", 3) == \
        "https://www.naukri.com/x?k=a&page=3"
    assert ns.with_page_param("https://www.naukri.com/x?k=a&page=1", 3).endswith("page=3")
