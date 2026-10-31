"""Mark systems, glyph -> token grouping, label grammar and the code checks.

SAM returns glyphs ("12M" can come back as 3 boxes); code groups them into mark tokens
before labels, anchor and scale. Labels come from a model (Spark) and are only used
after code confirms them (complexity.md §3).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from statistics import median

import numpy as np

from .sam import SamObject

SAM_VIDEO_OBJECT_CAP = 16


class ObjectCapError(ValueError):
    code = "OBJECT_CAP"


@dataclass(frozen=True)
class MarkSystem:
    id: str = "ship-metric"
    scale: float = 1.0  # 1.0 ship, 0.1 the 1:10 barge strip
    max_raw_glyphs: int = 14

    @property
    def pitch_m(self) -> float:
        return 0.20 * self.scale

    @property
    def digit_h_m(self) -> float:
        return 0.10 * self.scale

    def label_pattern(self) -> str:
        return r"^(?:[1-9][0-9]?M|[2468])$"

    def labels_enum(self, max_metre: int = 25) -> list[str]:
        return [f"{n}M" for n in range(1, max_metre + 1)] + ["2", "4", "6", "8"]


SHIP = MarkSystem("ship-metric", 1.0)
BARGE = MarkSystem("ship-metric", 0.1)


@dataclass
class Token:
    track: str  # stable across frames: "t<min glyph id>"
    glyph_ids: tuple[int, ...]
    box: tuple[float, float, float, float]
    glyphs: list[SamObject] = field(default_factory=list)

    @property
    def n_glyphs(self) -> int:
        return len(self.glyph_ids)

    @property
    def w(self) -> float:
        return self.box[2] - self.box[0]

    @property
    def h(self) -> float:
        return self.box[3] - self.box[1]

    @property
    def cy(self) -> float:
        return (self.box[1] + self.box[3]) / 2

    def mask_bottom(self, pct: float = 90.0) -> float:
        """Bottom edge from the masks: per column the lowest mask row, then the pct-th
        percentile across the token's width (robust to a ragged edge). Falls back to the box."""
        lows = []
        for g in self.glyphs:
            if g.mask is None or not g.mask.any():
                continue
            m = g.mask
            cols = np.flatnonzero(m.any(axis=0))
            for c in cols:
                rows = np.flatnonzero(m[:, c])
                lows.append(g.box[1] + rows[-1] + 1)
        if not lows:
            return self.box[3]
        return float(np.percentile(lows, pct))


