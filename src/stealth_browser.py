"""Stealth Chromium launcher: persistent profile + uBlock Origin Lite.

Stack (Chrome-only by decision):
    Playwright -> Chromium (persistent profile) -> uBOL (unpacked MV3) + site.

Layers:
    1. Persistent profile (``.pw-profile-chromium/``): cookies/history survive,
       less bot-like than fresh incognito; uBOL's settings persist too.
    2. uBlock Origin Lite (``UBLOCK_UNPACKED_DIR``, default
       ``vendor/ubol-chrome``): real MV3 content blocking via
       declarativeNetRequest — verified live (13/13 tracker/ad requests
       ``ERR_BLOCKED_BY_CLIENT`` on forbes.com). Loaded via
       ``--load-extension`` in HEADED mode only: headless-shell cannot load
       extensions, so headless runs skip it (fallback blocker covers them).
    3. Fallback request-blocker (``ADBLOCK_FALLBACK``): aborts known ad/tracker
       hosts even when uBOL is absent. Always on — harmless duplication when
       uBOL already blocked the request.
    4. Stealth init script: hides ``webdriver``, plugins stub, ``chrome``
       stub — measured live (Veil 23/23 human, BrowserScan 100 genuine).
    5. Hardened prefs: tracking protection, DNT, no WebRTC/geo leaks.

We do NOT bypass CAPTCHAs — on bot-walls we pause for manual solve.
"""
from __future__ import annotations

import random
import time
from pathlib import Path

from playwright.sync_api import BrowserContext, Playwright, sync_playwright

from .config import SETTINGS

# --- Minimal tracker/ad host blocklist (safety net under uBOL) ---
BLOCKED_HOSTS = (
    "doubleclick.net",
    "googlesyndication.com",
    "google-analytics.com",
    "googletagmanager.com",
    "googletagservices.com",
    "adservice.google.com",
    "ads.yahoo.com",
    "amazon-adsystem.com",
    "criteo.com",
    "outbrain.com",
    "taboola.com",
    "facebook.net",
    "hotjar.com",
    "fullstory.com",
    "mixpanel.com",
    "segment.io",
)

STEALTH_INIT_JS = """
() => {
  // webdriver flag
  Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
  // plugins
  Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
  // NOTE: navigator.languages is intentionally NOT overridden — Playwright's
  // `locale` already sets it, and a stub here contradicts the Worker scope
  // (BrowserScan flagged exactly this inconsistency).
  // chrome stub (many detectors check window.chrome)
  if (!window.chrome) { window.chrome = { runtime: {} }; }
  // permissions
  const origQuery = window.navigator.permissions && window.navigator.permissions.query;
  if (origQuery) {
    window.navigator.permissions.query = (p) =>
      p && p.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission })
        : origQuery(p);
  }
  // deviceMemory hint (Chromium ignores the redefine — property is
  // non-configurable — so the genuine value shows; kept for consistency).
  try {
    Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
  } catch (e) { /* genuine value stays: consistency beats stubbing */ }
}
"""


def human_pause(a: float | None = None, b: float | None = None) -> None:
    """Sleep a random politeness interval (defaults: SETTINGS min/max delay).

    Randomised — not fixed — so inter-request timing looks human and stays
    gentle on target servers. Pass ``(0, 0)`` in tests to skip waiting.
    """
    lo = a if a is not None else SETTINGS.min_delay_s
    hi = b if b is not None else SETTINGS.max_delay_s
    time.sleep(random.uniform(lo, hi))


def _maybe_block_ads(context: BrowserContext) -> None:
    """Install the fallback tracker/ad request-blocker (unless disabled).

    Aborts requests to known ad/tracker hosts (see BLOCKED_HOSTS) plus
    pixel/tracker media. Fewer third parties = fewer fingerprinting vectors
    AND faster page loads. Skipped entirely when ADBLOCK_FALLBACK=false.
    """
    if not SETTINGS.adblock_fallback:
        return

    def _route(route, request):  # type: ignore[no-untyped-def]
        url = request.url.lower()
        if any(h in url for h in BLOCKED_HOSTS):
            return route.abort()
        if request.resource_type in ("image", "media", "font"):
            if "pixel" in url or "track" in url or "beacon" in url:
                return route.abort()
        return route.continue_()

    context.route("**/*", _route)
    print("[privacy] Fallback request-blocker enabled.")


def _extension_args() -> list[str]:
    """Build ``--load-extension`` args for uBOL (headed mode only).

    Headless-shell cannot load extensions — requesting it there fails the
    launch — so headless runs rely on the fallback blocker instead. Returns
    ``[]`` with an explanatory note when uBOL is unavailable or unusable.
    """
    unpacked = (SETTINGS.ublock_unpacked_dir or "").strip()
    if not unpacked:
        print("[ublock] UBLOCK_UNPACKED_DIR not set — using fallback blocker. "
              "Run vendor/download-ubol.sh to fetch uBO Lite.")
        return []
    if SETTINGS.headless:
        print("[ublock] Headless mode: extensions unsupported by headless-shell; "
              "using fallback blocker. Run headed once for full uBO Lite.")
        return []
    if not Path(unpacked).expanduser().is_dir():
        print(f"[ublock] Not a directory: {unpacked} — using fallback blocker.")
        return []
    print(f"[ublock] Loading unpacked uBO Lite (chromium): {unpacked}")
    return [
        f"--disable-extensions-except={unpacked}",
        f"--load-extension={unpacked}",
    ]


def _launch_chromium(p: Playwright) -> BrowserContext:
    """Launch persistent Chromium with stealth defaults + uBO Lite.

    Own ``*-chromium`` profile dir, stealth init script, fallback blocker,
    ``--disable-blink-features=AutomationControlled``, and uBOL when headed.
    """
    profile = Path(str(SETTINGS.user_data_dir) + "-chromium")
    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--no-first-run",
        "--no-default-browser-check",
        *_extension_args(),
    ]
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(profile),
        headless=SETTINGS.headless,
        slow_mo=SETTINGS.slow_mo_ms,
        viewport={"width": SETTINGS.viewport_w, "height": SETTINGS.viewport_h},
        locale=SETTINGS.locale,
        timezone_id=SETTINGS.timezone,
        accept_downloads=True,
        args=args,
        # Hide the automation flag; keep headless-shell compatible.
        chromium_sandbox=False,
        ignore_default_args=["--enable-automation"],
    )
    context.set_default_navigation_timeout(SETTINGS.nav_timeout_ms)
    context.set_default_timeout(20000)
    context.add_init_script(STEALTH_INIT_JS)
    _maybe_block_ads(context)
    print(f"[browser] Chromium persistent profile ready | "
          f"headless={SETTINGS.headless} locale={SETTINGS.locale}")
    return context


def launch_context(p: Playwright) -> BrowserContext:
    """Launch the browser (Chromium-only stack).

    Raises:
        ValueError: If ``BROWSER`` names anything but ``chromium`` — Firefox
            was dropped: no Firefox engine starts in this environment
            (stable 155 and Nightly both die on profile spawn).
    """
    want = (SETTINGS.browser or "chromium").lower()
    if want != "chromium":
        raise ValueError(
            f"Unsupported BROWSER={SETTINGS.browser!r}: this project is "
            "Chrome-only (firefox engines fail to launch here).")
    return _launch_chromium(p)


def launch_playwright() -> tuple[object, BrowserContext]:
    """Convenience: returns (playwright_handle, context). Caller must stop()."""
    pw = sync_playwright().start()
    ctx = launch_context(pw)
    return pw, ctx
