"""Interaction QA against a live URL (P1c): overflow at 375/768/1280, console errors, link status, hover/focus byte-diff.

  python3 -I scripts/ui_qa.py [https://draftmark.edycu.dev] [outdir]     # exit 1 on any FAIL
Needs playwright (python) with chromium. Screenshots go to outdir (default .cache/ui, gitignored).
"""
import re
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://draftmark.edycu.dev").rstrip("/")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else ".cache/ui")
OUT.mkdir(parents=True, exist_ok=True)
PAGES = ["/", "/survey", "/evidence", "/certificate/rec-trieste-20261031", "/certificate/rec-db7x-20261031",
         "/certificate/synth-barge-s3", "/portal/"]
VIEWS = {"375": (375, 800), "768": (768, 900), "1280": (1280, 900)}
fails: list[str] = []


def rec(ok: bool, msg: str):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)


def status(url: str) -> int:
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"user-agent": "draftmark-ui-qa"})
        return urllib.request.urlopen(req, timeout=20).status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:  # noqa: BLE001
        return 0


with sync_playwright() as p:
    b = p.chromium.launch()
    links: dict[str, str] = {}
    for vname, (w, h) in VIEWS.items():
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=1)
        for path in PAGES:
            pg = ctx.new_page()
            errs: list[str] = []
            pg.on("console", lambda m, errs=errs: errs.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e, errs=errs: errs.append(str(e)))
            r = pg.goto(BASE + path, wait_until="networkidle")
            pg.wait_for_timeout(500)
            sw = pg.evaluate("document.documentElement.scrollWidth")
            rec(r.status == 200, f"{vname}px {path} -> {r.status}")
            rec(sw <= w + 1, f"{vname}px {path} no horizontal overflow (scrollWidth {sw})")
            rec(not errs, f"{vname}px {path} no console errors {errs[:2]}")
            small = pg.evaluate("""() => [...document.querySelectorAll('a,button,summary,input,select,[role=tab]')]
              .filter(e => e.offsetParent !== null && getComputedStyle(e).display !== 'inline' && !(e.tagName === 'INPUT' && e.closest('label') && e.closest('label').getBoundingClientRect().height >= 40)).map(e => ({t:(e.innerText||e.getAttribute('aria-label')||e.tagName).slice(0,24),
              w:e.getBoundingClientRect().width, h:e.getBoundingClientRect().height}))
              .filter(e => e.h < 40 && !/^(skip)/i.test(e.t))""")
            if vname == "375":
                rec(not small, f"375px {path} hit targets >= 40 px high {small[:3]}")
            pg.screenshot(path=str(OUT / f"{vname}-{re.sub(r'[^a-z0-9]+', '_', path.lower()).strip('_') or 'home'}.png"), full_page=True)
            if vname == "1280":
                for href in pg.evaluate("[...document.querySelectorAll('a[href]')].map(a => a.href)"):
                    links[href] = path
            pg.close()
        ctx.close()
    # link inventory
    for href, src in sorted(links.items()):
        if href.startswith(BASE) and "#" in href:
            continue
        if href.startswith("mailto:"):
            continue
        s = status(href)
        rec(s in (200, 301, 302, 307, 308), f"link {href} (on {src}) -> {s}")
    # hover / focus byte-diff, one per element class
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    pg.goto(BASE + "/", wait_until="networkidle")
    for name, sel in [("nav link", ".nav a:not(.btn)"), ("accent button", ".btn--accent"), ("brand", ".brand"), ("tab", ".tab[aria-selected=false]"), ("badge link", ".badge--link")]:
        el = pg.locator(sel).first
        if not el.count():
            print(f"SKIP hover {name}: {sel} not on /")
            continue
        el.scroll_into_view_if_needed()
        pg.mouse.move(0, 0)
        pg.wait_for_timeout(400)
        before = el.screenshot()
        el.hover()
        pg.wait_for_timeout(450)
        after = el.screenshot()
        rec(before != after, f"hover feedback: {name} ({sel})")
        pg.mouse.move(0, 0)
        el.focus()
        pg.keyboard.press("Tab")
        pg.keyboard.press("Shift+Tab")
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(OUT / f"focus-{name.replace(' ', '_')}.png"))
    pg.goto(BASE + "/survey", wait_until="networkidle")
    for name, sel in [("button", ".btn")]:
        el = pg.locator(sel).first
        if not el.count():
            print(f"SKIP hover {name}: {sel} not on /survey")
            continue
        el.scroll_into_view_if_needed()
        pg.mouse.move(0, 0)
        pg.wait_for_timeout(400)
        before = el.screenshot()
        el.hover()
        pg.wait_for_timeout(450)
        rec(before != el.screenshot(), f"hover feedback (survey): {name} ({sel})")
    b.close()
print(f"\n{len(fails)} FAIL" if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
