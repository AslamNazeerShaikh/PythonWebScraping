"""Shared test fixtures: isolated DB, sample jobs, Playwright fakes.

The fakes (FakePage/FakeContext/…) let us exercise the scraper, browser
launcher, and CLI at 100% coverage WITHOUT a real browser or network.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.config import SETTINGS
from src.models import Job


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------
def make_job(job_id: str = "12345678", **over) -> Job:
    """Build a valid Job with sensible defaults; ``over`` overrides fields."""
    base = dict(
        job_id=job_id,
        title="Senior .NET Developer",
        company="Acme",
        location="Pune",
        search_location="pune",
        experience="6-8 Yrs",
        salary="10-15 Lacs",
        posted="2 days ago",
        url=f"https://www.naukri.com/job-listings-dev-{job_id}",
        apply_url=f"https://www.naukri.com/job-listings-dev-{job_id}",
        snippet="asp.net core c# fullstack",
    )
    base.update(over)
    return Job(**base)


def raw_card(job_id: str = "12345678", title: str = "Senior .NET Developer") -> dict:
    """Build an in-page-JS-style raw card dict (camelCase keys)."""
    url = f"https://www.naukri.com/job-listings-dev-{job_id}"
    return {"jobId": job_id, "title": title, "company": "Acme",
            "location": "Pune", "experience": "6-8 Yrs", "salary": "10 Lacs",
            "posted": "today", "snippet": "asp.net core c#", "url": url}


# ---------------------------------------------------------------------------
# Isolated database (tmp SQLite file; engine globals reset before/after)
# ---------------------------------------------------------------------------
@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """Point SETTINGS.database_url at a tmp file and give a clean engine."""
    import src.db as dbmod

    monkeypatch.setattr(
        SETTINGS, "database_url", f"sqlite:///{tmp_path / 'test.db'}")
    dbmod._engine = None
    dbmod._SessionFactory = None
    dbmod.init_db()
    yield dbmod
    if dbmod._engine is not None:
        dbmod._engine.dispose()
    dbmod._engine = None
    dbmod._SessionFactory = None


# ---------------------------------------------------------------------------
# Playwright fakes — scriptable stand-ins for Page / Context / browsers
# ---------------------------------------------------------------------------
class FakeRoute:
    """Captures route.abort() / route.continue_() decisions for assertions."""

    def __init__(self) -> None:
        self.aborted = False
        self.continued = False

    def abort(self) -> None:
        self.aborted = True

    def continue_(self) -> None:
        self.continued = True


class FakeMouse:
    """Mouse double; ``fail=True`` makes every action raise (fallback paths)."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.wheeled: list[int] = []
        self.moved: list[tuple[int, int]] = []

    def wheel(self, dx: int, dy: int) -> None:
        if self.fail:
            raise RuntimeError("no mouse")
        self.wheeled.append(dy)

    def move(self, x: int, y: int) -> None:
        if self.fail:
            raise RuntimeError("no mouse")
        self.moved.append((x, y))


class FakePage:
    """Scriptable Page fake.

    Attributes to set per-test:
        listing_queue: lists popped per LISTING evaluate call.
        detail_result: dict returned for DETAIL evaluate calls.
        body_text / anchor_count / page_title: bot-wall inputs.
        html: returned by content() (or raises if content_fail).
        selector_fail: wait_for_selector raises when True.
        goto_plan: list of exceptions (None = success) consumed per goto.
        close_fail / mouse_fail: failure injection flags.
    """

    LISTING_MARK = "const out = [];"
    DETAIL_MARK = "applyUrl"

    def __init__(self) -> None:
        self.listing_queue: list[list[dict]] = []
        self.detail_result: dict = {}
        self.body_text = "some normal page content"
        self.anchor_count = 1
        self.page_title = "Jobs"
        self.html = "<html><body>jobs</body></html>"
        self.content_fail = False
        self.selector_fail = False
        self.goto_plan: list = []
        self.goto_urls: list[str] = []
        self.close_fail = False
        self.mouse = FakeMouse()
        self.timeouts: list[int] = []

    # -- navigation ------------------------------------------------------
    def goto(self, url: str, wait_until: str = "domcontentloaded"):
        self.goto_urls.append(url)
        if self.goto_plan:
            exc = self.goto_plan.pop(0)
            if exc is not None:
                raise exc
        return {"ok": True}

    # -- waiting / sensing -----------------------------------------------
    def wait_for_timeout(self, ms: int) -> None:
        self.timeouts.append(ms)

    def wait_for_selector(self, sel: str, timeout: int = 0):
        if self.selector_fail:
            raise TimeoutError("no cards")
        return True

    def title(self) -> str:
        return self.page_title

    def content(self) -> str:
        if self.content_fail:
            raise RuntimeError("no content")
        return self.html

    # -- JS evaluation (dispatches on markers in the real query strings) --
    def evaluate(self, js: str):
        if 'innerText.slice(0,4000)' in js:
            return self.body_text
        if js.lstrip().startswith('document.querySelectorAll'):
            return self.anchor_count  # bot-wall anchor probe (exact-match first:
            # the listing/detail scripts also mention querySelectorAll/length)
        if self.LISTING_MARK in js:
            return self.listing_queue.pop(0) if self.listing_queue else []
        if self.DETAIL_MARK in js:
            if isinstance(self.detail_result, Exception):
                raise self.detail_result
            return self.detail_result
        if 'window.scrollBy' in js:
            return True
        return None

    def close(self) -> None:
        if self.close_fail:
            raise RuntimeError("close failed")


class FakeContext:
    """Context fake: serves a preset page, records route handlers."""

    def __init__(self, page: FakePage | None = None) -> None:
        self.page = page or FakePage()
        self.routes: list = []
        self.closed = False

    def new_page(self) -> FakePage:
        return self.page

    def route(self, pattern: str, handler) -> None:  # type: ignore[no-untyped-def]
        self.routes.append((pattern, handler))

    def add_init_script(self, js: str) -> None:
        pass

    def set_default_navigation_timeout(self, ms: int) -> None:
        pass

    def set_default_timeout(self, ms: int) -> None:
        pass

    def close(self) -> None:
        self.closed = True


class FakeBrowserType:
    """Browser-type fake: returns contexts or raises (fallback testing)."""

    def __init__(self, contexts: list | None = None, error: Exception | None = None) -> None:
        self.contexts = contexts or []
        self.error = error
        self.kwargs: list[dict] = []

    def launch_persistent_context(self, **kwargs):  # type: ignore[no-untyped-def]
        self.kwargs.append(kwargs)
        if self.error is not None:
            raise self.error
        if self.contexts:
            return self.contexts.pop(0)
        return FakeContext()


def fake_playwright(firefox_ctxs=None, firefox_err=None,  # type: ignore[no-untyped-def]
                    chromium_ctxs=None, chromium_err=None):
    """Build a ``p`` object mimicking playwright's firefox/chromium attrs."""
    return SimpleNamespace(
        firefox=FakeBrowserType(contexts=list(firefox_ctxs or []), error=firefox_err),
        chromium=FakeBrowserType(contexts=list(chromium_ctxs or []), error=chromium_err),
    )
