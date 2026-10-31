"""Render a synthetic mini-barge clip with KNOWN truth (our own pixels, no third-party footage).

The 1:10 strip (white digits on dark red; bottom edge = draft) seen as a 2x crop, water
with a swell + ripple whose mean surface is the true draft. Writes OUT.mp4 (+ .webm with
--webm) and OUT.truth.json (per-frame true draft, mean).

  python scripts/synth_clip.py OUT.mp4 --mean-mm 112.0 --amp-mm 8 --frames 60 --fps 6 --seed 1 [--webm]
"""
import argparse
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def render(mean_mm, amp_mm, n, fps, seed, w=320, h=720, px_per_mm=6.0, top_mm=None):
    rng = np.random.default_rng(seed)
    top_mm = top_mm if top_mm is not None else mean_mm + 0.75 * h / px_per_mm  # draft at the top row
    y_of = lambda mm: (top_mm - mm) * px_per_mm  # noqa: E731
    font = ImageFont.truetype(FONT, int(10 * px_per_mm / 0.716))
    period = rng.uniform(1.4, 2.2)
    phase = rng.uniform(0, 2 * math.pi)
    frames, truth = [], []
    base = Image.new("RGB", (w, h), (108, 16, 16))
    d = ImageDraw.Draw(base)
    for cm in range(2, 27, 2):
        mm = cm * 10
        lab = f"{cm // 10}M" if cm % 10 == 0 else str(cm % 10)
        yb = y_of(mm)
        if -80 < yb < h + 80:
            bb = d.textbbox((0, 0), lab, font=font)
            d.text((w * 0.38 - bb[0], yb - bb[3]), lab, font=font, fill=(240, 236, 228))
    hull = np.array(base, dtype=np.float32)
    hull += rng.normal(0, 4, hull.shape)
    xs = np.arange(w)
    for i in range(n):
        t = i / fps
        level = mean_mm + amp_mm * math.sin(2 * math.pi * t / period + phase) + rng.normal(0, 0.4)
        truth.append(level)
        ripple = 1.2 * np.sin(xs / 17.0 + 3 * t) + 0.6 * np.sin(xs / 7.0 - 5 * t)
        surf = y_of(level) - ripple * px_per_mm / 4
        img = hull.copy()
        yy = np.arange(h)[:, None]
        water = yy >= surf[None, :]
        tex = 40 + 18 * np.sin(yy / 9.0 + xs[None, :] / 23.0 + t) + rng.normal(0, 6, (h, w))
        wat = np.stack([tex * 0.35, tex * 0.9 + 20, tex * 0.85 + 15], axis=-1)
        img = np.where(water[..., None], wat, img)
        frames.append(np.clip(img, 0, 255).astype(np.uint8))
    return frames, truth, {"period_s": period, "px_per_mm": px_per_mm, "top_mm": top_mm}


def encode(frames, fps, out: Path, codec_args):
    h, w, _ = frames[0].shape
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                          "-r", str(fps), "-i", "-", *codec_args, str(out)], stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(f.tobytes())
    p.stdin.close()
    p.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--mean-mm", type=float, default=112.0)
    ap.add_argument("--amp-mm", type=float, default=8.0)
    ap.add_argument("--frames", type=int, default=60)
    ap.add_argument("--fps", type=float, default=6.0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--webm", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    frames, truth, meta = render(a.mean_mm, a.amp_mm, a.frames, a.fps, a.seed)
    encode(frames, a.fps, out, ["-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p"])
    if a.webm:
        encode(frames, a.fps, out.with_suffix(".webm"), ["-c:v", "libvpx-vp9", "-b:v", "1M"])
    info = {"source": "synthetic (scripts/synth_clip.py)", "t0": 0, "dur": a.frames / a.fps, "fps": a.fps, "scale": 1,
            "box_wh": [frames[0].shape[1], frames[0].shape[0]], "frames": a.frames, "tracked": False,
            "seed": a.seed, "truth_mm": truth, "truth_mean_mm": float(np.mean(truth)), **meta}
    out.with_suffix(".json").write_text(json.dumps(info))
    print(json.dumps({k: v for k, v in info.items() if k != "truth_mm"}))


if __name__ == "__main__":
    main()
