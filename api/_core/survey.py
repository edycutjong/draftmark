"""Survey station: the proven program computes displacement, code computes everything around it.

Ship mode runs the cached Wonder-written program (the one that passed the Trieste self-test) in ONE
sandbox launch: the survey case, a +1 mm case per position (t per mm, shown on the draft sheet) and
the live positions moved together by +-u (the finite-difference uncertainty). Barge mode is the
analytic box (program_author: analytic), in-process because no model wrote it.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from . import barge as B
from . import reference_survey as R
from . import sandbox

DATA = Path(__file__).resolve().parents[2] / "data"
POSITIONS = ("fore_p", "fore_s", "mid_p", "mid_s", "aft_p", "aft_s")
# share of each position in the quarter mean (F + 6M + A) / 8, P and S averaged first
WEIGHTS = {"fore_p": 1 / 16, "fore_s": 1 / 16, "mid_p": 6 / 16, "mid_s": 6 / 16, "aft_p": 1 / 16, "aft_s": 1 / 16}
# entered-draft plausibility gate (frozen, complexity.md §1 row 4)
GATE_HOG_M, GATE_PS_M = 0.15, 0.30
# trim range the self-test's differential cases covered (selftest.differential_cases: -1.0 .. +2.0 m)
TRIM_PROVEN_M = (-1.0, 2.0)
NEMOTO_DD_M = 0.5  # the program's second trim correction reads MTC at d_mm +- this
MM = 0.001


def booklets() -> set[str]:
    """Booklets with a proven program on disk; anything else (incl. "../x") is refused before a path is built."""
    return {p.parent.name for p in (DATA / "programs").glob("*/proven.json")}


def booklet_meta(booklet: str = "trieste") -> dict:
    """What the certificate prints about the vessel: from our booklet data only."""
    b = json.loads((DATA / "booklets" / booklet / "booklet.json").read_text())
    return {"id": b.get("id", booklet), "vessel": b.get("vessel"), "source_url": b.get("source_url")}


def proven(booklet: str = "trieste") -> dict:
    """The default proven program for a booklet: code, ship JSON, self-test summary, attempts."""
    if booklet not in booklets():
        raise KeyError(booklet)
    root = DATA / "programs" / booklet
    meta = json.loads((root / "proven.json").read_text())
    run_dir = (root / meta["default_program"]).parent
    code = (root / meta["default_program"]).read_text()
    if sandbox.sha256(code) != meta["sha256"]:
        raise RuntimeError("proven program sha mismatch")
    st = json.loads((run_dir / "selftest.json").read_text())
    ship_txt = (run_dir / "ship.json").read_text()
    if meta.get("ship_sha256") and sandbox.sha256(ship_txt) != meta["ship_sha256"]:
        raise RuntimeError("ship.json does not match the proven manifest")
    if st.get("program_sha") != meta["sha256"] or st.get("verdict") != "PASS":
        raise RuntimeError("recorded self-test is not a PASS of this program")  # never certify on a stale proof
    att = json.loads((run_dir / "attempts.json").read_text())
    return {"meta": meta, "code": code, "ship": json.loads(ship_txt), "selftest": st,
            "attempts": att, "run": run_dir.name}


def selftest_summary(st: dict) -> dict:
    return {"verdict": st["verdict"], "pass_count": st["pass_count"], "n": st["n"],
            "probes_raised": st.get("probes_raised"), "differential_n": st.get("differential_n"),
            "differential_max_err_pct": st.get("differential_max_err_pct"), "program_sha": st["program_sha"]}


def failed_rows(st: dict) -> list[dict]:
    return [{"cond_id": r["cond_id"], "d_mm": r["trace"]["d_mm"], "trim": r["trace"]["trim"]}
            for r in st.get("rows", []) if not r.get("passed") and r.get("trace")]


def gate(drafts: dict[str, float], out: dict | None) -> list[str]:
    """Plausibility of the six drafts. Returns the failed sub-checks (empty = consistent)."""
    bad = []
    for a, b in (("fore_p", "fore_s"), ("mid_p", "mid_s"), ("aft_p", "aft_s")):
        if abs(drafts[a] - drafts[b]) > GATE_PS_M:
            bad.append(f"{a[:-2]} port/starboard differ by {abs(drafts[a] - drafts[b]):.3f} m > {GATE_PS_M} m")
    if out:
        hog = out["d_ms"] - (out["d_fp"] + out["d_ap"]) / 2
        if abs(hog) > GATE_HOG_M:
            bad.append(f"implied hog/sag {hog:+.3f} m beyond +-{GATE_HOG_M} m")
        trim = out["d_ap"] - out["d_fp"]
        if not TRIM_PROVEN_M[0] <= trim <= TRIM_PROVEN_M[1]:
            bad.append(f"implied trim {trim:+.3f} m outside the self-tested range {TRIM_PROVEN_M}")
    return bad


def ship(inp: dict, prog: dict | None = None) -> dict:
    """inp: {drafts: {pos: m}, sources: {pos: live|clip|entered}, u_live_m, sg, deductibles: {..: t},
    lightship_constant?, initial_net?}. Returns intermediates, disp, net, cargo, u_cargo and gate facts."""
    prog = prog or proven()
    drafts = {p: float(inp["drafts"][p]) for p in POSITIONS}
    sources = {p: (inp.get("sources") or {}).get(p, "entered") for p in POSITIONS}
    sg = float(inp.get("sg", 1.025))
    live = [p for p in POSITIONS if sources[p] in ("live", "clip")]
    u_live = float(inp.get("u_live_m") or 0.0)
    base = {**drafts, "sg": sg}
    cases = [base]
    for p in POSITIONS:
        cases.append({**base, p: drafts[p] + MM})
    if live and u_live > 0:
        cases.append({**base, **{p: drafts[p] + u_live for p in live}})
        cases.append({**base, **{p: drafts[p] - u_live for p in live}})
    rr = sandbox.run(prog["code"], {"ship": prog["ship"], "cases": cases})
    out: dict = {"program_sha": prog["meta"]["sha256"], "program_author": prog["meta"]["program_author"],
                 "response_id": prog["meta"].get("response_id"), "regen_count": prog["meta"].get("regen_count"),
                 "drafts": drafts, "sources": sources, "weights": WEIGHTS, "sg": sg, "sandbox_ms": rr.wall_ms,
                 "n_cases": len(cases), "out_of_table": False, "perturb_oot": False, "error": None}
    if not rr.ok:
        out["error"] = rr.error
        return out
    res = rr.data["results"]
    if not res[0]["ok"]:
        out["out_of_table"] = "OutOfTable" in (res[0]["error"] or "")
        out["error"] = res[0]["error"]
        out["gate_fail"] = gate(drafts, None)
        return out
    o = res[0]["out"]
    rows = R.table()
    lo, hi = rows[0]["draft"] + NEMOTO_DD_M, rows[-1]["draft"] - NEMOTO_DD_M
    if not lo <= o["d_mm"] <= hi:  # the second trim correction reads MTC at d +-0.5 m: never extrapolate it
        out["out_of_table"] = True
        out["error"] = f"OutOfTable: mean draft {o['d_mm']:.3f} m needs MTC at +-{NEMOTO_DD_M} m inside {lo}-{hi} m"
        out["gate_fail"] = gate(drafts, None)
        return out
    disp = o["disp_final"]
    t_per_mm = {}
    for p, r in zip(POSITIONS, res[1:7]):
        t_per_mm[p] = (r["out"]["disp_final"] - disp) / 1.0 if r["ok"] else None
    u_disp = 0.0
    if len(res) > 7:
        up, dn = res[7], res[8]
        if not (up["ok"] and dn["ok"]) or not all(lo <= r["out"]["d_mm"] <= hi for r in (up, dn)):
            out["perturb_oot"] = True
        else:
            u_disp = abs(up["out"]["disp_final"] - dn["out"]["disp_final"]) / 2
    ded = {k: float(v) for k, v in (inp.get("deductibles") or {}).items() if v not in (None, "")}
    deductions = sum(ded.values())
    net = disp - deductions
    if inp.get("initial_net") not in (None, ""):
        cargo, kind = net - float(inp["initial_net"]), "paired"
    elif inp.get("lightship_constant") not in (None, ""):
        cargo, kind = net - float(inp["lightship_constant"]), "single"
    else:
        cargo, kind = None, None
    d_mm = o["d_mm"]
    tpc = R.interp(rows, d_mm, "tpcm") if rows[0]["draft"] <= d_mm <= rows[-1]["draft"] else None
    out.update(trace={k: o.get(k) for k in ("d_fp", "d_ap", "d_ms", "d_mm", "trim", "disp_table", "corr_trim1",
                                             "corr_trim2", "corr_density", "disp_final")},
               disp=disp, t_per_mm=t_per_mm, u_disp=u_disp, deductibles=ded, deductions=deductions, net=net,
               cargo=cargo, cargo_kind=kind, u_cargo=u_disp if cargo is not None else None,
               u_label="draft + geometry uncertainty only — excludes entered drafts and deductibles",
               n_entered=sum(sources[p] == "entered" for p in POSITIONS), d_mm=d_mm, trim=o["d_ap"] - o["d_fp"],
               consequence={"tpc_t_per_cm": tpc, "d_mm": d_mm} if tpc else None,
               gate_fail=gate(drafts, o))
    out["entered_inconsistent"] = bool(out["gate_fail"])
    return out


def barge_from(booklet: dict) -> B.Barge:
    b = booklet["barge"]
    return B.Barge(b["L_m"], b["B_m"], b["light_kg"], b.get("zero_offset_m", 0.0), b.get("rho_kg_m3", 997.0))


def barge_booklet(name: str = "minibarge") -> dict:
    return json.loads((DATA / "booklets" / name / "booklet.synthetic.json").read_text())


def barge(inp: dict, booklet: dict | None = None) -> dict:
    """inp: {d_m, u_m (u_abs if calibrated else u_rep), what_if?: {rho_kg_m3?, L_m?, B_m?}, expected_u_kg?}."""
    booklet = booklet or barge_booklet()
    b0 = barge_from(booklet)
    wi = {k: v for k, v in (inp.get("what_if") or {}).items() if v not in (None, "")}
    b = B.Barge(float(wi.get("L_m", b0.L_m)), float(wi.get("B_m", b0.B_m)), b0.light_kg, b0.zero_offset_m,
                float(wi.get("rho_kg_m3", b0.rho_kg_m3)))
    what_if = b != b0
    out = {"program_author": "analytic", "barge": b.__dict__, "booklet_id": booklet.get("id"),
           "booklet_note": booklet.get("note"), "what_if": what_if, "out_of_table": False, "perturb_oot": False}
    d, u = float(inp["d_m"]), float(inp.get("u_m") or 0.0)
    try:
        s = B.survey(b, d, u, booklet.get("u_geom"))
    except ValueError as e:
        out.update(out_of_table=True, error=str(e))
        return out
    for dd in (d - u, d + u):
        try:
            B.displacement_kg(b, dd)
        except ValueError:
            out["perturb_oot"] = True
    out.update(trace={"T_m": s["T_m"], "area_m2": s["area_m2"], "rho": s["rho"]}, disp=s["disp_kg"],
               light=s["light_kg"], cargo=s["cargo_kg"], u_disp=s["u_disp_kg"], u_cargo=s["u_cargo_kg"],
               u_label="draft + geometry + density + scale uncertainty (k=1)",
               consequence={"g_per_mm": b.rho_kg_m3 * b.area_m2, "kg_per_mm": b.rho_kg_m3 * b.area_m2 / 1000},
               expected_u=inp.get("expected_u_kg"))
    return out


def isfinite(x) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x)
