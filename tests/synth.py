"""Synthetic SAM objects with known geometry (tests only)."""
import numpy as np

from api.core.sam import SamObject


def glyph(frame, oid, x0, y0, w, h):
    return SamObject(frame, oid, (float(x0), float(y0), float(x0 + w), float(y0 + h)), np.ones((h, w), dtype=bool))


def ship_frame(frame=0, draft_m=12.73, px_per_m=330.0, base_y=900.0, x=100, digit_h=33, digit_w=20,
               marks=(("12M", 12.0), ("2", 12.2), ("4", 12.4), ("6", 12.6), ("8", 12.8), ("13M", 13.0), ("2", 13.2),
                      ("4", 13.4)), start_id=0, split_metre=True):
    """Glyphs for ship marks; y of a mark's bottom = base_y - (z - 12) * px_per_m. Water edge at draft_m."""
    objs, oid = [], start_id
    for label, z in marks:
        yb = base_y - (z - 12.0) * px_per_m
        if label.endswith("M") and split_metre:
            cx = x - 8
            for ch in label:
                objs.append(glyph(frame, oid, cx, yb - digit_h, digit_w if ch != "M" else 26, digit_h))
                cx += (digit_w if ch != "M" else 26) + 3
                oid += 1
        else:
            objs.append(glyph(frame, oid, x, yb - digit_h, digit_w, digit_h))
            oid += 1
    wy = base_y - (draft_m - 12.0) * px_per_m
    water = SamObject(frame, 0, (0.0, wy, 300.0, wy + 200), np.ones((200, 300), dtype=bool))
    return objs, water
