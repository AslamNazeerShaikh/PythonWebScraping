"""E-commerce practice test — a few products from Amazon.in + Flipkart.

Scope (deliberately tiny): ONE search page per site ("wireless mouse"),
top ~5 product cards each (title/price/rating/url), Pydantic-validated,
saved to output/practice/ecommerce.json with a pass/fail report.

Fair-use: polite delays, no pagination, no login, testing only. If a site
serves a captcha/robot wall, the script screenshots it, records BLOCKED, and
moves on — it never hammers or bypasses. Real runs use headed mode (these
sites routinely wall headless-shell).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from src.stealth_browser import human_pause, launch_context  # noqa: E402

QUERY = "wireless mouse"
SITES = {
    "amazon": "https://www.amazon.in/s?k=" + QUERY.replace(" ", "+"),
    "flipkart": "https://www.flipkart.com/search?q=" + QUERY.replace(" ", "+"),
}

#: Tolerant multi-layout extractors (both sites rotate markup; first hit wins).
#: Amazon.in (verified live): title lives in `a.s-link-style[href*="/dp/"]`
#: (NOT inside h2 — h2 holds a bare span); price `span.a-price .a-offscreen`;
#: rating `span.a-icon-alt`. Sponsored cards carry `AdHolder` in class.
AMAZON_EXTRACT_JS = """
() => {
  const vis = (el) => { if (!el) return '';
    const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return (s.display === 'none' || r.width < 2) ? '' : (el.innerText || '').trim(); };
  const out = [];
  for (const card of document.querySelectorAll('div[data-component-type="s-search-result"]')) {
    let a = card.querySelector('a.s-link-style[href*="/dp/"]');
    if (!a) a = Array.from(card.querySelectorAll('a[href*="/dp/"]'))
      .find(x => (x.textContent || '').trim().length >= 10 && !x.href.includes('javascript:'));
    if (!a) continue;
    const title = (a.textContent || '').trim().replace(/\\s+/g, ' ');
    if (title.length < 4) continue;
    out.push({
      title,
      price: vis(card.querySelector('span.a-price span.a-offscreen')),
      rating: vis(card.querySelector('span.a-icon-alt')),
      url: new URL(a.getAttribute('href').split('?')[0], location.origin).toString(),
    });
    if (out.length >= 5) break;
  }
  return out;
}
"""

#: Flipkart (verified live): cards are `div[data-id]`; product links match
#: `/p/`. Title/price/rating are parsed from card TEXT with SEARCH regexes
#: (not line matches — Flipkart glues "Grey4.3(12)₹459₹84945% off" onto one
#: line; class names also rotate too fast to pin).
FLIPKART_EXTRACT_JS = """
() => {
  const out = []; const seen = new Set();
  for (const root of document.querySelectorAll('div[data-id]')) {
    const a = root.querySelector('a[href*="/p/"]');
    if (!a) continue;
    const href = (a.getAttribute('href') || '').split('?')[0];
    if (href.indexOf('/p/') < 0 || seen.has(href)) continue;
    const txt = root.innerText.replace(/\\s+/g, ' ');
    const mPrice = txt.match(/₹[\\d,]+/);
    if (!mPrice) continue;  // nav/accessory links have no price
    const mRate = txt.match(/\\d\\.\\d\\s*\\([^\\)]{0,20}\\)/);
    const cut = Math.min(mRate ? mRate.index : 1e9, mPrice.index == null ? 1e9 : mPrice.index);
    let title = txt.slice(0, cut).replace(/^Add to Compare/i, '').trim();
    if (title.length < 4) continue;
    seen.add(href);
    out.push({ title, price: mPrice[0], rating: mRate ? mRate[0] : '',
      url: new URL(href, location.origin).toString() });
    if (out.length >= 5) break;
  }
  return out;
}
"""

#: Visible bot-wall markers per site (captcha / robot-check pages).
WALL_MARKERS = {
    "amazon": ["enter the characters", "robot check", "sorry, we just need"],
    "flipkart": ["robot check"],
}


class Product(BaseModel):
    """Validated product record (e-commerce twin of the Job contract)."""

    site: str
    title: str = Field(min_length=4)
    price: str = ""
    rating: str = ""
    url: str = ""

    @classmethod
    def coerce(cls, site: str, raw: dict):  # type: ignore[no-untyped-def]
        try:
            return cls(site=site, title=(raw.get("title") or "").strip(),
                       price=(raw.get("price") or "").strip(),
                       rating=(raw.get("rating") or "").strip(),
                       url=(raw.get("url") or "").split("?")[0])
        except Exception:
            return None


def _dismiss_flipkart_login(page) -> None:  # type: ignore[no-untyped-def]
    """Close Flipkart's login modal when present (normal dismiss, not a wall)."""
    try:
        for sel in ["button._2KpZ6l._2doB4z", "span._30XB9F", "button:has-text('✕')"]:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                btn.click(timeout=3000)
                page.wait_for_timeout(800)
                return
    except Exception:
        pass


