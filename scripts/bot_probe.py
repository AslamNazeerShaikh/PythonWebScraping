"""Live bot-detection probe — implements docs/BOT_DETECTION.md Test B/C.

Uses the collector's REAL launcher (launch_context: persistent profile +
stealth init JS + adblock), visits bot-check sites, waits for client-side
checks, saves full-page screenshots + a machine-readable signal dump.

Diagnostic only: it MEASURES what automation exposes. It never alters
signals to fake a verdict.

Usage:
    HEADLESS=false BROWSER=firefox .venv/bin/python scripts/bot_probe.py --mode headed
    HEADLESS=true  BROWSER=chromium .venv/bin/python scripts/bot_probe.py --mode headless
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright  # noqa: E402

from src.stealth_browser import launch_context  # noqa: E402

#: Detection pages (all built for this purpose). Order = doc order.
TARGETS = [
    ("deviceandbrowserinfo",
     "https://deviceandbrowserinfo.com/are_you_a_bot"),
    ("browserscan", "https://browserscan.in/"),
    ("veil", "https://veilbrowser.cc/bot-check"),
    ("browserscan-net", "https://www.browserscan.net/bot-detection"),
    ("sannysoft", "https://bot.sannysoft.com/"),
    ("botd", "https://botd.fingerprint.com/"),
    ("creepjs", "https://creepjs.org/checker"),
    ("pixelscan", "https://pixelscan.net/"),
    ("iphey", "https://iphey.com/"),
    ("browserleaks", "https://browserleaks.com/"),
    ("fingerprint-scan", "https://fingerprint-scan.com/"),
]

#: Client-side signal dump — answers "what does this browser expose?"
SIGNAL_JS = """
() => {
  let webdriverInIframe = 'n/a';
  try {
    const f = document.createElement('iframe');
    f.style.display = 'none';
    document.body.appendChild(f);
    webdriverInIframe = f.contentWindow.navigator.webdriver;
    f.remove();
  } catch (e) { webdriverInIframe = 'error:' + e; }
  return {
    userAgent: navigator.userAgent,
    webdriver: navigator.webdriver,
    webdriverInIframe,
    plugins: navigator.plugins ? navigator.plugins.length : -1,
    languages: navigator.languages,
    hardwareConcurrency: navigator.hardwareConcurrency,
    deviceMemory: navigator.deviceMemory || 'unsupported',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    timezoneOffsetMin: new Date().getTimezoneOffset(),
    screen: [window.screen.width, window.screen.height],
    viewport: [window.innerWidth, window.innerHeight],
    maxTouchPoints: navigator.maxTouchPoints,
    hasChrome: !!window.chrome,
    cookieEnabled: navigator.cookieEnabled,
    doNotTrack: navigator.doNotTrack,
  };
}
"""


def probe(mode: str, out_dir: Path, wait_s: int = 10,
          only: list[str] | None = None) -> dict:
    """Run the full probe; returns the results dict (also saved as JSON)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict = {"mode": mode, "started": datetime.now().isoformat(),
                     "pages": {}}
    with sync_playwright() as p:
        context = launch_context(p)
        try:
            targets = [t for t in TARGETS if not only or t[0] in only]
            for name, url in targets:
                print(f"[{mode}] visiting {name}: {url}")
                page = context.new_page()
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=45000)
                except Exception as e:  # slow bot-check pages: still screenshot
                    print(f"[{mode}] nav warning on {name}: {e}")
                page.wait_for_timeout(wait_s * 1000)  # client-side checks finish
                shot = out_dir / f"{name}.png"
                try:
                    page.screenshot(path=str(shot), full_page=True, timeout=20000)
                except Exception as e:  # heavy/animated pages can stall stitching
                    print(f"[{mode}] {name}: full-page shot failed ({e}); "
                          f"viewport fallback")
                    page.screenshot(path=str(shot), full_page=False)
                try:
                    signals = page.evaluate(SIGNAL_JS)
                except Exception as e:
                    signals = {"error": str(e)}
                results["pages"][name] = {"url": url, "screenshot": str(shot),
                                          "signals": signals}
                print(f"[{mode}] {name}: webdriver={signals.get('webdriver')} "
                      f"tz={signals.get('timezone')} shot={shot.name}")
                page.close()
        finally:
            context.close()
    dest = out_dir / "signals.json"
    dest.write_text(json.dumps(results, indent=2))
    print(f"[{mode}] signals -> {dest}")
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="Bot-detection live probe (Test B/C).")
    ap.add_argument("--mode", default="headed", choices=["headed", "headless"])
    ap.add_argument("--wait", type=int, default=10,
                    help="seconds to let client-side checks finish per site")
    ap.add_argument("--out", default="output/botcheck",
                    help="results dir; mode becomes a subdir")
    ap.add_argument("--only", default="",
                    help="comma-separated target names to run (default: all)")
    args = ap.parse_args()
    only = [s.strip() for s in args.only.split(",") if s.strip()] or None
    probe(args.mode, Path(args.out) / args.mode, wait_s=args.wait, only=only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
