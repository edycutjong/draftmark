"""Per-frame draft and the clip-level error model (complexity.md §2). numpy only.

Per frame: dry tokens (mask bottom above the water edge) give a least-squares scale
y = a + b z; the water edge w is the median top of the "water" mask across the mark
band; d = (w - a) / b with a delta-method variance. Per clip: MAD outlier rejection,
mean of kept frames, N_eff from the lag-1 autocorrelation, u_rep / u_abs.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

import numpy as np

from .marks import MarkSystem, Token
from .sam import SamObject


@dataclass
class FrameGeom:
    i: int
    kept: bool
    drop_reason: str | None = None
    n_tokens: int = 0
    n_dry: int = 0
    water_edge_y: float | None = None
    edge_mad: float | None = None
    a: float | None = None
    b: float | None = None  # px per m (negative: y grows downward as draft falls)
    pitch_px: float | None = None
    resid_rms_px: float | None = None
    d_m: float | None = None
    var_d: float | None = None
    var_rand: float | None = None
    tracks: list[str] = field(default_factory=list)


WATER_GAP_PX = 3  # 2x crops: about 1.5 source pixels; real masks: holes in 5 of 7680 dB7X columns at this tolerance


def column_top(water: list[SamObject], c: int) -> float | None:
    """Top of the water in image column c: the contiguous run of water pixels (all masks united) that holds the
    lowest water pixel, so a detached spray or reflection blob above the surface never becomes the edge."""
    ys: set[float] = set()
    for o in water:
        if o.mask is None:
            continue
        lc = c - int(o.box[0])
        if 0 <= lc < o.mask.shape[1]:
            ys.update(float(o.box[1] + y) for y in np.flatnonzero(o.mask[:, lc]))
    if not ys:
        return None
    srt = sorted(ys)
    top = srt[-1]
    for y in reversed(srt[:-1]):  # bridge holes up to WATER_GAP_PX (foam/glare); a wider gap = detached blob
        if top - y > WATER_GAP_PX + 1:
            break
        top = y
    return top


def water_edge(water: list[SamObject], x_lo: float, x_hi: float) -> tuple[float, float, int] | None:
    """Median top edge of the water mask(s) over columns [x_lo, x_hi); (w, MAD, n_cols)."""
    tops: list[float] = []
    for c in range(int(math.floor(x_lo)), int(math.ceil(x_hi))):
        best = column_top(water, c)
        if best is not None:
            tops.append(best)
    if len(tops) < 3:
        return None
    arr = np.array(tops, dtype=float)
    w = float(np.median(arr))
    mad = float(np.median(np.abs(arr - w)))
    return w, mad, len(tops)


def frame_draft(i: int, tokens: list[Token], drafts: dict[str, float], water: list[SamObject],
                system: MarkSystem, pitch_ref_px: float | None = None) -> FrameGeom:
    fg = FrameGeom(i=i, kept=False, n_tokens=len(tokens))
    lab = [t for t in tokens if t.track in drafts]
    if not lab:
        fg.drop_reason = "NO_LABELLED_MARKS"
        return fg
    x_lo = min(t.box[0] for t in lab)
    x_hi = max(t.box[2] for t in lab)
    we = water_edge(water, x_lo, x_hi)
    if we is None:
        fg.drop_reason = "NO_WATER_EDGE"
        return fg
    w, mad, ncols = we
    fg.water_edge_y, fg.edge_mad = w, mad
    margin = max(5.0, 3.0 * 1.4826 * mad)
    dry = [t for t in lab if t.mask_bottom() <= w - margin]
    fg.n_dry = len(dry)
    fg.tracks = [t.track for t in dry]
    if len(dry) < 3:
        fg.drop_reason = "DRY_MARKS_LOW"
        return fg
    # track ids must keep the label order: higher on screen (smaller y) = deeper draft mark
    by_y = sorted(dry, key=lambda t: -t.mask_bottom())
    if any(drafts[b.track] <= drafts[a.track] for a, b in zip(by_y, by_y[1:])):
        fg.drop_reason = "TRACK_UNSTABLE"
        return fg
    z = np.array([drafts[t.track] for t in dry], dtype=float)
    y = np.array([t.mask_bottom() for t in dry], dtype=float)
    X = np.column_stack([np.ones_like(z), z])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    a, b = float(coef[0]), float(coef[1])
    resid = y - X @ coef
    dof = max(1, len(z) - 2)
    s2 = float(resid @ resid) / dof
    cov = s2 * np.linalg.inv(X.T @ X)
    pitch_px = abs(b) * system.pitch_m
    rms = float(np.sqrt(np.mean(resid ** 2)))
    fg.a, fg.b, fg.pitch_px, fg.resid_rms_px = a, b, pitch_px, rms
    if b >= 0:
        fg.drop_reason = "SCALE_SIGN"
        return fg
    if pitch_ref_px is not None and abs(pitch_px - pitch_ref_px) >= 0.15 * pitch_ref_px:
        fg.drop_reason = "PITCH"
        return fg
    if rms >= 0.1 * pitch_px:
        fg.drop_reason = "RESIDUAL"
        return fg
    if mad > 0.25 * pitch_px:
        fg.drop_reason = "EDGE_NOISY"
        return fg
    # perspective: single-glyph dry digit heights vary > 10 % bottom to top
    hs = [t.h for t in dry if t.n_glyphs == 1]
    if len(hs) >= 2 and (max(hs) - min(hs)) / max(hs) > 0.10 + 2.0 / max(hs):
        fg.drop_reason = "PERSPECTIVE"
        return fg
    d = (w - a) / b
    s_e = 1.4826 * mad / math.sqrt(ncols) if ncols else 0.0
    var_a, var_b, cov_ab = float(cov[0, 0]), float(cov[1, 1]), float(cov[0, 1])
    var_edge = (s_e / b) ** 2
    var_fit = var_a / b ** 2 + ((w - a) / b ** 2) ** 2 * var_b + 2 * ((w - a) / b ** 3) * cov_ab
    fg.d_m = float(d)
    fg.var_d = float(var_edge + max(0.0, var_fit))
    fg.var_rand = fg.var_d
    fg.kept = True
    return fg


@dataclass
class DraftResult:
    d_m: float | None
    u_rep_m: float | None
    u_abs_m: float | None
    u_parts: dict
    n_frames: int
    n_kept: int
    n_outliers: int
    n_eff: float | None
    rho1: float | None
    median_m: float | None
    huber_m: float | None
    sd_m: float | None
    swell_p5_p95: tuple[float, float] | None
    pitch_px_median: float | None
    label_shift_sensitivity_m: float
    drops: dict
    refused: bool
    reason: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def huber(x: np.ndarray, k: float = 1.345, iters: int = 50) -> float:
    mu = float(np.median(x))
    s = 1.4826 * float(np.median(np.abs(x - mu))) or 1e-9
    for _ in range(iters):
        r = (x - mu) / s
        wts = np.where(np.abs(r) <= k, 1.0, k / np.maximum(np.abs(r), 1e-12))
        new = float(np.sum(wts * x) / np.sum(wts))
        if abs(new - mu) < 1e-9:
            break
        mu = new
    return mu


def lag1(x: np.ndarray) -> float:
    if len(x) < 3:
        return 0.0
    xc = x - x.mean()
    den = float(xc @ xc)
    return float((xc[:-1] @ xc[1:]) / den) if den > 0 else 0.0


def summarize(frames: list[FrameGeom], system: MarkSystem, u_sys_parts: dict | None = None,
              min_kept_frac: float = 0.6, min_kept: int = 8) -> DraftResult:
    """Clip-level average + uncertainty. u_sys_parts (m, k=1) e.g. {"scale":..,"zero":..,"edge":..,"par":..};
    when None, u_abs is not computed (real-ship clips: repeatability only)."""
    drops: dict[str, int] = {}
    for f in frames:
        if not f.kept:
            drops[f.drop_reason or "?"] = drops.get(f.drop_reason or "?", 0) + 1
    kept = [f for f in frames if f.kept]
    n = len(frames)
    base = dict(u_parts={}, n_frames=n, n_kept=len(kept), n_outliers=0, n_eff=None, rho1=None, median_m=None,
                huber_m=None, sd_m=None, swell_p5_p95=None, pitch_px_median=None,
                label_shift_sensitivity_m=system.pitch_m, drops=drops)
    if len(kept) < max(min_kept, math.ceil(min_kept_frac * n)):
        return DraftResult(None, None, None, refused=True, reason="FRAMES_LOW", **base)
    d = np.array([f.d_m for f in kept])
    med = float(np.median(d))
    mad = float(np.median(np.abs(d - med)))
    keep = np.abs(d - med) <= 3.5 * 1.4826 * mad if mad > 0 else np.ones_like(d, dtype=bool)
    n_out = int((~keep).sum())
    dk = d[keep]
    vr = np.array([f.var_rand for f, k in zip(kept, keep) if k])
    mean = float(dk.mean())
    rho = min(0.99, max(0.0, lag1(dk)))
    n_eff = max(2.0, len(dk) * (1 - rho) / (1 + rho))
    sd = float(dk.std(ddof=1)) if len(dk) > 1 else 0.0
    u_swell = sd / math.sqrt(n_eff)
    u_rand = math.sqrt(float(vr.mean()) / n_eff)
    # the frame-to-frame scatter already contains each frame's own fit/edge noise, so the propagated per-frame
    # term is a floor (few or identical frames), not a second component to add in quadrature
    pitch_med = float(np.median([f.pitch_px for f in kept]))
    u_quant = 0.5 / pitch_med * system.pitch_m if pitch_med > 0 else 0.0  # half a pixel: never claim u = 0
    u_rep = max(u_swell, u_rand, u_quant)
    parts = {"swell": u_swell, "rand": u_rand, "quant": u_quant}
    u_abs = None
    if u_sys_parts is not None:
        u_sys = math.sqrt(sum(v ** 2 for v in u_sys_parts.values()))
        parts["sys"] = dict(u_sys_parts)
        u_abs = math.sqrt(u_rep ** 2 + u_sys ** 2)
    base.update(u_parts=parts, n_outliers=n_out, n_eff=round(n_eff, 2), rho1=round(rho, 3), median_m=med,
                huber_m=huber(dk), sd_m=sd, swell_p5_p95=(float(np.percentile(dk, 5)), float(np.percentile(dk, 95))),
                pitch_px_median=pitch_med)
    return DraftResult(mean, u_rep, u_abs, refused=False, **base)


def measure_clip(frames_tokens: dict[int, list[Token]], water_by_frame: dict[int, list[SamObject]],
                 drafts: dict[str, float], system: MarkSystem, u_sys_parts: dict | None = None
                 ) -> tuple[list[FrameGeom], DraftResult]:
    """Two passes: the first estimates the clip's median pitch, the second applies the pitch check."""
    idx = sorted(frames_tokens)
    first = [frame_draft(i, frames_tokens[i], drafts, water_by_frame.get(i, []), system) for i in idx]
    pitches = [f.pitch_px for f in first if f.pitch_px and f.drop_reason is None]
    ref = float(np.median(pitches)) if pitches else None
    frames = [frame_draft(i, frames_tokens[i], drafts, water_by_frame.get(i, []), system, ref) for i in idx]
    return frames, summarize(frames, system, u_sys_parts)