def scrape_site(page, site: str, url: str, out_dir: Path) -> dict:  # type: ignore[no-untyped-def]
    """Scrape one search page; returns a result dict (blocked or products)."""
    print(f"[eco] {site}: {url}", flush=True)
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(3000)
    if site == "flipkart":
        _dismiss_flipkart_login(page)
    # Human-like scroll to trigger lazy cards.
    for _ in range(3):
        try:
            page.mouse.wheel(0, 700)
        except Exception:
            page.evaluate("window.scrollBy(0,700)")
        page.wait_for_timeout(900)
    blob = (page.evaluate("document.body ? document.body.innerText.slice(0,3000) : ''")
            or "").lower()
    if any(m in blob for m in WALL_MARKERS.get(site, [])):
        shot = out_dir / f"{site}-wall.png"
        page.screenshot(path=str(shot), full_page=False)
        return {"site": site, "status": "BLOCKED",
                "detail": "captcha/robot wall served; screenshot saved, not retried",
                "products": []}
    raw = page.evaluate(AMAZON_EXTRACT_JS if site == "amazon"
                        else FLIPKART_EXTRACT_JS) or []
    products = [p for p in (Product.coerce(site, r) for r in raw) if p]
    return {"site": site,
            "status": "OK" if len(products) >= 3 else "THIN",
            "detail": f"{len(products)} valid products (target >= 3)",
            "products": [p.model_dump() for p in products]}


def main() -> int:
    ap = argparse.ArgumentParser(description="E-commerce practice test.")
    ap.add_argument("--out", default="output/practice")
    ap.add_argument("--query", default=QUERY)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.query != QUERY:
        for site in SITES:
            base = SITES[site].split("?")[0]
            param = "k" if site == "amazon" else "q"
            SITES[site] = f"{base}?{param}=" + args.query.replace(" ", "+")

    results: list[dict] = []
    with sync_playwright() as p:
        context = launch_context(p)
        try:
            page = context.new_page()
            for site, url in SITES.items():
                try:
                    results.append(scrape_site(page, site, url, out))
                except Exception as e:  # one site failing never kills the other
                    results.append({"site": site, "status": "ERROR",
                                    "detail": f"{type(e).__name__}: {str(e)[:120]}",
                                    "products": []})
                human_pause(2.0, 4.0)  # polite gap between sites
            page.close()
        finally:
            context.close()

    report = {"at": datetime.now().isoformat(), "query": args.query,
              "results": results}
    (out / "ecommerce.json").write_text(json.dumps(report, indent=2,
                                                   ensure_ascii=False))
    ok = sum(1 for r in results if r["status"] == "OK")
    print(f"\nE-commerce: {ok}/{len(results)} sites OK "
          f"(BLOCKED/THIN recorded honestly, never retried)")
    for r in results:
        for pr in r["products"][:5]:
            print(f"  [{r['site']}] {pr['title'][:60]:60} | "
                  f"{pr['price'][:18]:18} | {pr['rating'][:16]}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
