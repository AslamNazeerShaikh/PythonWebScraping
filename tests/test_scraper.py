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


# -- java-stack exclusion (pure-java jobs stay out of the Excel) -----------------
# Ports the title keyword/blocklist idea from ankitbaghel01's auto-apply
# runner (Node): filter by keywords before persisting/exporting. Rule here:
# a Java-stack signal (java/spring/selenium/gradle/...) excludes the job
# UNLESS a .NET anchor (c#/.net/asp.net/...) is also present.
def test_should_exclude_pure_java_stack():
    assert ns.should_exclude_java_job("Java Developer", ["Java", "Spring Boot"]) is True
    assert ns.should_exclude_java_job("Springboot Developer", ["Java", "J2EE"]) is True
    assert ns.should_exclude_java_job("Selenium Tester", ["Selenium", "TestNG"]) is True
    assert ns.should_exclude_java_job("Kotlin Engineer", ["Kotlin", "Android"]) is True
    assert ns.should_exclude_java_job("JAVA DEVELOPER", ["MAVEN", "Gradle"]) is True


def test_should_exclude_keeps_dotnet_anchored():
    assert ns.should_exclude_java_job("Sr java/.net Full Stack Developer",
                                      ["Java", "C#", "React.js"]) is False
    assert ns.should_exclude_java_job("Automation Test Engineer",
                                      ["Java", "Selenium", "C#"]) is False
    assert ns.should_exclude_java_job("Senior .NET Developer",
                                      ["C#", ".NET Core"]) is False
    assert ns.should_exclude_java_job("AI Engineer",
                                      ["C#", ".NET", "Python"]) is False


def test_should_exclude_ai_python_without_java():
    assert ns.should_exclude_java_job("AI Engineer",
                                      ["Python", "LangChain", "LLM"]) is False
    assert ns.should_exclude_java_job("AI/ML Developer",
                                      ["Python", "PyTorch"]) is False
    assert ns.should_exclude_java_job("Python Developer", ["Python", "Django"]) is False
    assert ns.should_exclude_java_job("Python Developer",
                                      ["Python", ".NET", "C#"]) is False


def test_should_exclude_ai_plus_java_without_dotnet():
    assert ns.should_exclude_java_job("Java Developer with AI",
                                      ["Java", "Spring Boot", "Python"]) is True
    assert ns.should_exclude_java_job("Forward Deployed Engineer",
                                      ["Java Backend", "Spring Boot", "AI/LLM"]) is True
    assert ns.should_exclude_java_job("Java Full Stack - AI",
                                      ["Java", "Spring", "generative ai"]) is True


def test_should_exclude_javascript_is_not_java():
    assert ns.should_exclude_java_job("Frontend Developer",
                                      ["JavaScript", "React"]) is False
    assert ns.should_exclude_java_job("Senior Software Engineer",
                                      ["Java Script", ".NET", "React"]) is False
    assert ns.should_exclude_java_job(".Net FSD", ["Angular", "JavaScript"]) is False


def test_should_exclude_checks_snippet_and_description():
    assert ns.should_exclude_java_job("Backend Developer", ["Python"],
                                      "rest apis", "must know Spring Boot") is True
    assert ns.should_exclude_java_job("Backend Developer", ["Python"],
                                      "hibernate experts wanted") is True
    assert ns.should_exclude_java_job(".NET Developer", ["C#"],
                                      "", "spring boot plus dotnet team") is False
    assert ns.should_exclude_java_job("Data Engineer", ["Pyspark", "SQL"],
                                      "night shift", "") is False
    assert ns.should_exclude_java_job("", [], "", "") is False


# -- relevance gate (Naukri fuzzy-search noise stays out of the Excel) -----------
# Lane 1 (AI) ∪ Lane 2 (.NET/full-stack): a posting must match an anchor in
# TITLE/SKILLS, or a *strong* term in the snippet — a bare "ai" in prose is
# the main noise path and must NOT qualify (spec §G1 truth table).
def test_should_exclude_irrelevant_job_drops_mixed_results():
    assert ns.should_exclude_irrelevant_job("Product Owner", ["Agile", "Jira"]) is True
    assert ns.should_exclude_irrelevant_job("Hardware Design Engineer", ["PCB"]) is True
    assert ns.should_exclude_irrelevant_job("Senior Identity Specialist",
                                            ["IAM", "OKTA"]) is True
    assert ns.should_exclude_irrelevant_job("Devops Engineer", ["AWS", "Terraform"]) is True
    # bare "ai" in prose ("training", "aided") must not qualify the job
    assert ns.should_exclude_irrelevant_job("Data Engineer", ["PySpark", "SQL"],
                                            "aided by technology and training") is True
    assert ns.should_exclude_irrelevant_job("", [], "") is True


