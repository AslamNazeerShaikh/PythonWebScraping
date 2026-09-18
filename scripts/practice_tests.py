"""Live practice suite — implements docs/TESTING.md Tests 1-7 on sandboxes.

Runs the REAL stack (launch_context: Chromium + uBO Lite + stealth) against
sites built for scraping practice. Each test asserts its pass criteria and
the run ends with a report (exit 0 = all green).

    .venv/bin/python scripts/practice_tests.py [--quick]

--quick: Books crawl limited to 3 pages (smoke); default crawls all 50.
Results: output/practice/report.json (gitignored).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright  # noqa: E402
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError  # noqa: E402
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed  # noqa: E402

from src.stealth_browser import launch_context  # noqa: E402

BOOKS = "https://books.toscrape.com/catalogue/page-{}.html"
QUOTES = "https://quotes.toscrape.com"
HTTPBIN = "https://httpbin.org"

BOOK_EXTRACT_JS = """
() => Array.from(document.querySelectorAll('article.product_pod')).map(card => ({
  title: card.querySelector('h3 a').getAttribute('title'),
  price: (card.querySelector('.price_color') || {}).innerText || '',
  rating: (card.querySelector('.star-rating') || {}).className || '',
  availability: ((card.querySelector('.instock') || {}).innerText || '').trim(),
  url: card.querySelector('h3 a').href,
}))
"""

QUOTE_EXTRACT_JS = """
() => Array.from(document.querySelectorAll('.quote')).map(q => ({
  text: q.querySelector('.text').innerText,
  author: q.querySelector('.author').innerText,
}))
"""


class Reporter:
    """Collects (name, passed, detail) rows and prints the final report."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, bool, str]] = []

    def check(self, name: str, passed: bool, detail: str) -> None:
        self.rows.append((name, passed, detail))
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}", flush=True)

    def all_green(self) -> bool:
        return all(ok for _, ok, _ in self.rows)


