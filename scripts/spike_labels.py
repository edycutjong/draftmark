"""P1a spike: Spark 1.3 reads the mark tokens on two annotated frames (>= 1 s apart),
code runs the five checks, then the error model measures the clip.

  python scripts/spike_labels.py .cache/clips/dB7X_t45.mp4 [--scale 1.0] [--frames 0,30]
Needs spike_sam.py's cached SAM text. Writes .cache/runs/<clip>.json (gitignored).
"""
import argparse
import json
from pathlib import Path

import cv2
from PIL import Image
from _common import CACHE, meta

from api._core import labels, marks, measure, sam


def frame_image(clip: Path, i: int) -> Image.Image:
    cap = cv2.VideoCapture(str(clip))
    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
    ok, fr = cap.read()
    cap.release()
    if not ok:
        raise SystemExit(f"cannot read frame {i}")
    return Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--frames", default="")
    a = ap.parse_args()
    clip = Path(a.clip)
    info = json.loads(clip.with_suffix(".json").read_text())
    system = marks.MarkSystem(scale=a.scale)
    num = sam.by_frame(sam.parse((CACHE / "sam" / f"{clip.stem}__white_number.txt").read_text()))
    wat = sam.by_frame(sam.parse((CACHE / "sam" / f"{clip.stem}__water.txt").read_text()))
    toks = {}
    for i in range(info["frames"]):
        try:
            toks[i] = marks.group_glyphs(num.get(i, []), system)
        except marks.ObjectCapError:
            toks[i] = []
    gap = max(1, int(round(info["fps"])))  # >= 1 s apart
    if a.frames:
        f1, f2 = (int(x) for x in a.frames.split(","))
    else:
        order = sorted(toks, key=lambda i: (-len(toks[i]), i))
        f1 = order[0]
        f2 = next(i for i in order if abs(i - f1) >= gap)
    cache = CACHE / "runs" / f"{clip.stem}__labels.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        reads = json.loads(cache.read_text())
    else:
        cl = meta.Client(run_id=f"p1a-labels-{clip.stem}")
        reads = {}
        for f in (f1, f2):
            img, numbering = labels.annotate(frame_image(clip, f), toks[f])
            img.save(CACHE / "runs" / f"{clip.stem}__annotated_{f}.jpg")
            by_track, meta_ = labels.read(cl, img, numbering, system, feature=f"spark labels {clip.stem} f{f}")
            reads[str(f)] = {"by_track": by_track, **meta_, "numbering": numbering}
        cache.write_text(json.dumps(reads, indent=1))
    r1, r2 = reads[str(f1)]["by_track"], reads[str(f2)]["by_track"]
    drafts, chk = marks.check_labels(toks[f1], r1, r2, system)
    print("reads:", json.dumps({k: v["raw"] for k, v in reads.items()}))
    print("checks:", json.dumps(chk.as_dict()))
    if not chk.ok:
        print("LABELS NOT CONFIRMED -> typed fallback in the app")
        return
    # tokens labelled in frame 2 only (tracks) get the draft implied by the label grammar too
    frames, res = measure.measure_clip(toks, wat, drafts, system)
    out = {"clip": clip.stem, "source": info["source"], "t0": info["t0"], "fps": info["fps"],
           "label_frames": [f1, f2], "checks": chk.as_dict(), "drafts_by_track": drafts,
           "result": res.as_dict(), "frames": [f.__dict__ for f in frames]}
    (CACHE / "runs" / f"{clip.stem}__measure.json").write_text(json.dumps(out, indent=1, default=float))
    r = res
    print(json.dumps({"d_m": r.d_m, "u_rep_m": r.u_rep_m, "n_kept": r.n_kept, "n_frames": r.n_frames,
                      "outliers": r.n_outliers, "n_eff": r.n_eff, "rho1": r.rho1, "sd_m": r.sd_m,
                      "median_m": r.median_m, "huber_m": r.huber_m, "p5_p95": r.swell_p5_p95,
                      "pitch_px": r.pitch_px_median, "drops": r.drops, "refused": r.refused, "reason": r.reason},
                     indent=1, default=float))


if __name__ == "__main__":
    main()
