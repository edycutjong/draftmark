"""Self-test a survey program against the booklet's PRINTED worked conditions.

One sandbox launch runs: the printed rows, two out-of-range probes (must raise) and a
randomized differential against our reference program. Verdict PASS only if rows >=
ceil(0.9 N) with N >= 20, both probes raise, and the differential agrees <= 0.05 %.
"""
from __future__ import annotations

import csv
import math
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import reference_survey as R
from . import sandbox

COND = Path(__file__).resolve().parents[2] / "data" / "booklets" / "trieste" / "conditions.csv"
INPUT_KEYS = ("fore_p", "fore_s", "mid_p", "mid_s", "aft_p", "aft_s", "sg")
TRACE = ("d_fp", "d_ap", "d_ms", "d_mm", "disp_table", "corr_trim1", "corr_trim2", "corr_density", "disp_final")
PROBES = [
    {"fore_p": 0.2, "fore_s": 0.2, "mid_p": 0.2, "mid_s": 0.2, "aft_p": 0.2, "aft_s": 0.2, "sg": 1.025},
    {"fore_p": 11.0, "fore_s": 11.0, "mid_p": 11.2, "mid_s": 11.2, "aft_p": 11.4, "aft_s": 11.4, "sg": 1.025},
]


def conditions(path: Path = COND) -> list[dict]:
    with path.open() as f:
        return [{"cond_id": r["cond_id"], "page": int(r["page"]), "inputs": {k: float(r[k]) for k in INPUT_KEYS},
                 "expected": float(r["disp_printed"])} for r in csv.DictReader(f)]


def differential_cases(n: int = 200, seed: int = 7) -> list[dict]:
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        d = rnd.uniform(3.2, 8.2)
        t = rnd.uniform(-1.0, 2.0)
        lst = rnd.uniform(-0.05, 0.05)
        hog = rnd.uniform(-0.05, 0.05)
        f, a = d - t / 2, d + t / 2
        m = d - hog
        out.append({"fore_p": f + lst, "fore_s": f - lst, "mid_p": m + lst, "mid_s": m - lst,
                    "aft_p": a + lst, "aft_s": a - lst, "sg": rnd.uniform(1.000, 1.030)})
    return out


def tol_pct(expected: float) -> float:
    return max(0.1, 0.05 / expected * 100)


@dataclass
class Row:
    cond_id: str
    page: int
    expected: float
    got: float | None
    err_pct: float | None
    passed: bool
    first_diverging: str | None = None
    error: str | None = None
    trace: dict = field(default_factory=dict)


@dataclass
class SelfTest:
    program_sha: str
    rows: list[Row]
    pass_count: int
    n: int
    probes_raised: list[bool]
    differential_n: int
    differential_max_err_pct: float | None
    differential_failures: int
    verdict: str
    error: str | None = None
    wall_ms: int = 0
    ship: dict | None = None

    def as_dict(self) -> dict:
        d = asdict(self)
        d.pop("ship", None)
        return d


def first_diverging(got: dict, ref: dict) -> str | None:
    for k in TRACE:
        g, r = got.get(k), ref.get(k)
        if not isinstance(g, (int, float)):
            return k
        scale = max(1.0, abs(r))
        if abs(g - r) / scale > (1e-4 if k.startswith(("d_", "disp")) else 2e-2):
            return k
    return None


def run(code: str, booklet: dict | None = None, ship: dict | None = None, n_diff: int = 200) -> SelfTest:
    conds = conditions()
    diff = differential_cases(n_diff)
    cases = [c["inputs"] for c in conds] + PROBES + diff
    req = {"cases": cases}
    if ship is not None:
        req["ship"] = ship
    else:
        req["booklet"] = booklet
    rr = sandbox.run(code, req)
    sha = sandbox.sha256(code)
    if not rr.ok:
        return SelfTest(sha, [], 0, len(conds), [], 0, None, 0, "FAIL", error=rr.error, wall_ms=rr.wall_ms)
    res = rr.data["results"]
    rows = []
    for c, r in zip(conds, res[:len(conds)]):
        ref = R.survey(c["inputs"])
        if not r["ok"]:
            rows.append(Row(c["cond_id"], c["page"], c["expected"], None, None, False, "raised", r["error"]))
            continue
        o = r["out"]
        got = o.get("disp_final")
        err = (got - c["expected"]) / c["expected"] * 100 if isinstance(got, (int, float)) else None
        ok = err is not None and abs(err) <= tol_pct(c["expected"])
        rows.append(Row(c["cond_id"], c["page"], c["expected"], got, err, ok,
                        None if ok else first_diverging(o, ref),
                        trace={k: o.get(k) for k in TRACE + ("trim",)}))
    probes = [not r["ok"] for r in res[len(conds):len(conds) + len(PROBES)]]
    errs, fails = [], 0
    for case, r in zip(diff, res[len(conds) + len(PROBES):]):
        try:
            ref = R.survey(case)["disp_final"]
        except R.OutOfTable:
            continue
        if not r["ok"] or not isinstance(r["out"].get("disp_final"), (int, float)):
            fails += 1
            continue
        errs.append(abs(r["out"]["disp_final"] - ref) / ref * 100)
    n = len(conds)
    pc = sum(r.passed for r in rows)
    dmax = max(errs) if errs else None
    verdict = "PASS" if (n >= 20 and pc >= math.ceil(0.9 * n) and all(probes) and len(probes) == 2
                         and fails == 0 and dmax is not None and dmax <= 0.05) else "FAIL"
    return SelfTest(sha, rows, pc, n, probes, len(diff), dmax, fails, verdict, wall_ms=rr.wall_ms,
                    ship=rr.data.get("ship"))
