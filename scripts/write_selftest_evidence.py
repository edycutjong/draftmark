"""Write evidence/selftest-booklet.md from committed program runs (no network)."""
import json
import math

from _common import EVIDENCE, ROOT

from api._core import reference_survey as R
from api._core import selftest

P = ROOT / "data" / "programs" / "trieste"


def ref_row_table(conds):
    out = ["| cond | page | printed disp (t) | reference (t) | err % | booklet-verbatim (t) | err % |", "|---|---|---|---|---|---|---|"]
    for c in conds:
        a = R.survey(c["inputs"])["disp_final"]
        b = R.survey(c["inputs"], second_trim=False)["disp_final"]
        e = c["expected"]
        out.append(f"| {c['cond_id']} | {c['page']} | {e:.1f} | {a:.1f} | {(a - e) / e * 100:+.3f} | {b:.1f} | "
                   f"{(b - e) / e * 100:+.3f} |")
    return out


def run_section(name, d, title):
    att = json.loads((d / "attempts.json").read_text())
    L = [f"### {title}", "", f"Prompt manifest: bundle sha256 `{att['manifest']['bundle_sha256'][:16]}…`, system prompt "
         f"sha256 `{att['manifest']['system_sha256'][:16]}…`, pages {att['manifest']['pages']}; "
         f"{att['manifest']['leak_check']}.", "",
         "| attempt | response id | minutes | tokens in / out | est $ | outcome | rows | probes raised | differential max % |",
         "|---|---|---|---|---|---|---|---|---|"]
    tot = 0.0
    for a in att["attempts"]:
        u = a.get("usage") or {}
        tot += a.get("est_usd", 0)
        outcome = "static gate REJECTED" if (a.get("error") or "").startswith("static gate") else a.get("verdict", a.get("error"))
        rows = f"{a.get('pass_count', 0)}/{a.get('n', 22)}" if not (a.get("error") or "").startswith("static") else "-"
        dm = a.get("diff_max")
        L.append(f"| {a['attempt']} | `{a['response_id']}` | {a['minutes']} | {u.get('input_tokens')} / "
                 f"{u.get('output_tokens')} | {a.get('est_usd', 0):.3f} | {outcome} | {rows} | "
                 f"{a.get('probes') or '-'} | {'-' if dm is None else f'{dm:.5f}'} |")
        if a.get("error"):
            L.append(f"|  | | | | | `{a['error'][:120]}` | | | |")
        if a.get("failing"):
            L.append(f"|  | | | | | failing (cond, first diverging intermediate): "
                     f"{', '.join(f'{c} {k}' for c, k in a['failing'])} | | | |")
    L += ["", f"Run total: {len(att['attempts'])} Wonder calls, est ${tot:.3f}.", ""]
    return L, tot


def main():
    conds = selftest.conditions()
    n = len(conds)
    need = math.ceil(0.9 * n)
    ref_pass = sum(abs(R.survey(c["inputs"])["disp_final"] - c["expected"]) / c["expected"] * 100 <= selftest.tol_pct(c["expected"]) for c in conds)
    verb_pass = sum(abs(R.survey(c["inputs"], second_trim=False)["disp_final"] - c["expected"]) / c["expected"] * 100 <= selftest.tol_pct(c["expected"]) for c in conds)
    base = json.loads((P / "baseline_generic_selftest.json").read_text())
    proven = json.loads((P / "proven.json").read_text())
    st = json.loads((P / "run-booklet-only" / "selftest.json").read_text())
    L = ["# Wonder's Trieste survey program: self-test against the booklet's printed conditions", "",
         "Booklet: public Trieste trim & stability booklet (Ro-Ro/passenger ship, Lpp 150 m; NOT a bulk carrier).",
         "There is no scale truth here: the check is that a program reproduces the displacements the booklet itself",
         "PRINTS for its 22 worked loading conditions (`data/booklets/trieste/conditions.csv`, verified row by row,",
         "see `data/booklets/trieste/CITATION.md`).", "",
         f"**Pass rule (pre-set in the spec):** a row passes if |program - printed| / printed <= 0.1 %. Verdict PASS only if",
         f">= ceil(0.9 N) = {need} of N = {n} rows pass, both out-of-range probes raise, and 200 randomized cases agree",
         "with our reference program within 0.05 %. Every program runs in the sandbox (`api/_core/sandbox.py`: AST gate,",
         "`python -I -S` subprocess, rlimits, audit hook).", "",
         "## Result", "",
         f"- **Default proven program:** `data/programs/trieste/{proven['default_program']}` by {proven['program_author']}, "
         f"sha256 `{proven['sha256'][:16]}…`, response `{proven['response_id']}`, regenerations {proven['regen_count']}: "
         f"**{st['pass_count']} of {st['n']} printed conditions**, probes raised {st['probes_raised']}, differential "
         f"{st['differential_n']} cases max {st['differential_max_err_pct']:.5f} %, verdict **{st['verdict']}**.",
         f"- Our reference program (`api/_core/reference_survey.py`, written before Wonder was called): {ref_pass} of {n}.",
         f"- The booklet's §3.1 procedure applied verbatim (no second trim correction): {verb_pass} of {n}.",
         f"- A generic textbook template that does not read this booklet's conventions (`scripts/baseline_generic.py`): "
         f"{base['pass_count']} of {base['n']}; first diverging intermediate `d_fp` on every row.", "",
         "## What the booklet hides (and Wonder found)",
         "- Lpp = 150 m, but the mark formulas divide by 140 (the distance between the draft marks).",
         "- LCF is measured from the AP; the table's MTcm column is per DEGREE (heading) though the legend says per cm.",
         "- §3.1 omits the second (Nemoto) trim correction; without it the high-trim rows miss by up to 0.38 %.", "",
         "## Wonder runs (both real, both kept)", ""]
    a, ta = run_section("A", P / "run-booklet-only", "Run A: booklet pages only (the default proven program)")
    b, tb = run_section("B", P / "run-unece-hint", "Run B: same prompt plus one sentence: \"where the booklet's "
                        "procedure is incomplete compared with standard draught-survey practice (UNECE code), apply the "
                        "standard practice\"")
    L += a + ["Regeneration feedback gave Wonder only the failing condition ids and its OWN intermediates; the printed "
              "displacements were never in its context (asserted on the prompt bundle before every run), nor was our "
              "reference program.", ""] + b
    L += ["## Rows of the default proven program", "",
          "| cond | page | printed (t) | Wonder program (t) | err % | pass |", "|---|---|---|---|---|---|"]
    for r in st["rows"]:
        L.append(f"| {r['cond_id']} | {r['page']} | {r['expected']:.1f} | {r['got']:.1f} | {r['err_pct']:+.4f} | "
                 f"{'yes' if r['passed'] else 'NO'} |")
    L += ["", "## Reference and booklet-verbatim, row by row", ""] + ref_row_table(conds)
    L += ["", f"Spend for the Wonder program-writing spike: est ${ta + tb:.3f} (price-list estimate; rows in "
          "`evidence/api-usage.md`). Raw booklet page text is not committed (licence unstated); only its hashes.", ""]
    (EVIDENCE / "selftest-booklet.md").write_text("\n".join(L))
    print("\n".join(L[14:20]))


if __name__ == "__main__":
    main()
