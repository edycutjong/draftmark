"""Write evidence/sam-real-clips.md from the cached spike outputs (.cache/sam, .cache/runs)."""
import json

from _common import CACHE, EVIDENCE

CLIPS = [("dB7X_t45", "dB7X-manr10"), ("UKTRQ_t20", "UKTRQ1KJ4G4"), ("eeLL_t8", "eeLL1kt2KiU")]


def main():
    L = ["# SAM 3.1 on real hull clips (P1a spike)", "",
         "Third-party public YouTube clips, used as TEST footage only: no ground truth exists for them, no frame is",
         "re-hosted here, and they never appear in the demo video. The scale-checked proof is the mini-barge (P1e).",
         "Pipeline: `scripts/prep_clip.py` (cut, crop the mark column, 2x; handheld clips use a column-tracking crop",
         "by normalised cross-correlation) -> `scripts/spike_sam.py` (SAM 3.1 video, concepts \"white number\" and",
         "\"water\", run concurrently; glyph -> token grouping) -> `scripts/spike_labels.py` (Spark 1.3 strict-JSON",
         "label reads on two frames >= 1 s apart, 5 code checks, then `api/core/measure.py`).", "",
         "| clip (source) | segment | frames | numerals found | water found | tokens/frame (median) | raw glyphs max | "
         "labels (code checks) | frames kept | draft d (m) | u_rep (m, k=1) | sd (m) | median / Huber (m) | "
         "p5-p95 swell (m) | rho1 · N_eff | drops |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    notes = []
    for stem, yt in CLIPS:
        s = json.loads((CACHE / "sam" / f"{stem}__summary.json").read_text())["summary"]
        info = json.loads((CACHE / "clips" / f"{stem}.json").read_text())
        lab = json.loads((CACHE / "runs" / f"{stem}__labels.json").read_text())
        mpath = CACHE / "runs" / f"{stem}__measure.json"
        seg = f"t={info['t0']:.0f}-{info['t0'] + info['dur']:.0f} s @ {info['fps']:.0f} fps, crop {info['box_wh'][0]}x{info['box_wh'][1]} px x2" + (", tracked" if info["tracked"] else "")
        src = f"[{yt}](https://www.youtube.com/watch?v={yt})"
        base = (f"| {src} | {seg} | {s['frames']} | {s['frames_with_numerals']}/{s['frames']} | "
                f"{s['frames_with_water']}/{s['frames']} | {s['median_tokens']} | {s['max_glyphs']} |")
        if mpath.exists():
            m = json.loads(mpath.read_text())
            r = m["result"]
            p = r["swell_p5_p95"]
            L.append(base + f" confirmed 5/5 | {r['n_kept']}/{r['n_frames']} | {r['d_m']:.3f} | {r['u_rep_m']:.3f} | "
                     f"{r['sd_m']:.3f} | {r['median_m']:.3f} / {r['huber_m']:.3f} | {p[0]:.2f}-{p[1]:.2f} | "
                     f"{r['rho1']:.2f} · {r['n_eff']:.1f} | {', '.join(f'{k} {v}' for k, v in r['drops'].items()) or 'none'} |")
        else:
            L.append(base + " REFUSED by code (see note) | - | - | - | - | - | - | - | - |")
        raws = {f: v["raw"] for f, v in lab.items()}
        rids = [v["response_id"] for v in lab.values()]
        notes.append(f"- **{stem}**: Spark reads (box number -> mark, top to bottom) {json.dumps(raws)}; "
                     f"response ids {', '.join(rids)}.")
    L += ["", "## Label reads", ""] + notes + [
        "",
        "Every token Spark named matches the painted mark visible in the annotated frame (checked by eye on the",
        "annotated crops in P1a). On the second read Spark answered \"?\" for the half-submerged tokens instead of",
        "guessing (UKTRQ: 2 tokens, eeLL: 3); the schema allows \"?\" and code treats it as no label.",
        "",
        "## Why eeLL is refused",
        "eeLL is a bow section with breaking waves and a strongly slanted mark column on a curved hull. Spark's two",
        "reads agree and are monotone, but code refuses the labels: the scale-fit residual is 8.8 px against a",
        "limit of 0.1 x pitch = 6.5 px (the marks are not on one straight scale), and the anchor check fails",
        "because SAM boxed only part of the \"10M\" mark (a 12 px wide glyph), so the token labelled \"10M\" is not",
        "geometrically wide. In the app this is the typed-labels fallback (run marked degraded). This is the",
        "intended behaviour: code, not the model, decides whether a label is trusted.",
        "",
        "## Reading the numbers",
        "- d is the mean of kept frames; u_rep is repeatability only (swell + per-frame noise, k=1), NOT absolute",
        "  accuracy: these clips have no ground truth. u_abs exists only for the calibrated mini-barge.",
        "- The swell is strongly correlated frame to frame (rho1 ~0.9), so 46-60 frames carry ~3 independent",
        "  samples (N_eff); a longer clip shrinks u_rep. A one-pitch label error would shift d by 0.20 m (ship).",
        "- Day-0 test on a different 10 s segment of the dB7X ship gave 12.756 m; this run gives 12.761 m.",
        "",
        "Cost: SAM video frames at $0.20 / 1k (price list); per-call rows in `evidence/api-usage.md`.",
    ]
    (EVIDENCE / "sam-real-clips.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[9:13]))


if __name__ == "__main__":
    main()