def group_glyphs(objs: list[SamObject], system: MarkSystem = SHIP) -> list[Token]:
    """Union glyphs sharing a baseline (bottom edges within 0.15 h) with a horizontal gap
    < 0.5 h, where h = median glyph height. Returns tokens sorted bottom -> top."""
    if len(objs) >= SAM_VIDEO_OBJECT_CAP:
        raise ObjectCapError(f"{len(objs)} raw glyphs >= SAM cap {SAM_VIDEO_OBJECT_CAP}: crop to fewer marks")
    if not objs:
        return []
    h = median(o.h for o in objs)
    parent = list(range(len(objs)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, a in enumerate(objs):
        for j in range(i + 1, len(objs)):
            b = objs[j]
            if abs(a.box[3] - b.box[3]) >= 0.15 * h:
                continue
            gap = max(a.box[0], b.box[0]) - min(a.box[2], b.box[2])
            if gap < 0.5 * h:
                parent[find(i)] = find(j)
    groups: dict[int, list[SamObject]] = {}
    for i, o in enumerate(objs):
        groups.setdefault(find(i), []).append(o)
    toks = []
    for g in groups.values():
        g.sort(key=lambda o: o.box[0])
        ids = tuple(sorted(o.obj_id for o in g))
        box = (min(o.box[0] for o in g), min(o.box[1] for o in g), max(o.box[2] for o in g), max(o.box[3] for o in g))
        toks.append(Token(f"t{ids[0]}", ids, box, g))
    toks.sort(key=lambda t: -t.box[3])
    return toks


def wide_class(tok: Token, median_digit_w: float) -> bool:
    """A whole-metre "NM" token: >= 2 grouped glyphs or width >= 1.6 x the median digit width."""
    return tok.n_glyphs >= 2 or tok.w >= 1.6 * median_digit_w


# -- labels -> drafts ---------------------------------------------------------------
_METRE = re.compile(r"^([1-9][0-9]?)M$")


def labels_to_drafts(labels_bottom_up: list[str], system: MarkSystem = SHIP) -> list[float | None]:
    """Convert labels ordered bottom -> top into drafts (m). A digit d above whole-metre
    mark M is M + d/10 (ship units); digits below the lowest metre mark use (M_low - 1).
    Returns None entries when no metre mark anchors the sequence."""
    metre_idx = [i for i, s in enumerate(labels_bottom_up) if _METRE.match(s or "")]
    if not metre_idx:
        return [None] * len(labels_bottom_up)
    out: list[float | None] = []
    for i, s in enumerate(labels_bottom_up):
        m = _METRE.match(s or "")
        if m:
            out.append(round(int(m.group(1)) * system.scale, 6))
            continue
        if s not in ("2", "4", "6", "8"):
            out.append(None)
            continue
        below = [k for k in metre_idx if k < i]
        if below:
            base = int(_METRE.match(labels_bottom_up[below[-1]]).group(1))
        else:
            base = int(_METRE.match(labels_bottom_up[metre_idx[0]]).group(1)) - 1
        out.append(round((base + int(s) / 10) * system.scale, 6))
    return out


@dataclass
class CheckResult:
    monotone: bool
    pitch: bool
    residual: bool
    cross_frame: bool
    anchor: bool
    detail: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.monotone and self.pitch and self.residual and self.cross_frame and self.anchor

    def as_dict(self) -> dict:
        return {"monotone": self.monotone, "pitch": self.pitch, "residual": self.residual,
                "cross_frame": self.cross_frame, "anchor": self.anchor, "ok": self.ok, **self.detail}


def check_labels(tokens: list[Token], read1: dict[str, str], read2: dict[str, str] | None,
                 system: MarkSystem = SHIP, strip_sequence: list[str] | None = None,
                 table_range: tuple[float, float] | None = None) -> tuple[dict[str, float], CheckResult]:
    """The five code checks on one annotated frame's tokens (bottom -> top)."""
    toks = [t for t in tokens if t.track in read1]
    labels = [read1[t.track] for t in toks]
    drafts = labels_to_drafts(labels, system)
    detail: dict = {"labels": dict(zip([t.track for t in toks], labels))}
    ok_vals = all(d is not None for d in drafts) and len(drafts) >= 3
    # (a) strictly increasing upward
    mono = ok_vals and all(b > a for a, b in zip(drafts, drafts[1:]))
    # (b) consecutive differences = k * pitch where k = round(pixel gap / pixel pitch)
    pitch_ok = False
    resid_ok = False
    if mono:
        bottoms = np.array([t.box[3] for t in toks], dtype=float)
        z = np.array(drafts, dtype=float)
        b, a = np.polyfit(z, bottoms, 1)
        pitch_px = abs(b) * system.pitch_m
        ks = [int(round(abs(bottoms[i + 1] - bottoms[i]) / pitch_px)) for i in range(len(toks) - 1)]
        pitch_ok = bool(all(k >= 1 and abs((z[i + 1] - z[i]) - k * system.pitch_m) < 1e-6 for i, k in enumerate(ks)))
        # (c) regression residual RMS < 0.1 x pitch (in px)
        rms = float(np.sqrt(np.mean((bottoms - (a + b * z)) ** 2)))
        resid_ok = bool(rms < 0.1 * pitch_px)
        detail.update(pitch_px=round(pitch_px, 2), resid_rms_px=round(rms, 2), gaps_in_pitches=ks)
    # (d) the two reads agree on every shared track id
    if read2 is None:
        cross = False
        detail["cross_frame_note"] = "no second read"
    else:
        shared = set(read1) & set(read2)
        disagree = sorted(k for k in shared if read1[k] != read2[k])
        cross = bool(shared) and not disagree
        detail.update(shared=len(shared), disagree=disagree)
    # (e) anchor: every token labelled "NM" is geometrically wide; barge: run of the printed sequence
    digit_ws = [t.w for t in toks if t.n_glyphs == 1 and not _METRE.match(read1[t.track] or "")]
    med_w = median(digit_ws) if digit_ws else median(t.w for t in toks) if toks else 0
    metre = [t for t in toks if _METRE.match(read1[t.track] or "")]
    anchor = bool(metre) and all(wide_class(t, med_w) for t in metre)
    # and no single-glyph narrow digit-labelled token may be wide (a missed "M")
    anchor = anchor and not any(t.n_glyphs >= 2 for t in toks if not _METRE.match(read1[t.track] or ""))
    if strip_sequence is not None and anchor:
        seq = list(strip_sequence)
        anchor = any(seq[i:i + len(labels)] == labels for i in range(len(seq) - len(labels) + 1)) or \
            _is_subsequence(labels, seq)
    if table_range is not None and anchor and ok_vals:
        anchor = table_range[0] - 1.0 <= min(drafts) and max(drafts) <= table_range[1] + 1.0
    detail["anchor_tokens"] = [t.track for t in metre]
    res = CheckResult(mono, pitch_ok, resid_ok, cross, anchor, detail)
    by_track = {t.track: d for t, d in zip(toks, drafts) if d is not None} if res.ok else {}
    return by_track, res


def _is_subsequence(labels: list[str], seq: list[str]) -> bool:
    """Labels in order inside the printed sequence (submerged marks may be missing)."""
    it = iter(seq)
    return all(any(s == x for s in it) for x in labels)


def strip_sequence(top_cm: int = 26) -> list[str]:
    """The printed 1:10 strip, bottom -> top (scripts/make_strip.py)."""
    return [f"{cm // 10}M" if cm % 10 == 0 else str(cm % 10) for cm in range(2, top_cm + 1, 2)]
