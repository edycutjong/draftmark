"""Computer-use sub-agent: Muse Spark 1.3 with the native `computer` tool drives a browser.

Rung A of the CU ladder: Wonder plans (no tools), Spark acts. Every Spark action carries
`computer_action_requires_confirmation`; the harness acknowledges ONLY when the page is on
an allowlisted host (our demo portal, read-only public pages) and stops anywhere else.
After filing, code reads back what the portal RECEIVED and compares it to the certificate.
"""
from __future__ import annotations

import base64
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse

from . import meta

ALLOWLIST = ("localhost", "127.0.0.1", "draftmark.edycu.dev", "wikipedia.org")
SYSTEM = ("You are a computer-use agent operating a web browser. Coordinates are pixels in the last screenshot. "
          "Batch actions only when they do not depend on intermediate visual feedback. Never submit anything except "
          "on the page you were asked to use. Finish with a short plain answer when the goal is visibly complete; "
          "say INFEASIBLE if blocked (login, captcha, unexpected site).")


def host_allowed(url: str, allow=ALLOWLIST) -> bool:
    h = (urlparse(url).hostname or "").lower()
    return any(h == a or h.endswith("." + a) for a in allow)


@dataclass
class CuRun:
    task: str
    steps: list[dict] = field(default_factory=list)
    final: str | None = None
    stopped: str | None = None
    seconds: float = 0.0
    usage_rows: list = field(default_factory=list)


def _shot(page) -> str:
    return "data:image/png;base64," + base64.b64encode(page.screenshot()).decode()


def _apply(page, a: dict) -> None:
    k = a.get("type")
    if k == "click":
        b = a.get("button", "left")
        page.mouse.click(a["x"], a["y"], button=b if b in ("left", "right", "middle") else "left")
    elif k == "double_click":
        page.mouse.dblclick(a["x"], a["y"])
    elif k == "type":
        page.keyboard.type(a["text"])
    elif k == "keypress":
        page.keyboard.press("+".join(a["keys"]))
    elif k == "scroll":  # notches -> 100 px each (day-0 finding)
        page.mouse.move(a["x"], a["y"])
        page.mouse.wheel(100 * a.get("scroll_x", 0), 100 * a.get("scroll_y", 0))
    elif k == "move":
        page.mouse.move(a["x"], a["y"])
    elif k == "drag":
        pts = a["path"]
        page.mouse.move(pts[0]["x"], pts[0]["y"])
        page.mouse.down()
        for q in pts[1:]:
            page.mouse.move(q["x"], q["y"])
        page.mouse.up()


def run(client: meta.Client, page, task: str, max_steps: int = 15, allow=ALLOWLIST, settle_s: float = 1.0,
        on_step=None) -> CuRun:
    out = CuRun(task)
    t0 = time.time()
    body = {"model": meta.SPARK, "instructions": SYSTEM, "tools": [{"type": "computer"}],
            "reasoning": {"effort": "low"},
            "input": [{"role": "user", "content": [{"type": "input_text", "text": task},
                                                   {"type": "input_image", "image_url": _shot(page)}]}]}
    for step in range(max_steps):
        resp = client.responses(body, f"spark computer-use step {step}")
        calls = [o for o in resp.get("output", []) if o.get("type") == "computer_call"]
        if not calls:
            out.final = " ".join(c.get("text", "") for o in resp.get("output", []) if o.get("type") == "message"
                                 for c in o.get("content", []) if isinstance(c, dict))
            break
        c = calls[0]
        acts = c.get("actions") or ([c["action"]] if c.get("action") else [])
        checks = c.get("pending_safety_checks") or []
        rec = {"step": step, "url": page.url, "actions": acts, "checks": [x.get("code") for x in checks]}
        if checks and not host_allowed(page.url, allow):
            rec["stopped"] = f"confirmation requested on non-allowlisted host {urlparse(page.url).hostname}"
            out.steps.append(rec)
            out.stopped = rec["stopped"]
            break
        for a in acts:
            _apply(page, a)
        time.sleep(settle_s)
        if not host_allowed(page.url, allow):
            rec["stopped"] = f"navigated off the allowlist to {urlparse(page.url).hostname}"
            out.steps.append(rec)
            out.stopped = rec["stopped"]
            break
        out.steps.append(rec)
        if on_step:
            on_step(step, page)
        body = {"model": meta.SPARK, "previous_response_id": resp["id"], "tools": [{"type": "computer"}],
                "reasoning": {"effort": "low"},
                "input": [{"type": "computer_call_output", "call_id": c["call_id"],
                           "acknowledged_safety_checks": [{"id": x["id"], "code": x["code"], "message": x["message"]}
                                                          for x in checks],
                           "output": {"type": "computer_screenshot", "image_url": _shot(page)}}]}
    else:
        out.stopped = f"max steps {max_steps}"
    out.seconds = round(time.time() - t0, 1)
    return out


def norm(v) -> str:
    s = str(v).strip().replace(",", "").replace(" ", " ")
    try:
        f = float(s)
        return f"{f:.1f}"
    except ValueError:
        return s.upper()


def compare(expected: dict, received: dict) -> dict:
    """Field-by-field read-back: what the portal echoed vs the certificate's code values."""
    rows = {k: {"expected": str(v), "received": received.get(k), "match": norm(v) == norm(received.get(k, ""))}
            for k, v in expected.items()}
    return {"ok": all(r["match"] for r in rows.values()), "fields": rows}
