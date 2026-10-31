"""The measurement station end to end, split at the two places a stateless function hands over:

  1. SAM text (two concepts) -> compact geometry (tokens + a per-column water profile per frame) + the
     decision-matrix row 1 checks (NO_MASKS / OBJECT_CAP / WATER_MISS) and the two label frames.
  2. compact geometry + confirmed labels -> per-frame drafts -> clip average and uncertainty (measure.py).

Compact geometry is plain JSON, so the browser can carry it from /measure to /labels to /draft with no
server storage. Rebuilding it reproduces exactly what the mask-level code computes (tests/test_pipeline.py).
"""
from __future__ import annotations

import math

import numpy as np

from . import marks, measure, sam
from .marks import MarkSystem, Token
from .sam import SamObject

PAD_PX = 8  # water profile is kept over the mark column plus this margin


def tokens_by_frame(num: dict[int, list[SamObject]], n_frames: int, system: MarkSystem
                    ) -> tuple[dict[int, list[Token]], dict[int, int], list[int]]:
    toks, raw, capped = {}, {}, []
    for i in range(n_frames):
        g = num.get(i, [])
        raw[i] = len(g)
        try:
            toks[i] = marks.group_glyphs(g, system)
        except marks.ObjectCapError:
            toks[i] = []
            capped.append(i)
    return toks, raw, capped


def column(toks: dict[int, list[Token]]) -> tuple[int, int] | None:
    xs0 = [t.box[0] for ts in toks.values() for t in ts]
    xs1 = [t.box[2] for ts in toks.values() for t in ts]
    if not xs0:
        return None
    return int(math.floor(min(xs0))) - PAD_PX, int(math.ceil(max(xs1))) + PAD_PX


def water_profile(water: list[SamObject], x_lo: int, x_hi: int) -> list[float | None]:
    """Top row of the water mask(s) per column x_lo..x_hi-1 (None where no mask covers the column)."""
    out: list[float | None] = []
    for c in range(x_lo, x_hi):
        best = None
        for o in water:
            if o.mask is None:
                continue
            lc = c - int(o.box[0])
            if 0 <= lc < o.mask.shape[1]:
                ys = np.flatnonzero(o.mask[:, lc])
                if ys.size:
                    t = o.box[1] + ys[0]
                    best = t if best is None else min(best, t)
        out.append(None if best is None else float(best))
    return out


def water_from_profile(frame: int, x_lo: int, prof: list[float | None]) -> list[SamObject]:
    tops = [t for t in prof if t is not None]
    if not tops:
        return []
    y0 = float(min(tops))  # SAM boxes are integer pixels; a fractional origin is kept exactly
    rows = int(math.ceil(max(tops) - y0)) + 2
    m = np.zeros((rows, len(prof)), dtype=bool)
    for c, t in enumerate(prof):
        if t is not None:
            m[int(round(t - y0)):, c] = True
    return [SamObject(frame, 0, (float(x_lo), y0, float(x_lo + len(prof)), y0 + rows), m)]


def token_json(t: Token) -> dict:
    return {"track": t.track, "glyph_ids": list(t.glyph_ids), "box": [round(v, 2) for v in t.box],
            "bottom": round(t.mask_bottom(), 3), "n": t.n_glyphs}


def token_from_json(d: dict) -> Token:
    return Token(d["track"], tuple(d["glyph_ids"]), tuple(d["box"]), [], bottom_px=d["bottom"])


def pick_label_frames(toks: dict[int, list[Token]], fps: float) -> tuple[int, int] | None:
    """Two frames >= 1 s apart with the most tokens (ties -> earliest)."""
    gap = max(1, int(round(fps)))
    order = sorted((i for i in toks if toks[i]), key=lambda i: (-len(toks[i]), i))
    if not order:
        return None
    f1 = order[0]
    f2 = next((i for i in order if abs(i - f1) >= gap), None)
    return (f1, f2) if f2 is not None else None


def geometry(num_text: str, water_text: str, n_frames: int, fps: float, system: MarkSystem,
             crop: dict | None = None) -> dict:
    """Stage 1 from SAM's output text (two concepts)."""
    return geometry_from_objects(sam.parse(num_text), sam.parse(water_text), n_frames, fps, system, crop)


