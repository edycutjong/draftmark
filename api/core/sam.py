"""SAM 3.1 output grammar -> objects with half-open boxes and box-local masks.

Grammar (Responses API output_text):
  [<Nf>] id<|box;x1=..;y1=..;x2=..;y2=..;w=W;h=H|>[<|mask;x=..;y=..;data=H,W,<enc><payload>|>] , ...
x2/y2 are inclusive pixel indices; we return half-open boxes [x1, y1, x2+1, y2+1] (the
same convention as meta_sam_parser), so a numeral's bottom edge is box[3]. The mask is
cropped to its box: its origin is the box origin.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

try:
    import meta_sam_parser as msp
except ImportError:  # pragma: no cover - fallback path is tested explicitly
    msp = None


@dataclass
class SamObject:
    frame: int
    obj_id: int
    box: tuple[float, float, float, float]  # half-open x0, y0, x1, y1 in media pixels
    mask: np.ndarray | None = None  # bool [h, w], origin = (box[0], box[1])

    @property
    def cx(self) -> float:
        return (self.box[0] + self.box[2]) / 2

    @property
    def cy(self) -> float:
        return (self.box[1] + self.box[3]) / 2

    @property
    def w(self) -> float:
        return self.box[2] - self.box[0]

    @property
    def h(self) -> float:
        return self.box[3] - self.box[1]


_TOKEN = re.compile(
    r"<(\d+)f>"
    r"|(\d+)<\|box;x1=([\d.]+);y1=([\d.]+);x2=([\d.]+);y2=([\d.]+);w=(\d+);h=(\d+)\|>"
    r"(?:<\|mask;x=(\d+);y=(\d+);data=(\d+),(\d+),([~!])(.*?)\|>)?",
    re.S,
)


def _decode(enc: str, payload: str, w: int, h: int) -> np.ndarray | None:
    if msp is None:
        return None
    mk = msp.SegmentationMask(encoding="lossless" if enc == "~" else "one_bit",
                              payload=enc + payload, width=w, height=h)
    raw = np.frombuffer(msp.decode_mask_to_raster(mk), dtype=np.uint8)
    return raw.reshape(h, w) > 0


def parse_own(text: str) -> list[SamObject]:
    """Our grammar parser (no dependency on the parser package for structure)."""
    out: list[SamObject] = []
    frame = 0
    for m in _TOKEN.finditer(text):
        if m.group(1) is not None:
            frame = int(m.group(1))
            continue
        oid, x1, y1, x2, y2 = int(m.group(2)), *(float(m.group(i)) for i in range(3, 7))
        mask = None
        if m.group(13) is not None:
            mh, mw = int(m.group(11)), int(m.group(12))
            mask = _decode(m.group(13), m.group(14), mw, mh)
        out.append(SamObject(frame, oid, (x1, y1, x2 + 1, y2 + 1), mask))
    return out


def parse_msp(text: str, video: bool = True) -> list[SamObject]:
    """meta_sam_parser path (the official grammar implementation)."""
    if msp is None:
        raise ImportError("meta_sam_parser not installed")
    fmt = msp.video_segmentation_format() if video else msp.image_segmentation_format()
    p = fmt.create_parser()
    p.push(text, emit=False)
    res = p.finish(msp.CompletedOutcome()).result
    boxes: dict[tuple[int, str], SamObject] = {}
    order: list[tuple[int, str]] = []
    for r in res.records:
        fr = r.frame.frame_index if r.frame is not None else 0
        k = (fr, r.object_id)
        if r.kind == "box":
            boxes[k] = SamObject(fr, int(r.object_id), (float(r.left), float(r.top), float(r.right), float(r.bottom)))
            order.append(k)
        elif r.kind == "mask" and k in boxes:
            raw = np.frombuffer(msp.decode_mask_to_raster(r.mask), dtype=np.uint8)
            boxes[k].mask = raw.reshape(r.mask.height, r.mask.width) > 0
    return [boxes[k] for k in order]


def parse(text: str, video: bool = True) -> list[SamObject]:
    if msp is not None:
        try:
            objs = parse_msp(text, video)
            if objs or "<|box" not in text:
                return objs
        except Exception:
            pass
    return parse_own(text)


def by_frame(objs: list[SamObject]) -> dict[int, list[SamObject]]:
    d: dict[int, list[SamObject]] = {}
    for o in objs:
        d.setdefault(o.frame, []).append(o)
    return d


def mask_top_at(o: SamObject, x: float, half: int = 6) -> float | None:
    """Median top row (media px) of a mask over columns x±half; None if no pixels there."""
    if o.mask is None:
        return None
    x0, y0 = int(o.box[0]), int(o.box[1])
    tops = []
    for c in range(int(x) - half, int(x) + half + 1):
        lc = c - x0
        if 0 <= lc < o.mask.shape[1]:
            ys = np.flatnonzero(o.mask[:, lc])
            if ys.size:
                tops.append(y0 + ys[0])
    return float(np.median(tops)) if tops else None


def mask_bottom(o: SamObject) -> float | None:
    """Lowest mask row + 1 (half-open), media px."""
    if o.mask is None or not o.mask.any():
        return None
    rows = np.flatnonzero(o.mask.any(axis=1))
    return float(o.box[1] + rows[-1] + 1)
