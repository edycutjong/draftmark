"""P1a CU spike (rung A): Wonder plans the filing, Spark 1.3's native computer tool files it
into our local DEMO PORTAL (public/portal), code reads back what the portal received.
Also: a fault-injection filing (one wrong value typed by the harness) that the read-back
must reject, and one read-only lookup on an allowlisted public site.

  python scripts/spike_cu.py
Writes evidence/cu-runs.md. Screenshots stay in .cache/cu/.
"""
import functools
import http.server
import json
import threading
import time

from _common import CACHE, EVIDENCE, ROOT, meta
from playwright.sync_api import sync_playwright

from api._core import cu, selftest
from api._core import reference_survey as R

PORT = 8765


def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT / "public"))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def certificate() -> dict:
    """A spike fixture computed by code: Trieste condition 4.1 inputs through the reference program;
    cargo here = displacement - lightship weight (booklet cond 1); u from +-10 mm on every mark."""
    c = next(x for x in selftest.conditions() if x["cond_id"] == "4.1")
    d = R.survey(c["inputs"])["disp_final"]
    up = R.survey({k: v + 0.01 if k != "sg" else v for k, v in c["inputs"].items()})["disp_final"]
    lo = R.survey({k: v - 0.01 if k != "sg" else v for k, v in c["inputs"].items()})["disp_final"]
    light = 11244.06
    return {"vessel": "TRIESTE BOOKLET TEST SHIP (cond 4.1)", "survey_date": time.strftime("%Y-%m-%d"),
            "displacement": f"{d:.1f}", "cargo": f"{d - light:.1f}", "uncertainty": f"{(up - lo) / 2:.1f}",
            "decision": "ISSUE"}


def wonder_plan(cl, cert: dict) -> dict:
    schema = {"type": "object", "additionalProperties": False, "required": ["steps", "check"],
              "properties": {"steps": {"type": "array", "items": {"type": "string"}}, "check": {"type": "string"}}}
    body = {"model": meta.WONDER, "reasoning": {"effort": "low"}, "max_output_tokens": 3000,
            "text": {"format": {"type": "json_schema", "name": "filing_plan", "strict": True, "schema": schema}},
            "input": [{"role": "user", "content": [{"type": "input_text", "text": (
                "You orchestrate a browser sub-agent that will file a draft-survey result into a web form titled "
                "'File a draft-survey result' (fields: Vessel name, Survey date, Displacement (t), Cargo (t), "
                "Uncertainty ± (t), Decision dropdown; a 'Submit filing' button; after submit the page shows a "
                "'Received' box). Write short imperative steps for the sub-agent with the exact values to enter, "
                "and one sentence it must check before finishing. Values (enter exactly): " + json.dumps(cert))}]}]}
    resp = cl.responses(body, "wonder filing plan")
    return json.loads(meta.output_text(resp)) | {"response_id": resp.get("id")}


def read_back(page) -> dict:
    return {el.get_attribute("data-field"): el.inner_text().strip() for el in page.query_selector_all("[data-field]")}


def main():
    (CACHE / "cu").mkdir(parents=True, exist_ok=True)
    srv = serve()
    cert = certificate()
    cl = meta.Client(run_id="p1a-cu")
    plan = wonder_plan(cl, cert)
    task = ("File this draft-survey result on the open page. Follow these steps:\n- " + "\n- ".join(plan["steps"])
            + "\nBefore finishing, check: " + plan["check"])
    results = {"certificate": cert, "plan": plan}
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"http://127.0.0.1:{PORT}/portal/index.html")
        shots = lambda i, pg: pg.screenshot(path=str(CACHE / "cu" / f"file_step{i:02d}.png"))  # noqa: E731
        rows0 = len(cl.rows)
        run = cu.run(cl, page, task, max_steps=15, on_step=shots)
        rb = read_back(page)
        results["filing"] = {"steps": len(run.steps), "seconds": run.seconds, "final": run.final,
                             "stopped": run.stopped, "actions": [s["actions"] for s in run.steps],
                             "confirmations_acked": sum(len(s["checks"]) for s in run.steps),
                             "est_usd": round(sum(r.est_usd for r in cl.rows[rows0:]), 4),
                             "read_back": cu.compare(cert, rb)}
        # fault injection: the harness types one wrong value; the read-back must fail
        page.goto(f"http://127.0.0.1:{PORT}/portal/index.html")
        bad = dict(cert, cargo=f"{float(cert['cargo']) + 1:.1f}")
        for k, v in bad.items():
            if k == "decision":
                page.select_option("#decision", v)
            else:
                page.fill(f"#{k}", v)
        page.click("#submit")
        page.wait_for_selector("[data-field]")
        results["fault_injection"] = cu.compare(cert, read_back(page))
        # read-only lookup on an allowlisted public host
        page.goto("https://en.wikipedia.org/wiki/Ever_Given", timeout=60000)
        rows1 = len(cl.rows)
        look = cu.run(cl, page, "On this Wikipedia article, find the ship's gross tonnage and its length as listed "
                                "in the infobox. Answer with both values only.", max_steps=6)
        results["lookup"] = {"steps": len(look.steps), "seconds": look.seconds, "final": look.final,
                             "stopped": look.stopped, "est_usd": round(sum(r.est_usd for r in cl.rows[rows1:]), 4)}
        # off-allowlist stop: a host we never acknowledge on
        page.goto("https://example.com/", timeout=60000)
        rows2 = len(cl.rows)
        off = cu.run(cl, page, "Click the 'More information' link on this page.", max_steps=2)
        results["off_allowlist"] = {"steps": len(off.steps), "stopped": off.stopped,
                                    "est_usd": round(sum(r.est_usd for r in cl.rows[rows2:]), 4)}
        b.close()
    srv.shutdown()
    (CACHE / "cu" / "results.json").write_text(json.dumps(results, indent=1, default=str))
    f = results["filing"]
    print(json.dumps({"filing_ok": f["read_back"]["ok"], "steps": f["steps"], "s": f["seconds"], "usd": f["est_usd"],
                      "stopped": f["stopped"], "final": (f["final"] or "")[:200],
                      "fault_rejected": not results["fault_injection"]["ok"], "lookup": results["lookup"],
                      "off_allowlist": results["off_allowlist"]}, indent=1, default=str))


if __name__ == "__main__":
    main()