# ---------------------------------------------------------------------------
# Tests 1-3: Books to Scrape — extraction, pagination, DB dedupe
# ---------------------------------------------------------------------------
def crawl_books(page, pages: int):  # type: ignore[no-untyped-def]
    """Crawl N Books pages; returns list of book dicts."""
    books: list[dict] = []
    for n in range(1, pages + 1):
        page.goto(BOOKS.format(n), wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector("article.product_pod", timeout=15000)
        books.extend(page.evaluate(BOOK_EXTRACT_JS))
        page.wait_for_timeout(400)  # polite even on sandboxes
    return books


def store_books(db_path: Path, books: list[dict]) -> tuple[int, int]:
    """Upsert books by URL; returns (new, total) — proves dedupe (Test 3)."""
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE IF NOT EXISTS books(url TEXT PRIMARY KEY, title TEXT,"
                " price TEXT, rating TEXT, availability TEXT)")
    new = 0
    for b in books:
        cur = con.execute("INSERT OR IGNORE INTO books VALUES(?,?,?,?,?)",
                          (b["url"], b["title"], b["price"], b["rating"],
                           b["availability"]))
        new += cur.rowcount
    con.commit()
    total = con.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    con.close()
    return new, total


# ---------------------------------------------------------------------------
# Test 7 helpers: failure taxonomy with tenacity (transient-only retries)
# ---------------------------------------------------------------------------
# Playwright timeouts raise playwright's TimeoutError, NOT the builtin —
# catching the wrong one (as v1 did) silently disables all retries.
_TRANSIENT = (TimeoutError, PlaywrightTimeoutError)


@retry(retry=retry_if_exception_type(_TRANSIENT),
       stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
def _get_with_retry(page, url: str, timeout_ms: int):  # type: ignore[no-untyped-def]
    resp = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    if resp is None:
        raise TimeoutError("no response (timeout)")
    return resp


def main() -> int:
    ap = argparse.ArgumentParser(description="TESTING.md live practice suite.")
    ap.add_argument("--quick", action="store_true", help="3 book pages (smoke)")
    ap.add_argument("--out", default="output/practice")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rep = Reporter()
    book_pages = 3 if args.quick else 50

    with sync_playwright() as p:
        context = launch_context(p)
        try:
            page = context.new_page()

            # -- Test 1: basic extraction (Books p1) -----------------------
            page.goto(BOOKS.format(1), wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("article.product_pod", timeout=15000)
            first = page.evaluate(BOOK_EXTRACT_JS)
            rep.check("T1 basic extraction", len(first) == 20
                      and all(b["title"] and b["price"] for b in first),
                      f"{len(first)} books on page 1 with title+price")

            # -- Test 2: full pagination -----------------------------------
            books = crawl_books(page, book_pages)
            expect = book_pages * 20
            rep.check("T2 pagination", len(books) == expect,
                      f"collected {len(books)}/{expect} books")

            # -- Test 3: DB dedupe (insert twice) ---------------------------
            db_path = out / "practice.db"
            if db_path.exists():
                db_path.unlink()
            new1, total1 = store_books(db_path, books)
            new2, total2 = store_books(db_path, books)
            rep.check("T3 dedupe", new1 == len(books) and new2 == 0
                      and total2 == len(books),
                      f"run1 +{new1}, run2 +{new2} (total {total2})")

            # -- Test 4: JS rendering (Quotes /js/) --------------------------
            page.goto(f"{QUOTES}/js/", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector(".quote", timeout=15000)
            js_quotes = page.evaluate(QUOTE_EXTRACT_JS)
            rep.check("T4 JS rendering", len(js_quotes) == 10
                      and all(q["author"] for q in js_quotes),
                      f"{len(js_quotes)} JS-rendered quotes with authors")

            # -- Test 5: infinite scroll (terminate, don't loop forever) -----
            page.goto(f"{QUOTES}/scroll", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector(".quote", timeout=15000)
            last, stable_rounds = -1, 0
            for _ in range(30):  # hard cap: termination guaranteed
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(900)
                n = page.evaluate("document.querySelectorAll('.quote').length")
                if n == last:
                    stable_rounds += 1
                    if stable_rounds >= 3:
                        break
                else:
                    stable_rounds, last = 0, n
            rep.check("T5 infinite scroll", last > 10,
                      f"settled at {last} quotes (stable x{stable_rounds})")

            # -- Test 6: login + session --------------------------------------
            page.goto(f"{QUOTES}/login", wait_until="domcontentloaded", timeout=30000)
            page.fill('input[name="username"]', "admin")
            page.fill('input[name="password"]', "admin")
            page.click('input[type="submit"]')
            page.wait_for_timeout(1500)
            body = page.evaluate("document.body.innerText")
            rep.check("T6 login/session", "Logout" in body,
                      "authenticated (Logout link present), session held")

            # -- Test 7: failure taxonomy (HTTPBin) ------------------------------
            # NOTE: this Chromium makes page.goto() THROW on HTTP error
            # statuses, so classification uses page.request (returns status,
            # never throws); the tenacity retry path uses a goto timeout.
            r200 = page.request.get(f"{HTTPBIN}/status/200", timeout=15000)
            ok200 = r200.status == 200  # process
            r404 = page.request.get(f"{HTTPBIN}/status/404", timeout=15000)
            ok404 = r404.status == 404  # skip, log, continue (no retry)
            tries500 = 0  # 500 = transient: bounded retries, then abort page
            for _ in range(3):
                tries500 += 1
                if page.request.get(f"{HTTPBIN}/status/500",
                                    timeout=15000).status != 500:
                    break
            ok500 = tries500 == 3
            # Retry path proven via guaranteed timeout: /delay/10 with a 2s
            # cap -> 3 attempts, then abort (elapsed >= ~4s proves retries ran).
            t0 = time.time()
            try:
                _get_with_retry(page, f"{HTTPBIN}/delay/10", 2000)
                ok_timeout = False
            except _TRANSIENT:
                ok_timeout = time.time() - t0 >= 4  # 3 attempts x ~2s waits
            r429 = page.request.get(f"{HTTPBIN}/status/429", timeout=15000)
            ok429 = r429.status == 429  # observed -> back off / stop, not hammer
            rep.check("T7 failures",
                      ok200 and ok404 and ok500 and ok_timeout and ok429,
                      f"200 ok={ok200}, 404 skip={ok404}, 500 retried-x3={ok500}, "
                      f"timeout retried-3x-then-abort={ok_timeout}, 429 seen={ok429}")

            page.close()
        finally:
            context.close()

    report = {"at": datetime.now().isoformat(), "quick": args.quick,
              "results": [{"test": n, "pass": ok, "detail": d}
                          for n, ok, d in rep.rows]}
    (out / "report.json").write_text(json.dumps(report, indent=2))
    print(f"\n{'ALL GREEN' if rep.all_green() else 'FAILURES PRESENT'} "
          f"({sum(1 for _, ok, _ in rep.rows if ok)}/{len(rep.rows)})")
    return 0 if rep.all_green() else 1


if __name__ == "__main__":
    raise SystemExit(main())