def geometry_from_objects(num_objs: list[SamObject], water_objs: list[SamObject], n_frames: int, fps: float,
                          system: MarkSystem, crop: dict | None = None) -> dict:
    """Stage 1. Returns the compact geometry with `row1` = None or a REFUSE reason."""
    num = sam.by_frame(num_objs)
    toks, raw, capped = tokens_by_frame(num, n_frames, system)
    return geometry_from_tokens(toks, raw, capped, sam.by_frame(water_objs), n_frames, fps, system, crop)


def geometry_from_tokens(toks: dict[int, list[Token]], raw: dict[int, int], capped: list[int],
                         wat: dict[int, list[SamObject]], n_frames: int, fps: float, system: MarkSystem,
                         crop: dict | None = None) -> dict:
    col = column(toks)
    frames = []
    any_edge = False
    for i in range(n_frames):
        ti = toks.get(i, [])
        prof = water_profile(wat.get(i, []), *col) if col else []
        if ti and col and measure.water_edge(water_from_profile(i, col[0], prof), *col) is not None:
            any_edge = True
        frames.append({"i": i, "raw": raw.get(i, 0), "tokens": [token_json(t) for t in ti], "water": prof,
                       "n_water_objs": len(wat.get(i, []))})
    n_num = sum(raw.values())
    n_wat = sum(len(v) for v in wat.values())
    if n_num == 0 or n_wat == 0:
        row1 = "NO_MASKS"
    elif capped:
        row1 = "OBJECT_CAP"
    elif not any_edge:
        row1 = "WATER_MISS"
    else:
        row1 = None
    lf = pick_label_frames({i: toks.get(i, []) for i in range(n_frames)}, fps)
    return {"n_frames": n_frames, "fps": fps, "mark_system": {"id": system.id, "scale": system.scale},
            "crop": crop, "column": list(col) if col else None, "frames": frames, "raw_numeral_objs": n_num,
            "raw_water_objs": n_wat, "object_cap_frames": capped, "row1": row1,
            "label_frames": list(lf) if lf else None,
            "frames_with_3_tokens": sum(len(f["tokens"]) >= 3 for f in frames),
            "frames_with_water": sum(f["n_water_objs"] > 0 for f in frames)}


def rebuild(geom: dict) -> tuple[dict[int, list[Token]], dict[int, list[SamObject]]]:
    x_lo = geom["column"][0] if geom.get("column") else 0
    toks = {f["i"]: [token_from_json(t) for t in f["tokens"]] for f in geom["frames"]}
    water = {f["i"]: water_from_profile(f["i"], x_lo, f["water"]) for f in geom["frames"]}
    return toks, water


def system_of(geom: dict) -> MarkSystem:
    ms = geom.get("mark_system") or {}
    return MarkSystem(ms.get("id", "ship-metric"), float(ms.get("scale", 1.0)))


def check(geom: dict, reads: dict[int, dict[str, str]], strip: list[str] | None = None,
          table_range: tuple[float, float] | None = None) -> tuple[dict[str, float], marks.CheckResult]:
    """The five code checks on the first label frame; reads = {frame: {track: label}}."""
    toks, _ = rebuild(geom)
    f1, f2 = (int(k) for k in list(reads)[:2])
    return marks.check_labels(toks[f1], reads[f1], reads.get(f2), system_of(geom), strip, table_range)


def finish(geom: dict, drafts: dict[str, float], u_sys_parts: dict | None = None
           ) -> tuple[list[measure.FrameGeom], measure.DraftResult]:
    """Stage 2: per-frame drafts and the clip-level average (pure code)."""
    toks, water = rebuild(geom)
    return measure.measure_clip(toks, water, drafts, system_of(geom), u_sys_parts)


def frames_json(frames: list[measure.FrameGeom]) -> list[dict]:
    keys = ("i", "kept", "drop_reason", "n_tokens", "n_dry", "water_edge_y", "edge_mad", "pitch_px", "d_m")
    out = []
    for f in frames:
        d = {k: getattr(f, k) for k in keys}
        d["a"], d["b"] = f.a, f.b
        out.append(d)
    return out
