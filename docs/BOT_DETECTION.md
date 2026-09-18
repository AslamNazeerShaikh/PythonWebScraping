# Bot-Detection Test Guide — measure exposure, don't chase “Human”

> These public test sites answer **“what signals does my automation expose?”**
> They are diagnostic instruments, not obstacles to defeat. The collector stays
> a normal, low-volume browser: persistent profile, human pacing, manual solves.
> Never tune signals to fake a “Human” verdict.

## 1. Sites (comparison order)

| Site | Signals covered | Use |
|---|---|---|
| [Fingerprint BotD](https://github.com/fingerprintjs/BotD) (open source) | Playwright/Firefox automation flags | Start here — compare normal vs automated |
| [Fingerprint Bot Firewall demo](https://demo.fingerprint.com/bot-firewall) | Playwright-vs-demo detection + IP block demo | Closest to production anti-bot |
| [DeviceAndBrowserInfo](https://deviceandbrowserinfo.com/are_you_a_bot) | UA, `webdriver` (+in iframe), headers, mouse/typing, CDP | Per-signal drill-down |
| [BrowserScan](https://browserscan.in/) | 200+ checks: fingerprint vs IP/timezone/network, WebRTC | Consistency (browser vs network identity) |
| [BrowserScan.net bot-detection](https://www.browserscan.net/bot-detection) | Webdriver/UA/CDP/Navigator matrix + native-function checks | Second opinion, CDP focus |
| [Sannysoft bot test](https://bot.sannysoft.com/) | Phantom/Headless/Selenium/WebDriver flags, canvas, fp-collect | Classic flag table |
| [CreepJS checker](https://creepjs.org/checker) | Trust score, lies detection, collector coverage, IP risk | Strictest open tester |
| [Pixelscan](https://pixelscan.net/) | Proxy/automation/behavior, consistency, WebGL | Green/red verdict badges |
| [Iphey](https://iphey.com/) | hasCDP/hasWebdriver/hasNavigator flags, MX score | Names the exact tripwire |
| [BrowserLeaks](https://browserleaks.com/) | IP/WebRTC/canvas/WebGL/TLS/font leak tools (hub) | Manual sub-page checks |
| [Fingerprint-scan](https://fingerprint-scan.com/) | Bot score 0-100 by category (Browser vs HW/OS) | Where the points come off |
| [BotD live demo](https://botd.fingerprint.com/) | — retired (DNS NXDOMAIN) | Use bot-firewall demo manually |
| [Fingerprint bot-firewall](https://demo.fingerprint.com/bot-firewall) | Playwright-vs-demo + IP block demo | Manual (interactive) |

Verdict evidence: [`evidence/`](evidence/) (screenshots + `signals-headed.json`).
Probe: `scripts/bot_probe.py [--only site,...]` (11 targets).
| [Veil bot-check](https://veilbrowser.cc/bot-check) | Automation, headless, consistency, leaks | Secondary opinion |
| [Sendwin](https://send.win/tools/bot-detection-test/) | webdriver, driver globals, headless markers | Quick lightweight check |
| DataDome / Akamai demos | Commercial device-check concepts | Background reading, not playgrounds |

## 2. Procedure — Test A/B/C matrix

**Test A — baseline (normal Firefox, headed).** Visit BotD, DeviceAndBrowserInfo,
BrowserScan. Screenshot/note every reported signal. This is your reference row.

**Test B — Playwright (headed).** Run the collector's real launcher headful
against the same three sites; screenshot; diff against A. Example probe:

```python
from playwright.sync_api import sync_playwright
from src.stealth_browser import launch_context  # real profile + stealth init JS

with sync_playwright() as p:
    ctx = launch_context(p)          # headed: HEADLESS=false in .env
    page = ctx.new_page()
    page.goto("https://deviceandbrowserinfo.com/are_you_a_bot")
    page.wait_for_timeout(8000)      # let client-side checks finish
    page.screenshot(path="output/botcheck-headed.png")
    ctx.close()
```

**Test C — headed vs headless.** Repeat B with `HEADLESS=true`; record the
delta (expect headless to light up more signals — one reason the collector
runs headful for first contact).

## 3. Signal table (fill from your runs)

Measured 2026-09-19 on this Mac (Playwright Chromium-fallback, headed unless
noted; screenshots + `signals.json` under `output/botcheck*/`, gitignored):

| Signal | Normal Fx (Test A) | PW headed (Test B) | PW headless (Test C) | Notes |
|---|---|---|---|---|
| User-Agent | — (see below) | genuine `Chrome/153` | `HeadlessChrome` brand | was pinned `126` → fixed, see §5 |
| `navigator.webdriver` | n/a | `false` (+in iframe) | `false` | init script hides; iframe verified too |
| Headless markers | n/a | none fired | software GL, 0 plugins, `window.chrome` absent, UA brands | headless-shell lights up 7+ checks |
| Plugins / languages | n/a | 5 / `['en-IN']` (genuine) | 0 / `en-IN` | stub languages removed, see §5 |
| Timezone vs IP | n/a | `Asia/Calcutta` ⇔ IN IP, consistent | same | `TIMEZONE=Asia/Kolkata` |
| WebRTC leaks | n/a | real IPs shown (info-only) | same | disabled prefs don't hide local IPs from JS |
| Canvas / WebGL | n/a | real Apple M GPU (headed) | SwiftShader software GL | headless dead giveaway |
| TLS / HTTP/2 fingerprint | n/a | browser-level, not spoofable here | same | accepted residual |
| Mouse/typing behaviour | n/a | detected after interaction | "waiting for activity" | probe doesn't interact; real runs scroll |

Site verdicts: **Veil** headed 23/23 human (twice) → headless "Automated"
(2 failed / 7 suspicious). **BrowserScan** headed **44 → 100** after the §5
fix ("looks genuine", 1 residual: main-vs-worker language). **DeviceAndBrowserInfo**
headed "bot" on CDP/timing/worker flags only — every classic flag
(webdriver, Playwright, headless, UA) false; inherent to any CDP-driven
browser, accepted. **BrowserScan.net** headed: **Normal** — all four
categories green (Webdriver, User-Agent, CDP, Navigator), incl. genuine
`Chrome/153` UA, `MacIntel`, `en-IN`, real plugins. **Sannysoft** headed:
**all rows green** (Phantom/Headless/Selenium/WebDriver flags, canvas,
fp-collect). **CreepJS checker** headed: **Trust 93/100, Level I** —
"No automation indicator observed", collector 100% (53/53), IP risk perfect
(residential Airtel IN). **Pixelscan** headed: all green ("No proxy
detected", "No automated behavior detected", consistent Asia/Calcutta).
**Iphey** headed: "Unreliable", MX 90 — exactly ONE tripwire named:
`hasCDP: true`; hasWebdriver/hasUserAgent/hasNavigator all false.
**BrowserLeaks** hub loads clean (sub-tools are manual spot-checks).
**Fingerprint-scan** headed: **Bot 80/100** — Browser: HIGH, Hardware/OS:
LOW (same CDP-only story, priced at 20 points). **BotD demo domain is
retired** (`botd.fingerprint.com` NXDOMAIN); the interactive bot-firewall
demo remains a manual exercise. Probe: `scripts/bot_probe.py --only browserscan-net,sannysoft`.

Test A (real Firefox baseline) could NOT run in this sandbox: no Firefox
engine starts here (stable 155 + Nightly both fail with “Could not find
profile folder” on this macOS), and screen capture is denied. Manual step
(~1 min): open the three URLs in your own Firefox/Chrome and compare with
`output/botcheck2/headed/*.png` — expect green/human verdicts; the gap
between those and Test B is the true automation delta.

## 5. Fix applied from these measurements (2026-09-19)

Two self-inflicted inconsistencies, both fixed as *consistency* (not spoofing):
1. Pinned `Chrome/126` UA vs auto-updating engine → BrowserScan "engine NEWER
   than UA claims". **Fix:** no `user_agent` override; genuine engine UA.
2. Stubbed `navigator.languages` vs Worker scope → BrowserScan worker mismatch.
   **Fix:** override removed; Playwright `locale` (`en-IN`) is the single source.
Result: BrowserScan 44 → 100; Veil unchanged at 23/23. DeviceAndBrowserInfo
unchanged (CDP-inherent). Suite: 93 tests / 100% coverage.

## 4. Reading the results

- A **few** residual differences vs normal Firefox are normal and acceptable;
  Naukri's wall for unknown sessions is handled by the manual-solve pause +
  persistent cookies, not by signal forgery.
- A **large** headed-vs-normal gap means re-check launcher prefs/init script
  rather than adding spoofing libraries (explicitly out of scope).
- Re-run A/B after any Playwright/Firefox upgrade; browsers drift, notes rot.
