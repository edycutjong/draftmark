"""Error-model check on synthetic barge geometry (no API calls): bias and coverage of +-u / +-2u.

Each seed draws a clip whose noise families differ from the estimator's model: a two-harmonic
swell of random amplitude/period/phase, per-column edge jitter and per-frame edge offsets, a
systematic crest-occlusion bias, a print stretch of the strip, and random frame drops. Truth =
the calm (equilibrium) draft. The estimator is api/_core/measure.py with the frozen nominal
systematic terms below.

  python scripts/error_model_synthetic.py [--seeds 100]
"""
import argparse
import json
import math

import numpy as np
from _common import EVIDENCE

from api._core import marks, measure
from api._core.sam import SamObject

PX_PER_MM = 6.0  # rig gate: >= 5 px/mm on the 2x crop
H, W = 720, 320
# frozen nominal systematic terms (k=1), metres
U_SYS = {"scale": 0.0004, "edge": 0.5 / PX_PER_MM / 1000, "par": 0.0003}


def clip(seed, fps=6.0, n=60):
    rng = np.random.default_rng(seed)
    calm = rng.uniform(0.105, 0.150)  # m on the strip
    top = calm + 0.75 * H / PX_PER_MM / 1000
    stretch = 1 + rng.uniform(-0.004, 0.004)  # printed pitch error
    occl = rng.uniform(0.0, 0.0004)  # crest hides the contact line: edge appears higher (m)
    a1, a2 = rng.uniform(0.002, 0.010), rng.uniform(0.0, 0.003)
    p1 = rng.uniform(1.2, 2.5)
    ph1, ph2 = rng.uniform(0, 2 * math.pi, 2)
    labs = marks.strip_sequence()
    zs = [round(cm / 100, 4) for cm in range(2, 27, 2)]
    toks_by_f, water_by_f = {}, {}
    for i in range(n):
        if rng.random() < 0.06:
            continue  # dropped frame
        t = i / fps
        level = calm + a1 * math.sin(2 * math.pi * t / p1 + ph1) + a2 * math.sin(4 * math.pi * t / p1 + ph2)
        y_of = lambda z: (top - z * stretch) * PX_PER_MM * 1000  # noqa: E731
        objs = []
        for k, (lab, z) in enumerate(zip(labs, zs)):
            yb = y_of(z)
            if not (40 < yb < H - 2):
                continue
            wdt = 70 if lab.endswith("M") else 36
            h = 60
            m = np.ones((h, wdt), dtype=bool)
            wl = y_of(level)
            if yb > wl:  # submerged part is not visible: SAM's mask stops at the water
                cut = int(max(0, min(h, h - (yb - wl))))
                m[cut:, :] = False
                if cut < 8:
                    continue
            objs.append(SamObject(i, k, (130.0, yb - h, 130.0 + wdt, yb), m))
        wl = y_of(level + occl) + rng.normal(0, 0.8)
        cols = (wl + rng.normal(0, 1.5, W)).clip(0, H - 1)
        top_row = int(cols.min())
        mask = (np.arange(top_row, H)[:, None] >= cols[None, :])
        water = SamObject(i, 0, (0.0, float(top_row), float(W), float(H)), mask)
        toks_by_f[i] = marks.group_glyphs(objs, marks.BARGE)
        water_by_f[i] = [water]
    track_z = {f"t{k}": z for k, z in enumerate(zs)}
    return toks_by_f, water_by_f, track_z, calm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=100)
    a = ap.parse_args()
    rows = []
    for s in range(a.seeds):
        toks, water, tz, calm = clip(s)
        _, r = measure.measure_clip(toks, water, tz, marks.BARGE, u_sys_parts=U_SYS)
        if r.refused:
            rows.append({"seed": s, "refused": r.reason})
            continue
        err = r.d_m - calm
        rows.append({"seed": s, "err_mm": err * 1000, "u_abs_mm": r.u_abs_m * 1000, "u_rep_mm": r.u_rep_m * 1000,
                     "in_1u": abs(err) <= r.u_abs_m, "in_2u": abs(err) <= 2 * r.u_abs_m, "kept": r.n_kept,
                     "n_eff": r.n_eff})
    ok = [r for r in rows if "err_mm" in r]
    errs = np.array([r["err_mm"] for r in ok])
    c1 = np.mean([r["in_1u"] for r in ok])
    c2 = np.mean([r["in_2u"] for r in ok])
    summ = {"seeds": a.seeds, "measured": len(ok), "refused": len(rows) - len(ok),
            "bias_mm": float(errs.mean()), "rmse_mm": float(np.sqrt((errs ** 2).mean())),
            "max_abs_err_mm": float(np.abs(errs).max()), "mean_u_abs_mm": float(np.mean([r["u_abs_mm"] for r in ok])),
            "coverage_1u": float(c1), "coverage_2u": float(c2), "target_2u": 0.90}
    L = ["# Error model on synthetic barge geometry (no API calls)", "",
         "`scripts/error_model_synthetic.py`: noise families differ from the estimator's model (two-harmonic swell,",
         "per-column edge jitter + per-frame edge offset, systematic crest-occlusion bias 0-0.4 mm, print stretch",
         "+-0.4 %, ~6 % dropped frames, submerged numerals with clipped masks). Truth = the calm draft. 60 frames at",
         f"6 fps, {PX_PER_MM:g} px/mm. Nominal systematic terms (k=1, frozen here): scale {U_SYS['scale'] * 1000:.2f} mm, "
         f"edge {U_SYS['edge'] * 1000:.3f} mm, parallax/occlusion {U_SYS['par'] * 1000:.2f} mm.", "",
         "| seeds | measured | refused | bias (mm) | RMSE (mm) | max abs err (mm) | mean u_abs (mm) | truth inside +-u | "
         "truth inside +-2u (target >= 90 %) |", "|---|---|---|---|---|---|---|---|---|",
         f"| {summ['seeds']} | {summ['measured']} | {summ['refused']} | {summ['bias_mm']:+.3f} | {summ['rmse_mm']:.3f} | "
         f"{summ['max_abs_err_mm']:.3f} | {summ['mean_u_abs_mm']:.3f} | {c1 * 100:.0f} % | {c2 * 100:.0f} % |", "",
         "This checks the estimator and its stated uncertainty on geometry we control. It is not the bucket result:",
         "real masks, glare and a real meniscus are measured on the human's clips (P1e, pre-registered protocol).", ""]
    (EVIDENCE / "error-model-synthetic.md").write_text("\n".join(L))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
