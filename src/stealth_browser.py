"""Stealth browser launcher: Firefox-first + Chromium auto-fallback.

Preferred stack per request: Playwright + Firefox + uBlock Origin.
Reality check (Sep 2026): Playwright's Firefox Nightly build is broken on
newer macOS ("Could not find profile folder" even for temp profiles), so:
  - BROWSER=firefox (default): tries Firefox persistent profile first.
  - On ANY Firefox launch failure: automatically falls back to Chromium
    persistent profile with the same stealth init script + adblock fallback.
  - BROWSER=chromium: skips Firefox and goes straight to Chromium.

uBlock layers:
  - Firefox: official .xpi pre-seeded into profile/extensions/ (2nd+ run) or
    one-time manual install via about:addons (persists in .pw-profile/).
  - Chromium: unpacked extension dir via --load-extension (UBLOCK_UNPACKED_DIR),
    else fallback request-blocker (ADBLOCK_FALLBACK).
We do NOT bypass CAPTCHAs — on bot-walls we pause for manual solve.
"""
from __future__ import annotations

import random
import shutil
import time
import zipfile
from pathlib import Path

from playwright.sync_api import BrowserContext, Playwright, sync_playwright

from .config import SETTINGS

# --- Minimal tracker/ad host blocklist (fallback when uBlock absent) ---
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
  // languages
  Object.defineProperty(navigator, 'languages', { get: () => ['en-IN', 'en-US', 'en'] });
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
  // screen size consistency handled by viewport; add realistic deviceMemory
  Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
}
"""

FIREFOX_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) "
    "Gecko/20100101 Firefox/126.0"
)
CHROMIUM_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def human_pause(a: float | None = None, b: float | None = None) -> None:
    """Sleep a random politeness interval (defaults: SETTINGS min/max delay).

    Randomised — not fixed — so inter-request timing looks human and stays
    gentle on Naukri's servers. Pass ``(0, 0)`` in tests to skip waiting.
    """
    lo = a if a is not None else SETTINGS.min_delay_s
    hi = b if b is not None else SETTINGS.max_delay_s
    time.sleep(random.uniform(lo, hi))


def install_ublock_into_profile(profile_dir: Path, xpi_path: str) -> bool:
    """Install uBlock Origin XPI into a Firefox profile dir (2nd+ run only)."""
    try:
        src = Path(xpi_path).expanduser().resolve()
        if not src.is_file():
            print(f"[ublock] XPI not found at {src} — using fallback blocker.")
            return False
        profile_dir.mkdir(parents=True, exist_ok=True)
        ext_dir = profile_dir / "extensions"
        ext_dir.mkdir(parents=True, exist_ok=True)
        ext_id = "uBlock0@raymondhill.net"  # official uBO Firefox ID
        dest = ext_dir / f"{ext_id}.xpi"
        if not dest.exists() or dest.stat().st_size != src.stat().st_size:
            shutil.copyfile(src, dest)
            print(f"[ublock] Installed uBlock Origin XPI -> {dest}")
        else:
            print("[ublock] uBlock Origin already installed in profile.")
        return True
    except Exception as e:  # never crash launch because of adblock
        print(f"[ublock] Install failed ({e}) — using fallback blocker.")
        return False


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


def _prep_profile(profile: Path) -> None:
    """Prepare the profile dir for a Firefox persistent launch.

    Removes an EMPTY dir (Playwright's Firefox/juggler exits with “Could not
    find profile folder” for empty dirs) and ensures the parent exists.
    """
    try:
        if profile.exists() and profile.is_dir() and not any(profile.iterdir()):
            profile.rmdir()
    except Exception:
        pass
    profile.parent.mkdir(parents=True, exist_ok=True)


def _launch_firefox(p: Playwright) -> BrowserContext:
    """Launch the preferred engine: persistent Firefox with stealth defaults.

    Uses the real profile dir (cookies/history survive → less bot-like),
    hardened prefs (tracking protection, DNT, no WebRTC/geo leaks), the
    stealth init script, and the adblock fallback. Raises on failure so
    :func:`launch_context` can fall back to Chromium.
    """
    profile = SETTINGS.user_data_dir
    _prep_profile(profile)

    ublock_ok = False
    profile_exists = profile.exists() and (profile / "prefs.js").exists()
    if SETTINGS.ublock_xpi_path and profile_exists:
        ublock_ok = install_ublock_into_profile(profile, SETTINGS.ublock_xpi_path)
    elif SETTINGS.ublock_xpi_path and not profile_exists:
        print("[ublock] First run: profile will be created now. "
              "Install the XPI once via about:addons, it persists.")
    else:
        print("[ublock] UBLOCK_XPI_PATH not set — using fallback blocker. "
              "See README for one-time uBO download.")

    context = p.firefox.launch_persistent_context(
        user_data_dir=str(profile),
        headless=SETTINGS.headless,
        slow_mo=SETTINGS.slow_mo_ms,
        viewport={"width": SETTINGS.viewport_w, "height": SETTINGS.viewport_h},
        locale=SETTINGS.locale,
        timezone_id=SETTINGS.timezone,
        user_agent=FIREFOX_UA,
        accept_downloads=True,
        firefox_user_prefs={
            "privacy.trackingprotection.enabled": True,
            "privacy.trackingprotection.socialtracking.enabled": True,
            "privacy.donottrackheader.enabled": True,
            "dom.webdriver.enabled": False,
            "media.peerconnection.enabled": False,
            "geo.enabled": False,
        },
    )
    context.set_default_navigation_timeout(SETTINGS.nav_timeout_ms)
    context.set_default_timeout(20000)
    context.add_init_script(STEALTH_INIT_JS)
    _maybe_block_ads(context)
    mode = "uBlock-XPI" if ublock_ok else "fallback-blocker"
    print(f"[browser] Firefox persistent profile ready ({mode}) | "
          f"headless={SETTINGS.headless} locale={SETTINGS.locale}")
    return context


def _launch_chromium(p: Playwright) -> BrowserContext:
    """Launch the fallback engine: persistent Chromium with stealth defaults.

    Mirrors the Firefox setup (own ``*-chromium`` profile dir, stealth init
    script, adblock fallback) plus ``--disable-blink-features=
    AutomationControlled``. Supports unpacked uBlock via UBLOCK_UNPACKED_DIR
    (Firefox .xpi files do NOT load here — noted at runtime).
    """
    profile = Path(str(SETTINGS.user_data_dir) + "-chromium")
    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    unpacked = getattr(SETTINGS, "ublock_unpacked_dir", "")
    if unpacked and Path(unpacked).expanduser().is_dir():
        args += [
            f"--disable-extensions-except={unpacked}",
            f"--load-extension={unpacked}",
        ]
        print(f"[ublock] Loading unpacked uBO (chromium): {unpacked}")
    elif SETTINGS.ublock_xpi_path:
        print("[ublock] XPI is Firefox-only; chromium uses fallback blocker.")
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(profile),
        headless=SETTINGS.headless,
        slow_mo=SETTINGS.slow_mo_ms,
        viewport={"width": SETTINGS.viewport_w, "height": SETTINGS.viewport_h},
        locale=SETTINGS.locale,
        timezone_id=SETTINGS.timezone,
        user_agent=CHROMIUM_UA,
        accept_downloads=True,
        args=args,
        # Chromium: hide automation flag; keep headless-shell compatible
        chromium_sandbox=False,
        ignore_default_args=["--enable-automation"],
    )
    context.set_default_navigation_timeout(SETTINGS.nav_timeout_ms)
    context.set_default_timeout(20000)
    context.add_init_script(STEALTH_INIT_JS)
    _maybe_block_ads(context)
    print(f"[browser] Chromium persistent profile ready (fallback-blocker) | "
          f"headless={SETTINGS.headless} locale={SETTINGS.locale}")
    return context


def launch_context(p: Playwright) -> BrowserContext:
    """Launch requested engine; auto-fallback Firefox -> Chromium."""
    want = (SETTINGS.browser or "firefox").lower()
    if want.startswith("chrom"):
        return _launch_chromium(p)
    try:
        return _launch_firefox(p)
    except Exception as e:
        print(f"[browser] Firefox launch failed ({type(e).__name__}: {str(e)[:200]})")
        print("[browser] Falling back to Chromium persistent profile...")
        return _launch_chromium(p)


def launch_playwright() -> tuple[object, BrowserContext]:
    """Convenience: returns (playwright_handle, context). Caller must stop()."""
    pw = sync_playwright().start()
    ctx = launch_context(pw)
    return pw, ctx