def test_should_exclude_irrelevant_job_keeps_both_lanes():
    # Lane 1 — AI
    assert ns.should_exclude_irrelevant_job("AI Engineer", ["LLM", "RAG"]) is False
    assert ns.should_exclude_irrelevant_job("Gen AI Engineer",
                                            ["LangChain", "Pinecone"]) is False
    assert ns.should_exclude_irrelevant_job("MCP Integration Engineer") is False
    assert ns.should_exclude_irrelevant_job("Machine Learning Engineer") is False
    # strong term in the snippet rescues a generic title
    assert ns.should_exclude_irrelevant_job("Sr. SW Engineer", ["Python"],
                                            "python, ai & agentic automation") is False
    # Lane 2 — .NET / full stack
    assert ns.should_exclude_irrelevant_job("Senior .NET Developer", ["C#"]) is False
    assert ns.should_exclude_irrelevant_job("Full Stack Developer",
                                            ["React", "Microservices"]) is False
    assert ns.should_exclude_irrelevant_job("Software Engineer",
                                            [], "asp.net core web api") is False
    assert ns.should_exclude_irrelevant_job("Software Engineer",
                                            [], "must know microservices") is False


# -- pure-frontend gate (React/Angular-only postings stay out) -------------------
def test_should_exclude_frontend_job_pure_frontend():
    assert ns.should_exclude_frontend_job("React Developer", ["React", "Redux"]) is True
    assert ns.should_exclude_frontend_job("Frontend Engineer",
                                          ["JavaScript", "HTML", "CSS"]) is True
    assert ns.should_exclude_frontend_job("UI UX Designer", ["Figma"]) is True
    assert ns.should_exclude_frontend_job("Angular Developer",
                                          ["Angular", "TypeScript"],
                                          "build responsive UIs") is True


def test_should_exclude_frontend_job_keeps_hybrids():
    assert ns.should_exclude_frontend_job("Full Stack Developer",
                                          ["React", "C#", ".NET"]) is False
    assert ns.should_exclude_frontend_job("Fullstack JavaScript Engineer",
                                          ["Node", "Express", "MongoDB"]) is False
    assert ns.should_exclude_frontend_job("AI Engineer",
                                          ["Python", "React"]) is False
    assert ns.should_exclude_frontend_job("Senior .NET Developer", ["C#"]) is False
    assert ns.should_exclude_frontend_job("Python Backend Developer",
                                          ["Python", "Django", "SQL"]) is False


def test_job_should_exclude_wraps_job():
    from tests.conftest import make_job

    pure = make_job("11111111", title="Java Developer",
                    skills=["Java", "Spring Boot"],
                    snippet="spring boot java backend")
    assert ns.job_should_exclude(pure) is True
    mixed = make_job("22222222", title="Sr java/.net Developer",
                     skills=["Java", "C#"])
    assert ns.job_should_exclude(mixed) is False


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


def test_run_scrape_skips_pure_java_listing_card(monkeypatch):
    _tune(monkeypatch, enrich_details=False, max_pages_per_search=1)
    page = FakePage()
    java_card = raw_card("99999991", "Java Network Engineer")
    java_card["snippet"] = "spring boot networking team"  # relevant via "net", pure-Java
    mixed_card = raw_card("99999992", "Sr java/.net Full Stack Developer")
    mixed_card["snippet"] = "java plus c# dotnet team"  # Java signal + anchor -> kept
    page.listing_queue = [[raw_card("11111111"), java_card, mixed_card]]
    jobs = ns.run_scrape(FakeContext(page))
    assert sorted(j.job_id for j in jobs) == ["11111111", "99999992"]


