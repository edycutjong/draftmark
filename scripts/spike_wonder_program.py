"""P1a spike: Muse Wonder 1.0 writes the Trieste survey program from the booklet's own
pages; the sandbox self-test proves it against the PRINTED conditions.

  python scripts/spike_wonder_program.py /path/to/booklet.pdf [--max-regen 3] [--baseline-only]

Wonder's prompt = raw page text (particulars p4, procedure p21-22, calculation sheet p26,
hydrostatic table p36-39) + each condition's INPUT drafts. Never the printed displacements
(asserted), never our reference program. Regeneration feedback = failing cond_ids + the
program's own intermediates. The raw page text stays in .cache/ (third-party, not
committed); its sha256 manifest is recorded.
"""
import argparse
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

from _common import CACHE, ROOT, meta

from api._core import selftest

PAGES = [4, 21, 22, 26, 36, 37, 38, 39]
OUTDIR = CACHE / "wonder"
PROGRAMS = ROOT / "data" / "programs" / "trieste" / "run-unece-hint"

SYSTEM = """You write draft-survey software for ship surveyors. Write ONE self-contained Python 3 file for the ship
whose stability booklet pages are given below. It must define exactly:

  parse_booklet(booklet) -> dict
      booklet = {"pages": {"<page number>": "<raw text of that page as printed>"}}.
      Extract from the raw text everything the survey needs (particulars, draft-mark positions, the hydrostatic
      table). Return JSON-serialisable data only (dicts, lists, numbers, strings).
  survey(inputs, ship) -> dict
      inputs: fore_p, fore_s, mid_p, mid_s, aft_p, aft_s = drafts read at the draft marks in metres (port and
      starboard), sg = specific gravity of the dock water. ship = the dict parse_booklet returned.
      Return at least these floats: d_fp, d_ap, d_ms, trim, d_mm, disp_table, corr_trim1, corr_trim2,
      corr_density, disp_final (tonnes). corr_trim2 is 0.0 if you apply no second trim correction.
      Raise OutOfTable (a ValueError subclass already defined in the global namespace; do not define it) when a
      draft falls outside the hydrostatic table.

Rules: follow THIS booklet's own conventions exactly (units, reference points, which length is which, column
units).{UNECE}
Allowed imports: math, bisect, json, statistics, re. No file, network or OS access, no eval/exec, no dunder
attributes. Pure functions. Reply with the complete file in a single ```python block and nothing else."""
UNECE_SENTENCE = (" Where the booklet's procedure is incomplete compared with standard draught-survey practice (UNECE "
                  "Code of\nuniform standards and procedures for draught surveys), apply the standard practice and say "
                  "which in a comment.")
SYSTEM = SYSTEM.replace("{UNECE}", UNECE_SENTENCE)


def build_bundle(pdf: Path) -> tuple[dict, str]:
    pages = {}
    for p in PAGES:
        pages[str(p)] = subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), str(pdf), "-"],
                                       capture_output=True, text=True, check=True).stdout
    conds = selftest.conditions()
    inputs = [{"cond_id": c["cond_id"], **c["inputs"]} for c in conds]
    blob = json.dumps(pages, sort_keys=True)
    leaks = []
    for c in conds:
        v = c["expected"]
        for s in {f"{v:.1f}", f"{v:,.1f}".replace(",", " "), f"{v:.2f}".replace(",", " ")}:
            if s in blob:
                leaks.append(s)
    if leaks:
        raise SystemExit(f"LEAK: printed displacements in the prompt bundle: {leaks}")
    text = "Booklet pages (raw text as printed):\n\n" + "\n\n".join(
        f"===== PAGE {p} =====\n{t}" for p, t in pages.items())
    text += ("\n\n===== Draft readings to be surveyed (inputs only) =====\n" + json.dumps(inputs))
    return {"pages": pages}, text


def extract_code(resp: dict) -> str | None:
    txt = meta.output_text(resp)
    m = re.search(r"```python\s*\n(.*?)```", txt, re.S)
    return m.group(1) if m else None


def generate(cl, messages: list, feature: str, max_out: int) -> dict:
    body = {"model": meta.WONDER, "input": messages, "max_output_tokens": max_out,
            "reasoning": {"effort": "medium"}, "background": True, "store": True}
    try:
        resp = cl.responses(body, feature + " (submit)")
    except meta.MetaError as e:
        if e.status == 400 and "background" in str(e).lower():
            body.pop("background")
            body.pop("store")
            return cl.responses(body, feature + " (sync; background rejected)", timeout=1200)
        raise
    if resp.get("status") in ("queued", "in_progress"):
        return cl.poll(resp["id"], feature, every=8, max_wait=1500)
    return resp


