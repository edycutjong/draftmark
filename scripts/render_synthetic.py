"""Render the SYNTHETIC mini-barge loads (P1e): code-drawn pixels, NOT a filmed clip, NOT an AI image/video model.

For each registered load the true draft is physics: T = (light + cargo) / (rho * L * B) with the analytic barge from
data/booklets/minibarge (100 x 100 mm box, 0.18 kg light weight, rho 997). The 1:10 strip (white numerals on dark
red, a numeral's bottom edge = its stated draft) is drawn at that draft, a swell of 2-6 mm amplitude moves the
waterline, and the camera adds blur, exposure drift, sensor noise and MP4 compression. Fixed seeds.

Truth goes to a sidecar CSV (data/synthetic/truth.csv) that the measuring flow never reads: the flow only gets the MP4.

  python scripts/render_synthetic.py [--out .cache/synthetic] [--only 7]
"""
import argparse
import csv
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from _common import ROOT

from api._core import survey

FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
W, H, PX_PER_MM, FPS, N = 320, 720, 5.0, 6.0, 60  # the 2x crop of the mark column; 5 px/mm = the rig gate floor
LOADS_KG = [0.6, 0.7, 0.8, 0.9, 1.0, 1.0, 1.1, 1.2, 1.2, 1.3, 1.4, 1.5]  # eval-protocol.md, load_id 1..12
AMPS_MM = [2.0, 4.0, 6.0]  # swell amplitudes, cycled over the loads
TRUTH_CSV = ROOT / "data" / "synthetic" / "truth.csv"
FIELDS = ["load_id", "cargo_kg", "light_kg", "rho_kg_m3", "L_m", "B_m", "draft_true_mm", "amp_mm", "period_s", "seed",
          "fps", "frames"]


def load_params(load_id: int) -> dict:
    bk = survey.barge_booklet()
    b = bk["barge"]
    cargo = LOADS_KG[load_id - 1]
    area = b["L_m"] * b["B_m"]
    t_m = (b["light_kg"] + cargo) / (b["rho_kg_m3"] * area)
    rng = np.random.default_rng(1000 + load_id)
    return {"load_id": load_id, "cargo_kg": cargo, "light_kg": b["light_kg"], "rho_kg_m3": b["rho_kg_m3"],
            "L_m": b["L_m"], "B_m": b["B_m"], "draft_true_mm": t_m * 1000, "amp_mm": AMPS_MM[(load_id - 1) % 3],
            "period_s": float(rng.uniform(1.4, 2.2)), "seed": 1000 + load_id, "fps": FPS, "frames": N}


def hull_image(top_mm: float, rng) -> np.ndarray:
    """The strip as the camera sees it: painted dark red, worn white numerals, vertical shading."""
    y_of = lambda mm: (top_mm - mm) * PX_PER_MM  # noqa: E731
    img = Image.new("RGB", (W, H), (104, 18, 18))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, int(10 * PX_PER_MM / 0.716))  # 1 cm numerals at 1:10 -> 10 mm tall
    for cm in range(2, 27, 2):
        lab = f"{cm // 10}M" if cm % 10 == 0 else str(cm % 10)
        yb = y_of(cm * 10)
        if -80 < yb < H + 80:
            bb = d.textbbox((0, 0), lab, font=font)
            d.text((W * 0.38 - bb[0], yb - bb[3]), lab, font=font, fill=(238, 232, 222))
    a = np.asarray(img, dtype=np.float32)
    yy = np.arange(H)[:, None, None]
    a *= 0.92 + 0.08 * np.cos(yy / 160.0)  # soft vertical shading
    a += rng.normal(0, 5, a.shape) + rng.normal(0, 3, (H, 1, 1))  # paint grain + brush streaks
    return a


def render(p: dict) -> tuple[list[np.ndarray], dict]:
    rng = np.random.default_rng(p["seed"])
    t_mm = p["draft_true_mm"]
    top_mm = t_mm + 0.8 * H / PX_PER_MM  # draft at the top row: 115 mm of strip above the water, a whole-metre mark stays dry
    y_of = lambda mm: (top_mm - mm) * PX_PER_MM  # noqa: E731
    hull = hull_image(top_mm, rng)
    xs = np.arange(W)
    yy = np.arange(H)[:, None]
    ph = rng.uniform(0, 2 * math.pi, 3)
    per = p["period_s"]
    frames = []
    for i in range(N):
        t = i / FPS
        swell = p["amp_mm"] * math.sin(2 * math.pi * t / per + ph[0])  # the whole surface heaves
        slope = 0.25 * p["amp_mm"] * np.sin(xs / 41.0 - 2 * math.pi * t / (per * 1.3) + ph[1])  # crest travels along
        ripple = 0.6 * np.sin(xs / 7.0 - 5 * t + ph[2]) + 0.4 * rng.normal(0, 1, W)
        surf_mm = t_mm + swell + slope + ripple * 0.5
        surf = y_of(surf_mm)  # px row of the surface in each column (rows grow downward)
        under = yy >= surf[None, :]
        depth = np.clip((yy - surf[None, :]) / 220.0, 0, 1)
        sheen = 14 * np.sin(yy / 9.0 + xs[None, :] / 23.0 + 1.7 * t) + rng.normal(0, 5, (H, W))
        base = 62 - 36 * depth + sheen
        wat = np.stack([base * 0.35 + 6, base * 0.88 + 22, base * 0.8 + 20], axis=-1)
        # faint mirror of the hull just under the surface, fading with depth (murky water)
        refl_row = np.clip((2 * surf[None, :] - yy).astype(int), 0, H - 1)
        mirror = hull[refl_row, xs[None, :]]
        fade = np.exp(-(yy - surf[None, :]) / 14.0)[..., None]
        wat = wat * (1 - 0.18 * fade) + mirror * 0.10 * fade
        img = np.where(under[..., None], wat, hull)
        edge = np.abs(yy - surf[None, :]) < 1.0  # bright meniscus line
        img = np.where(edge[..., None], img * 0.4 + np.array([120, 150, 150]) * 0.6, img)
        img = np.asarray(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)),
                         dtype=np.float32)
        img = img * (1 + 0.03 * math.sin(0.9 * t + ph[0])) + rng.normal(0, 3.0, img.shape)  # exposure + sensor noise
        frames.append(np.clip(img, 0, 255).astype(np.uint8))
    return frames, {"top_mm": top_mm, "px_per_mm": PX_PER_MM}


def encode(frames, out: Path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p", str(out)],
                         stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(f.tobytes())
    p.stdin.close()
    p.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / ".cache" / "synthetic"))
    ap.add_argument("--only", type=int, help="render one load_id only")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ids = [a.only] if a.only else list(range(1, len(LOADS_KG) + 1))
    TRUTH_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = [load_params(i) for i in range(1, len(LOADS_KG) + 1)]
    with TRUTH_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()} for r in rows)
    for i in ids:
        p = rows[i - 1]
        frames, meta = render(p)
        mp4 = out / f"load{i:02d}.mp4"
        encode(frames, mp4)
        mp4.with_suffix(".json").write_text(json.dumps({"source": "SYNTHETIC (scripts/render_synthetic.py)", "fps": FPS,
                                                        "frames": N, "scale": 0.1, **meta}))
        print(f"load {i}: cargo {p['cargo_kg']} kg  T {p['draft_true_mm']:.3f} mm  amp {p['amp_mm']} mm -> {mp4.name}")


if __name__ == "__main__":
    main()
