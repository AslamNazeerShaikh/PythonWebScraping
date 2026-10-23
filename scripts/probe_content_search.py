#!/usr/bin/env python3
"""Dev probe: what does LinkedIn content-search actually render?

Diagnostic only (R3-MCP style dev probe): opens ONE search URL in the
persistent profile and reports login state, landed URL, main text, and
candidate card-selector counts. Used to fix CONTENT_EXTRACT_JS selectors
when the collector returns 0 emails. Usage:

    .venv/bin/python scripts/probe_content_search.py "@ltm.com"
    .venv/bin/python scripts/probe_content_search.py --login  # one-time sign-in
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root

from playwright.sync_api import sync_playwright  # noqa: E402

from src.config import SETTINGS
from src.linkedin_email_scraper import (
    CONTENT_EXTRACT_JS,
    SETTLE_MS,
    build_content_search_url,
)
from src.stealth_browser import launch_context

PROBE_JS = """
() => {
  const count = (sel) => document.querySelectorAll(sel).length;
  const main = document.querySelector('main');
  return {
    url: location.href,
    loggedIn: !!(document.querySelector('header.global-nav, .global-nav')) &&
              !/\\/login|authwall|checkpoint/.test(location.href),
    mainTextLen: main ? (main.innerText || '').length : -1,
    mainTextHead: main ? (main.innerText || '').slice(0, 800)
                       : document.body.innerText.slice(0, 400),
    counts: {
      'div.feed-shared-update-v2': count('div.feed-shared-update-v2'),
      'li.reusable-search__result-container':
        count('li.reusable-search__result-container'),
      '[data-urn]': count('[data-urn]'),
      '.feed-shared-text': count('.feed-shared-text'),
      '.feed-shared-update-v2__description':
        count('.feed-shared-update-v2__description'),
      '.update-components-text': count('.update-components-text'),
      'li.research-entity-lockup-result':
        count('li.research-entity-lockup-result'),
      '.entity-result': count('.entity-result'),
      'ul.reusable-search__entity-result-list > li':
        count('ul.reusable-search__entity-result-list > li'),
      'div.search-results-container': count('div.search-results-container'),
      'main article': count('main article'),
      'main li': count('main li'),
    },
    cardsJs: ((%s)()).length,
    cardsJsFirst: ((%s)()).slice(0, 2),
  };
}
""" % (CONTENT_EXTRACT_JS, CONTENT_EXTRACT_JS)


def _login_wait(timeout_s: int = 600) -> int:
    """Open LinkedIn headful; wait for the human to sign in (max 10 min).

    One-time step — the persistent profile (``.pw-profile``) keeps the
    session for every later ``collect-emails`` run. Never automates the
    credentials: the human types them, this only polls for success.
    """
    import time

    from src.linkedin_email_scraper import _on_login_wall

    with sync_playwright() as p:
        ctx = launch_context(p)
        try:
            page = ctx.new_page()
            page.goto("https://www.linkedin.com/feed/",
                      wait_until="domcontentloaded")
            print(f"LOG IN IN THE OPENED WINDOW (waiting up to {timeout_s}s)…",
                  flush=True)
            deadline = time.time() + timeout_s
            while time.time() < deadline:
                page.wait_for_timeout(2000)
                if not _on_login_wall(page) and page.evaluate(
                        "!!document.querySelector('header.global-nav, .global-nav')"):
                    print("LOGGED_IN_OK — session persisted; closing.",
                          flush=True)
                    return 0
            print("LOGIN_TIMEOUT — try again.", flush=True)
            return 1
        finally:
            ctx.close()


def main() -> int:
    if "--login" in sys.argv:
        return _login_wait()
    keyword = sys.argv[1] if len(sys.argv) > 1 else "@ltm.com"
    url = build_content_search_url(keyword, SETTINGS.email_date_facet)
    with sync_playwright() as p:
        ctx = launch_context(p)
        try:
            page = ctx.new_page()
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(SETTLE_MS)
            page.wait_for_timeout(2000)  # extra SDUI settle for the probe
            info = page.evaluate(PROBE_JS)
        finally:
            ctx.close()
    for key, value in info.items():
        print(f"== {key} ==")
        if isinstance(value, dict):
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
