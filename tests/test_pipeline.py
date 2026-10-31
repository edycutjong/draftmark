import numpy as np
import pytest
from synth import glyph, ship_frame

from api._core import marks, measure, pipeline
from api._core.sam import SamObject


def clip(n=12, water_x=(0.0, 300.0)):
    num, wat = [], []
    for i in range(n):
        objs, water = ship_frame(frame=i, draft_m=12.73 + 0.03 * np.sin(i), start_id=0)
        num += objs
        x0, x1 = water_x
        wy = water.box[1]
        wat.append(SamObject(i, 0, (x0, wy, x1, wy + 200), np.ones((200, int(x1 - x0)), dtype=bool)))
    return num, wat



def labelled(g):
    toks, _ = pipeline.rebuild(g)
    f = g["label_frames"][0]
    labs = ["12M", "2", "4", "6", "8", "13M", "2", "4"]
    return {t.track: lab for t, lab in zip(toks[f], labs)}


def test_compact_geometry_reproduces_mask_level_result():
    num, wat = clip()
    g = pipeline.geometry_from_objects(num, wat, 12, 6.0, marks.SHIP)
    assert g["row1"] is None and len(g["label_frames"]) == 2
    read = labelled(g)
    drafts, chk = pipeline.check(g, {g["label_frames"][0]: read, g["label_frames"][1]: read})
    assert chk.ok
    _, res = pipeline.finish(g, drafts)
    from api._core import sam
    toks, _, _ = pipeline.tokens_by_frame(sam.by_frame(num), 12, marks.SHIP)
    _, ref = measure.measure_clip(toks, sam.by_frame(wat), drafts, marks.SHIP)
    assert res.d_m == pytest.approx(ref.d_m, abs=1e-12) and res.u_rep_m == pytest.approx(ref.u_rep_m, abs=1e-12)
    assert res.n_kept == ref.n_kept == 12


def test_label_frames_one_second_apart():
    num, wat = clip()
    g = pipeline.geometry_from_objects(num, wat, 12, 6.0, marks.SHIP)
    f1, f2 = g["label_frames"]
    assert abs(f1 - f2) >= 6


def test_row1_no_masks():
    num, _ = clip()
    assert pipeline.geometry_from_objects(num, [], 12, 6.0, marks.SHIP)["row1"] == "NO_MASKS"
    assert pipeline.geometry_from_objects([], clip()[1], 12, 6.0, marks.SHIP)["row1"] == "NO_MASKS"


def test_row1_object_cap():
    num, wat = clip()
    num += [glyph(3, 100 + k, 250, 10 + 20 * k, 10, 12) for k in range(8)]  # 19 raw objects in frame 3
    g = pipeline.geometry_from_objects(num, wat, 12, 6.0, marks.SHIP)
    assert g["row1"] == "OBJECT_CAP" and g["object_cap_frames"] == [3]


def test_row1_water_miss():
    num, wat = clip(water_x=(400.0, 600.0))
    assert pipeline.geometry_from_objects(num, wat, 12, 6.0, marks.SHIP)["row1"] == "WATER_MISS"
