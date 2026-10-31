"""Reference draft-survey program for the Trieste booklet (our code, the baseline).

Implements the booklet's own §3.1 procedure (p.21 of the booklet): drafts at marks ->
dFP/dAP/dMS -> d = (dFP + 6 dMS + dAP) / 8 -> D1 from the hydrostatic table ->
D2 = t * TPcm * 100 * (Lpp/2 - LCF) / Lpp with LCF from the AP -> D3 density, PLUS the
second trim correction (Nemoto, UNECE draught-survey code) that §3.1 omits. Measured on
the 22 printed conditions: §3.1 verbatim reproduces 14 (worst 0.378 %, error grows with
trim squared); with the second correction 22 of 22 (worst 0.060 %). Two booklet quirks:
Lpp is 150 m while the "140" in its mark formulas is the distance between the marks, and
the table's MTcm column is per DEGREE of trim (its header says MT-m/deg; the legend says /cm).
Same contract as a Wonder-written program: survey(inputs) -> dict of intermediates.
It is never shown to Wonder.
"""
from __future__ import annotations

import bisect
import csv
import math
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data" / "booklets" / "trieste"
LPP = 150.0  # booklet p.6 particulars; used in D2
FORE_MARK_FROM_FP = 1.200  # fore mark Fr.189: dFP = df - 1.200 * (da - df) / 140
AFT_MARK_FROM_AP = 8.800  # aft mark Fr.11: dAP = da + 8.800 * (da - df) / 140
L_MARKS = LPP - FORE_MARK_FROM_FP - AFT_MARK_FROM_AP  # 140 m between the marks (the booklet's "140")
SG_STD = 1.025


class OutOfTable(ValueError):
    pass


def load_table(path: Path = DATA / "hydrostatics.csv") -> list[dict]:
    with path.open() as f:
        return [{k: float(v) for k, v in r.items() if k in ("draft", "disp", "tpcm", "lcf", "mtcm")}
                for r in csv.DictReader(f)]


_TABLE: list[dict] | None = None


def table() -> list[dict]:
    global _TABLE
    if _TABLE is None:
        _TABLE = load_table()
    return _TABLE


def interp(rows: list[dict], d: float, key: str) -> float:
    xs = [r["draft"] for r in rows]
    if d < xs[0] or d > xs[-1]:
        raise OutOfTable(f"draft {d:.3f} m outside table {xs[0]}-{xs[-1]} m")
    i = bisect.bisect_right(xs, d)
    if i >= len(xs):
        return rows[-1][key]
    x0, x1 = xs[i - 1], xs[i]
    f = (d - x0) / (x1 - x0)
    return rows[i - 1][key] + f * (rows[i][key] - rows[i - 1][key])


def mtc_per_cm(rows: list[dict], d: float) -> float:
    """Moment to change trim 1 cm (t.m/cm) from the table's per-degree column."""
    return interp(rows, d, "mtcm") * 0.01 / LPP * 180 / math.pi


def survey(inputs: dict, rows: list[dict] | None = None, second_trim: bool = True) -> dict:
    rows = rows or table()
    df = (inputs["fore_p"] + inputs["fore_s"]) / 2
    dm = (inputs["mid_p"] + inputs["mid_s"]) / 2
    da = (inputs["aft_p"] + inputs["aft_s"]) / 2
    sg = inputs.get("sg", SG_STD)
    trim_marks = da - df
    d_fp = df - FORE_MARK_FROM_FP * trim_marks / L_MARKS
    d_ap = da + AFT_MARK_FROM_AP * trim_marks / L_MARKS
    d_ms = dm
    t = d_ap - d_fp
    d_mean = (d_ap + d_fp) / 2
    d_mm = (d_fp + 6 * d_ms + d_ap) / 8
    d1 = interp(rows, d_mm, "disp")
    tpcm = interp(rows, d_mm, "tpcm")
    lcf = interp(rows, d_mm, "lcf")
    d2 = t * tpcm * 100 * (LPP / 2 - lcf) / LPP
    d2b = 0.0
    if second_trim:  # Nemoto: 50 t^2 (MTC(d+0.5) - MTC(d-0.5)) / Lpp
        d2b = 50 * t * t * (mtc_per_cm(rows, d_mm + 0.5) - mtc_per_cm(rows, d_mm - 0.5)) / LPP
    d3 = (d1 + d2 + d2b) * (sg - SG_STD) / SG_STD
    disp = d1 + d2 + d2b + d3
    out = {"d_f": df, "d_m": dm, "d_a": da, "d_fp": d_fp, "d_ap": d_ap, "d_ms": d_ms, "trim": t,
           "d_mean": d_mean, "deflection": d_mean - d_ms, "d_mm": d_mm, "tpcm": tpcm, "lcf": lcf,
           "disp_table": d1, "corr_trim1": d2, "corr_trim2": d2b, "corr_density": d3, "disp_final": disp}
    ded = inputs.get("deductibles") or {}
    deductions = sum(float(v) for v in ded.values())
    out["deductions"] = deductions
    out["net"] = disp - deductions
    light = inputs.get("lightship_constant")
    out["cargo"] = out["net"] - light if light is not None else None
    return out


def survey_batch(cases: list[dict]) -> list[dict]:
    return [survey(c) for c in cases]
