"""Prepare a SAM input clip: cut [t0, t0+dur] at FPS, crop the mark column, scale 2x.

SAM 3.1 misses ~18 px numerals on a full 1280-1920 px frame, finds them on a 2x crop
(day-0 test). The bucket rig is a fixed camera (fixed crop). Handheld public clips use
--track: the crop follows the mark column by normalised cross-correlation of the first
frame's mark patch (search +-16 px per frame). The draft is fitted per frame, so a
moving crop does not bias it. Local/offline tool (OpenCV); the deployed app never runs it.

  python scripts/prep_clip.py IN.mp4 OUT.mp4 --t0 45 --dur 10 --fps 6 --box x,y,w,h [--track] [--scale 2]
Writes OUT.mp4 and OUT.json (crop per frame, source, fps).
"""
import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np


def read_frames(path, t0, dur, fps):
    cap = cv2.VideoCapture(str(path))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frames = []
    n = int(round(dur * fps))
    for k in range(n):
        t = t0 + k / fps
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        if not ok:
            break
        frames.append(fr)
    cap.release()
    return frames, src_fps


def track(frames, box, search=16, tmpl_frac=0.6):
    x, y, w, h = box
    th = int(h * tmpl_frac)
    g0 = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    tmpl = g0[y:y + th, x:x + w]
    pos = [(x, y)]
    H, W = g0.shape
    for fr in frames[1:]:
        px, py = pos[-1]
        g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        sx0, sy0 = max(0, px - search), max(0, py - search)
        sx1, sy1 = min(W, px + w + search), min(H, py + th + search)
        res = cv2.matchTemplate(g[sy0:sy1, sx0:sx1], tmpl, cv2.TM_CCOEFF_NORMED)
        _, score, _, loc = cv2.minMaxLoc(res)
        nx, ny = sx0 + loc[0], sy0 + loc[1]
        nx = min(max(0, nx), W - w)
        ny = min(max(0, ny), H - h)
        pos.append((nx, ny))
        # slow template refresh against drift in appearance, only on confident matches
        if score > 0.8:
            tmpl = cv2.addWeighted(tmpl, 0.8, g[ny:ny + th, nx:nx + w], 0.2, 0)
    return pos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--t0", type=float, default=0)
    ap.add_argument("--dur", type=float, default=10)
    ap.add_argument("--fps", type=float, default=6)
    ap.add_argument("--box", required=True, help="x,y,w,h in source pixels")
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--track", action="store_true")
    ap.add_argument("--search", type=int, default=16, help="tracking search radius, px per frame")
    a = ap.parse_args()
    box = tuple(int(v) for v in a.box.split(","))
    frames, src_fps = read_frames(a.src, a.t0, a.dur, a.fps)
    pos = track(frames, box, a.search) if a.track else [(box[0], box[1])] * len(frames)
    w, h = box[2], box[3]
    ow, oh = int(w * a.scale) // 2 * 2, int(h * a.scale) // 2 * 2
    out = Path(a.out)
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{ow}x{oh}",
         "-r", str(a.fps), "-i", "-", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(out)],
        stdin=subprocess.PIPE)
    for fr, (x, y) in zip(frames, pos):
        crop = fr[y:y + h, x:x + w]
        proc.stdin.write(cv2.resize(crop, (ow, oh), interpolation=cv2.INTER_CUBIC).tobytes())
    proc.stdin.close()
    proc.wait()
    meta = {"source": Path(a.src).name, "t0": a.t0, "dur": a.dur, "fps": a.fps, "scale": a.scale,
            "box_wh": [w, h], "frames": len(frames), "tracked": a.track,
            "crop_xy": [list(map(int, p)) for p in pos],
            "drift_px": float(np.hypot(pos[-1][0] - pos[0][0], pos[-1][1] - pos[0][1]))}
    out.with_suffix(".json").write_text(json.dumps(meta))
    print(json.dumps({k: v for k, v in meta.items() if k != "crop_xy"}))


if __name__ == "__main__":
    main()
