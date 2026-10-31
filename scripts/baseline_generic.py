"""Generic-template baseline: a textbook draft-survey program that does NOT read this
booklet's conventions, run through the same sandbox self-test as Wonder's program.

Textbook assumptions it makes (each one wrong for this booklet): LCF is measured from
midships; the table's MTC column is per cm; the "140" in the mark formulas is Lpp.
It reads OUR extracted table (passed as `ship`), so only the conventions differ.

  python scripts/baseline_generic.py
"""
import csv
import json

from _common import CACHE, ROOT

from api._core import selftest

TEMPLATE = '''import bisect, math

def parse_booklet(booklet):
    return {}

def _interp(rows, d, key):
    xs = [r["draft"] for r in rows]
    if d < xs[0] or d > xs[-1]:
        raise OutOfTable("draft outside table")
    i = min(max(bisect.bisect_right(xs, d), 1), len(xs) - 1)
    f = (d - xs[i - 1]) / (xs[i] - xs[i - 1])
    return rows[i - 1][key] + f * (rows[i][key] - rows[i - 1][key])

def survey(inp, ship):
    rows, lbp = ship["table"], ship["lbp"]
    df = (inp["fore_p"] + inp["fore_s"]) / 2
    dm = (inp["mid_p"] + inp["mid_s"]) / 2
    da = (inp["aft_p"] + inp["aft_s"]) / 2
    t_obs = da - df
    lbm = lbp - ship["fore_mark_from_fp"] - ship["aft_mark_from_ap"]
    d_fp = df - ship["fore_mark_from_fp"] * t_obs / lbm
    d_ap = da + ship["aft_mark_from_ap"] * t_obs / lbm
    t = d_ap - d_fp
    d_mm = (d_fp + 6 * dm + d_ap) / 8
    d1 = _interp(rows, d_mm, "disp")
    tpc = _interp(rows, d_mm, "tpcm")
    lcf_mid = _interp(rows, d_mm, "lcf")          # textbook: LCF from midships
    c1 = t * lcf_mid * tpc * 100 / lbp
    mtc = lambda d: _interp(rows, d, "mtcm")      # textbook: MTC per cm
    c2 = 50 * t * t * (mtc(d_mm + 0.5) - mtc(d_mm - 0.5)) / lbp
    c3 = (d1 + c1 + c2) * (inp["sg"] - 1.025) / 1.025
    return {"d_fp": d_fp, "d_ap": d_ap, "d_ms": dm, "trim": t, "d_mm": d_mm, "disp_table": d1,
            "corr_trim1": c1, "corr_trim2": c2, "corr_density": c3, "disp_final": d1 + c1 + c2 + c3}
'''


def ship_from_csv() -> dict:
    with (ROOT / "data" / "booklets" / "trieste" / "hydrostatics.csv").open() as f:
        rows = [{k: float(r[k]) for k in ("draft", "disp", "tpcm", "lcf", "mtcm")} for r in csv.DictReader(f)]
    return {"table": rows, "lbp": 140.0, "fore_mark_from_fp": 1.2, "aft_mark_from_ap": 8.8}


def main():
    st = selftest.run(TEMPLATE, ship=ship_from_csv())
    out = st.as_dict()
    (CACHE / "baseline_selftest.json").write_text(json.dumps(out, indent=1, default=float))
    (ROOT / "data" / "programs" / "trieste").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "programs" / "trieste" / "baseline_generic_selftest.json").write_text(
        json.dumps(out, indent=1, default=float))
    print(json.dumps({"verdict": st.verdict, "pass": st.pass_count, "n": st.n, "probes": st.probes_raised,
                      "diff_max": st.differential_max_err_pct, "error": st.error,
                      "worst_rows": sorted(((r.cond_id, round(r.err_pct, 3), r.first_diverging) for r in st.rows
                                            if r.err_pct is not None), key=lambda x: -abs(x[1]))[:5]},
                     default=float))


if __name__ == "__main__":
    main()
