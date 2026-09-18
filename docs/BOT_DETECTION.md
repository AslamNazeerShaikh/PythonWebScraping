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

| Signal | Normal Fx | PW headed | PW headless | Notes |
|---|---|---|---|---|
| User-Agent | | | | |
| `navigator.webdriver` | | | | init script hides; verify incl. iframe |
| Headless markers | | | | |
| Plugins / languages | | | | |
| Timezone vs IP | | | | `Asia/Kolkata` + IN IP = consistent |
| WebRTC leaks | | | | disabled via prefs |
| Canvas / WebGL | | | | |
| TLS / HTTP/2 fingerprint | | | | browser-level, not spoofable here |
| Mouse/typing behaviour | | | | human pauses/scrolls only |

## 4. Reading the results

- A **few** residual differences vs normal Firefox are normal and acceptable;
  Naukri's wall for unknown sessions is handled by the manual-solve pause +
  persistent cookies, not by signal forgery.
- A **large** headed-vs-normal gap means re-check launcher prefs/init script
  rather than adding spoofing libraries (explicitly out of scope).
- Re-run A/B after any Playwright/Firefox upgrade; browsers drift, notes rot.