def test_run_scrape_skips_unwanted_listing_cards(monkeypatch):
    _tune(monkeypatch, enrich_details=False, max_pages_per_search=1)
    page = FakePage()
    owner = raw_card("99999993", "Product Owner")
    owner["snippet"] = "roadmap prioritisation, stakeholders"  # no lane anchor
    frontend = raw_card("99999994", "React Developer")
    frontend["snippet"] = "javascript, html, css, responsive UIs"  # pure FE
    ai = raw_card("99999995", "AI Engineer")
    ai["snippet"] = "langchain, rag, mcp"  # Lane 1 — the old .NET-only gate
    # relevance check would have dropped it (spec: browser path fix)
    page.listing_queue = [[raw_card("11111111"), owner, frontend, ai]]
    jobs = ns.run_scrape(FakeContext(page))
    assert sorted(j.job_id for j in jobs) == ["11111111", "99999995"]


def test_run_scrape_excludes_java_revealed_by_enrichment(monkeypatch):
    _tune(monkeypatch, max_pages_per_search=1)
    page = FakePage()
    card = raw_card("11111111", "Fullstack Engineer (Angular)")
    card["snippet"] = "fullstack angular team"  # relevant, no Java signal yet
    page.listing_queue = [[card]]
    page.detail_result = {"skills": ["Java", "Spring Boot"]}  # detail reveals Java
    assert ns.run_scrape(FakeContext(page)) == []


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
            make_job("22222222", skills=["c#", "SQL"]),  # same company (Acme)
            make_job("33333333", company="Initech"),  # no skills
            make_job("44444444", company="Globex", skills=["C#"])]
    rep = ns.build_skills_report(jobs)  # default: distinct companies
    assert rep["jobs_scanned"] == 4 and rep["with_skills"] == 3
    assert rep["without_skills"] == 1  # card-only reads surface here, not silently
    assert rep["unique_skills"] == 3 and rep["companies_total"] == 3
    assert rep["count_mode"] == "companies"
    top = {t["skill"]: t for t in rep["top"]}
    assert top["C#"]["count"] == 2 and top["C#"]["pct"] == round(200 / 3, 1)
    assert top["C#"]["companies"] == [{"name": "Acme", "count": 2},
                                      {"name": "Globex", "count": 1}]
    assert top["SQL"] == {"skill": "SQL", "count": 1, "pct": round(100 / 3, 1),
                          "companies": [{"name": "Acme", "count": 1}]}
    assert len(rep["top"]) <= 30
    old = ns.build_skills_report(jobs, by_company=False)  # legacy: per posting
    assert old["count_mode"] == "postings" and old["companies_total"] == 3
    old_top = {t["skill"]: t for t in old["top"]}
    assert old_top["C#"]["count"] == 3 and old_top["C#"]["pct"] == 75.0
    assert old_top["C#"]["companies"] == [{"name": "Acme", "count": 2},
                                          {"name": "Globex", "count": 1}]


def test_build_skills_report_unknown_company():
    from tests.conftest import make_job

    rep = ns.build_skills_report([make_job("11111111", company="",
                                           skills=["Go"])])
    assert rep["top"][0]["companies"] == [{"name": "Unknown", "count": 1}]


def test_build_skills_report_empty():
    assert ns.build_skills_report([]) == {"jobs_scanned": 0, "with_skills": 0,
                                          "without_skills": 0,
                                          "unique_skills": 0,
                                          "companies_total": 0,
                                          "count_mode": "companies", "top": []}


def test_run_skills_scan_full_flow(monkeypatch):
    _tune_skills(monkeypatch)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111", skills=["C#"])],
                          [raw_card("22222222", skills=["C#", "SQL"]),
                           raw_card("11111111"),  # dup skipped
                           {"jobId": "1", "title": "AB", "url": "https://x"}]]  # invalid dropped
    monkeypatch.setattr(ns, "_click_next_page", lambda p: True)
    seen: list = []
    rep = ns.run_skills_scan(FakeContext(page), "asp.net core", "pune",
                             6, 7, 2, 10, by_company=False,
                             on_progress=seen.append)
    assert rep["jobs_scanned"] == 2 and rep["unique_skills"] == 2
    assert [s["stage"] for s in seen] == ["search", "search", "done"]
    # Page 1 is a direct URL; page 2 was the already-clicked Next view.
    assert len(page.goto_urls) == 1
    assert "-jobs-in-pune?" in page.goto_urls[0]
    assert all("/job-listings-" not in u for u in page.goto_urls)
    top = {t["skill"]: t["count"] for t in rep["top"]}
    assert top == {"C#": 2, "SQL": 1}        # one vote per posting


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
    page.listing_queue = [[raw_card("11111111", skills=["C#"])],
                          [raw_card("22222222", skills=["SQL"])]]
    monkeypatch.setattr(ns, "_click_next_page", lambda p: True)
    calls = [0]

    def _stop():
        calls[0] += 1
        return calls[0] > 3  # stop after page 2 is read, before page 3

    seen: list = []
    rep = ns.run_skills_scan(FakeContext(page), "a", "pune", 6, 7, 3,
                             10, should_stop=_stop, on_progress=seen.append)
    assert rep["jobs_scanned"] == 2  # both pages done; page 3 never clicked
    assert [s["stage"] for s in seen] == ["search", "search", "done"]


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
    assert (ns.SEARCH_CANDIDATES["keywords"][0], "C#, ASP.Net Core") in page.fills
    assert (ns.SEARCH_CANDIDATES["location"][0], "pune") in page.fills
    assert "Enter" in page.keyboard.presses
    assert page.goto_urls == ["https://www.naukri.com/"]