def feedback(st) -> str:
    fails = [r for r in st.rows if not r.passed]
    lines = []
    for r in fails:
        tr = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.trace.items()}
        lines.append(f"cond {r.cond_id}: {r.error or ''} your intermediates {json.dumps(tr)}")
    msg = (f"Self-test result: {st.pass_count} of {st.n} printed loading conditions reproduced within 0.1 % of the "
           f"booklet's printed displacement. Out-of-range probes raised: {st.probes_raised}. ")
    if st.error:
        msg += f"The program did not run: {st.error}. "
    if lines:
        msg += "Failing conditions (the printed values are withheld):\n" + "\n".join(lines)
    msg += ("\nRe-read the booklet pages, find what your program gets wrong, and reply with the complete corrected "
            "file in a single ```python block.")
    return msg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--max-regen", type=int, default=3)
    ap.add_argument("--max-out", type=int, default=16000)
    ap.add_argument("--no-standard-hint", action="store_true",
                    help="ablation: drop the 'apply UNECE practice where the booklet is incomplete' sentence")
    a = ap.parse_args()
    global OUTDIR, PROGRAMS, SYSTEM
    if a.no_standard_hint:
        SYSTEM = SYSTEM.replace(UNECE_SENTENCE, "")
        assert "UNECE" not in SYSTEM
        OUTDIR = OUTDIR / "no-hint"
        PROGRAMS = PROGRAMS.parent / "run-booklet-only"
    OUTDIR.mkdir(parents=True, exist_ok=True)
    PROGRAMS.mkdir(parents=True, exist_ok=True)
    booklet, bundle = build_bundle(Path(a.pdf))
    manifest = {"pages": PAGES, "bundle_sha256": hashlib.sha256(bundle.encode()).hexdigest(),
                "system_sha256": hashlib.sha256(SYSTEM.encode()).hexdigest(),
                "page_sha256": {p: hashlib.sha256(t.encode()).hexdigest() for p, t in booklet["pages"].items()},
                "leak_check": "no printed displacement string found in the bundle"}
    (OUTDIR / "bundle.txt").write_text(bundle)
    (OUTDIR / "booklet_pages.json").write_text(json.dumps(booklet))
    cl = meta.Client(run_id="p1a-wonder-trieste")
    messages = [{"type": "message", "role": "system", "content": [{"type": "input_text", "text": SYSTEM}]},
                {"type": "message", "role": "user", "content": [{"type": "input_text", "text": bundle}]}]
    attempts = []
    for attempt in range(1, a.max_regen + 2):
        t0 = time.time()
        resp = generate(cl, messages, f"wonder program trieste attempt {attempt}", a.max_out)
        code = extract_code(resp)
        u = resp.get("usage") or {}
        rec = {"attempt": attempt, "response_id": resp.get("id"), "status": resp.get("status"),
               "minutes": round((time.time() - t0) / 60, 2), "usage": u,
               "est_usd": meta.estimate_usd(meta.WONDER, u)}
        if code is None:
            rec["error"] = "no python block in reply"
            attempts.append(rec)
            messages += [{"type": "message", "role": "assistant",
                          "content": [{"type": "output_text", "text": meta.output_text(resp)[:4000]}]},
                         {"type": "message", "role": "user", "content": [{"type": "input_text",
                          "text": "Reply with the complete file in a single ```python block."}]}]
            continue
        (OUTDIR / f"attempt{attempt}.py").write_text(code)
        st = selftest.run(code, booklet=booklet)
        rec.update(sha=st.program_sha, verdict=st.verdict, pass_count=st.pass_count, n=st.n,
                   probes=st.probes_raised, diff_max=st.differential_max_err_pct, diff_fail=st.differential_failures,
                   error=st.error, failing=[(r.cond_id, r.first_diverging) for r in st.rows if not r.passed],
                   sandbox_ms=st.wall_ms)
        attempts.append(rec)
        (OUTDIR / f"attempt{attempt}_selftest.json").write_text(json.dumps(st.as_dict(), indent=1, default=float))
        (PROGRAMS / f"attempt{attempt}_selftest.json").write_text(json.dumps(st.as_dict(), indent=1, default=float))
        print(json.dumps({k: v for k, v in rec.items() if k != "usage"}, default=float))
        if st.verdict == "PASS":
            (PROGRAMS / "program.py").write_text(code)
            (PROGRAMS / "ship.json").write_text(json.dumps(st.ship, indent=1))
            (PROGRAMS / "selftest.json").write_text(json.dumps(st.as_dict(), indent=1, default=float))
            break
        if attempt <= a.max_regen:
            messages += [{"type": "message", "role": "assistant",
                          "content": [{"type": "output_text", "text": "```python\n" + code + "```"}]},
                         {"type": "message", "role": "user", "content": [{"type": "input_text", "text": feedback(st)}]}]
    (OUTDIR / "attempts.json").write_text(json.dumps({"manifest": manifest, "attempts": attempts}, indent=1,
                                                    default=float))
    for i, rec in enumerate(attempts, 1):
        if rec.get("sha"):
            (PROGRAMS / f"attempt{rec['attempt']}.py").write_text((OUTDIR / f"attempt{rec['attempt']}.py").read_text())
    (PROGRAMS / "attempts.json").write_text(json.dumps({"manifest": manifest, "attempts": attempts}, indent=1,
                                                       default=float))
    print("total est $", round(sum(r.get("est_usd", 0) for r in attempts), 4))


if __name__ == "__main__":
    main()
