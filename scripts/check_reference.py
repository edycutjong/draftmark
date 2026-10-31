"""Run a survey program against the Trieste printed conditions (no network).

  python scripts/check_reference.py            # our reference program
  python scripts/check_reference.py --verbatim # booklet §3.1 only (no second trim correction)
Prints one row per condition and the pass count. Row pass = |err| <= max(0.1 %, half the
printed rounding unit (0.05 t) / expected).
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from api.core import reference_survey as R  # noqa: E402

COND = ROOT / "data" / "booklets" / "trieste" / "conditions.csv"
KEYS = ("fore_p", "fore_s", "mid_p", "mid_s", "aft_p", "aft_s", "sg")


def rows():
    with COND.open() as f:
        for r in csv.DictReader(f):
            yield r["cond_id"], {k: float(r[k]) for k in KEYS}, float(r["disp_printed"]), r


def tol_pct(expected: float) -> float:
    return max(0.1, 0.05 / expected * 100)


def main():
    second = "--verbatim" not in sys.argv
    n = ok = 0
    worst = 0.0
    for cid, inp, exp, _ in rows():
        o = R.survey(inp, second_trim=second)
        err = (o["disp_final"] - exp) / exp * 100
        p = abs(err) <= tol_pct(exp)
        n += 1
        ok += p
        worst = max(worst, abs(err))
        print(f"{cid:>4}  printed {exp:9.1f}  ref {o['disp_final']:9.1f}  err {err:+.3f} %  trim {o['trim']:+.3f} m  "
              f"D2 {o['corr_trim1']:+7.1f}  {'PASS' if p else 'FAIL'}")
    print(f"reference{'' if second else ' (booklet-verbatim, no 2nd trim corr)'}: {ok} of {n} printed conditions within tolerance; worst |err| {worst:.3f} %")
    return 0 if ok == n else 1


if __name__ == "__main__":
    sys.exit(main())