def test_submit_searchbar_experience_fallback(monkeypatch):
    _tune_skills(monkeypatch)
    page = FakePage()
    page.click_plan = [RuntimeError("dropdown stuck")]
    landed = ns.submit_searchbar(page, "x", "pune", 6)
    assert landed == page.url  # dropdown skipped, typed search still submitted


def test_skills_scan_bar_failure_uses_url_fallback(monkeypatch):
    _tune_skills(monkeypatch)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111")]]
    page.selector_fail = True  # no suggestions, no cards -> submit raises
    rep = ns.run_skills_scan(FakeContext(page), "a", "pune", 6, 7, 1, 10)
    assert rep["jobs_scanned"] == 1  # fallback found the card, run survived
    assert any("-jobs-in-pune?" in u for u in page.goto_urls)  # slug fallback taken


def test_slugify_matches_manual_search():
    # Ground truth: the user's own manual Naukri URL slug, character-exact.
    assert ns.slugify_keywords(
        "C#, ASP.Net Core, .NET Application Developer, "
        "Full Stack .Net Developer, Net Development, .Net Core") == \
        "c-sharp-asp-dot-net-core-dot-net-application-developer-\
full-stack-dot-net-developer-net-development-dot-net-core"


def test_build_slug_search_url_mirrors_manual():
    url = ns.build_slug_search_url("C#, ASP.Net Core", "pune", 6, 7, 1)
    assert url.startswith("https://www.naukri.com/c-sharp-asp-dot-net-core-jobs-in-pune?")
    assert "k=C%23%2C+ASP.Net+Core" in url and "l=pune" in url
    assert "experience=6" in url and "jobAge=7" in url
    p3 = ns.build_slug_search_url("C#, ASP.Net Core", "pune", 6, 7, 3)
    assert "-jobs-in-pune-3?" in p3 and "jobAge=7" in p3  # path paging, filters kept


def test_submit_searchbar_resolves_variant_inputs(monkeypatch):
    _tune_skills(monkeypatch)
    page = FakePage()
    # Bot-variant homepage: class selectors absent, semantic ones present.
    page.query_counts = [0, 0, 3, 0, 2, 0, 0, 1, 0, 1, 1]
    page.option_texts = ["Pune", "Mumbai", "6 years"]
    landed = ns.submit_searchbar(page, "C#, x", "pune", 6)
    assert landed == page.url
    cands = ns.SEARCH_CANDIDATES
    assert (cands["keywords"][2], "C#, x") in page.fills
    assert (cands["location"][1], "pune") in page.fills
    assert cands["location_option"][1] in str(page.evals)  # indexed option click ran
    assert "search_btn" not in cands  # submit is Enter-based, no button


def test_submit_searchbar_missing_option_keeps_typed(monkeypatch):
    _tune_skills(monkeypatch)
    page = FakePage()
    page.query_counts = [1, 1, 1, 1, 0, 0]  # inputs found, no suggestion nodes
    landed = ns.submit_searchbar(page, "x", "pune", 6)
    assert landed == page.url  # suggestion skipped, typed search submitted


def test_submit_searchbar_absent_bar_raises(monkeypatch):
    import pytest as _pytest

    _tune_skills(monkeypatch)
    page = FakePage()
    page.query_counts = [0] * 13  # no known inputs anywhere
    with _pytest.raises(RuntimeError, match="without known inputs"):
        ns.submit_searchbar(page, "x", "pune", 6)
    assert page.fills == []  # failed fast: nothing typed anywhere


def test_pick_option_exact_substring_and_miss():
    page = FakePage()
    page.query_counts = [1]
    page.option_texts = ["Fresher (less than 1 year)", "6 years", "16 years"]
    assert ns._pick_option(page, ["li"], "6 years") is True  # exact beats 16
    assert "[1].click()" in str(page.evals)
    page2 = FakePage()
    page2.query_counts = [1]
    page2.option_texts = ["16 years"]
    assert ns._pick_option(page2, ["li"], "6 years") is True  # substring fallback
    page3 = FakePage()
    page3.query_counts = [1]
    page3.option_texts = ["Fresher"]
    assert ns._pick_option(page3, ["li"], "6 years") is False
    assert ns._pick_option(page3, ["li"], "") is False
    page4 = FakePage()
    page4.query_counts = [0]
    assert ns._pick_option(page4, ["li"], "6 years") is False  # no nodes


# -- SRP card key skills + native pagination (2026-10-26 fix) -----------------
def test_listing_js_reads_card_key_skills_and_posted_date():
    js = ns.LISTING_EXTRACT_JS
    assert "ul.tags-gt li" in js and "li.tag-li" in js
    assert ".keyskill > span" in js
    assert "span.job-post-day" in js
    assert "skills," in js                      # pushed with every card


def test_build_slug_search_url_multi_location_uses_first_city_in_path():
    url = ns.build_slug_search_url(
        "C#, ASP.Net Core", "pune, hyderabad, bangalore", 6, 7, 2)
    assert "-jobs-in-pune-2?" in url
    assert "l=pune%2C+hyderabad%2C+bangalore" in url
    assert "k=C%23%2C+ASP.Net+Core" in url
    assert "experience=6" in url and "jobAge=7" in url


def test_build_slug_search_url_empty_location_falls_back_to_india():
    url = ns.build_slug_search_url("C#", "", 6, 7, 1)
    assert "-jobs-in-india?" in url


def test_click_next_page_waits_for_range_change(monkeypatch):
    page = FakePage()
    page.js_returns["/*next-page*/"] = True
    states = iter([{"text": "1 - 20 of 442"},
                   {"text": "21 - 40 of 442"}])
    monkeypatch.setattr(ns, "_list_state", lambda p: next(states))
    assert ns._click_next_page(page) is True
    assert page.timeouts == [ns.NEXT_PAGE_POLL_MS]


def test_click_next_page_returns_false_without_enabled_control():
    page = FakePage()
    page.js_returns["/*next-page*/"] = False
    assert ns._click_next_page(page) is False
    assert page.timeouts == []


def test_click_next_page_and_list_state_survive_detached_dom():
    class _Boom(FakePage):
        def evaluate(self, js):  # type: ignore[override]
            raise RuntimeError("execution context destroyed")

    assert ns._list_state(_Boom()) == {}
    assert ns._click_next_page(_Boom()) is False


def test_click_next_page_times_out_when_range_never_changes(monkeypatch):
    page = FakePage()
    page.js_returns["/*next-page*/"] = True
    monkeypatch.setattr(ns, "_list_state", lambda p: {"text": "same"})
    assert ns._click_next_page(page, timeout_ms=1000) is False
    assert len(page.timeouts) == 2      # 1000 / NEXT_PAGE_POLL_MS


def test_run_skills_scan_stops_when_next_page_is_absent(monkeypatch):
    _tune_skills(monkeypatch)
    page = FakePage()
    page.listing_queue = [[raw_card("11111111", skills=["C#"])]]
    monkeypatch.setattr(ns, "_click_next_page", lambda p: False)
    seen: list = []
    rep = ns.run_skills_scan(FakeContext(page), "a", "pune", 6, 7, 2, 10,
                             on_progress=seen.append)
    assert rep["jobs_scanned"] == 1
    assert [s["stage"] for s in seen] == ["search", "done"]


def test_run_skills_scan_zero_pages_returns_empty_report():
    page = FakePage()
    rep = ns.run_skills_scan(FakeContext(page), "a", "pune", 6, 7, 0, 10)
    assert rep["jobs_scanned"] == 0 and rep["top"] == []
    assert page.goto_urls == []
