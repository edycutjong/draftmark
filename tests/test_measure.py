import numpy as np
from synth import ship_frame

from api._core import marks, measure


def _clip(drafts):
    toks, water = {}, {}
    labs = ["12M", "2", "4", "6", "8", "13M", "2", "4"]
    for i, d in enumerate(drafts):
        objs, w = ship_frame(frame=i, draft_m=d)
        toks[i] = marks.group_glyphs(objs)
        water[i] = [w]
    lab = {t.track: z for t, z in zip(toks[0], marks.labels_to_drafts(labs))}
    return toks, water, lab


def test_single_frame_recovers_known_draft():
    toks, water, lab = _clip([12.37])
    fg = measure.frame_draft(0, toks[0], lab, water[0], marks.SHIP)
    assert fg.kept and abs(fg.d_m - 12.37) < 0.004  # sub-pixel quantisation only
    assert fg.n_dry == 2 + 0 or fg.n_dry >= 3


def test_submerged_marks_excluded_and_low_dry_dropped():
    toks, water, lab = _clip([13.25])  # only "4" (13.4) dry
    fg = measure.frame_draft(0, toks[0], lab, water[0], marks.SHIP)
    assert not fg.kept and fg.drop_reason == "DRY_MARKS_LOW"


def test_clip_average_and_uncertainty():
    rng = np.random.default_rng(1)
    t = np.arange(60) / 6
    truth = 12.40
    series = truth + 0.12 * np.sin(2 * np.pi * t / 4.0) + rng.normal(0, 0.01, 60)
    toks, water, lab = _clip(series)
    frames, res = measure.measure_clip(toks, water, lab, marks.SHIP, u_sys_parts={"scale": 0.005})
    assert not res.refused and res.n_kept >= 55
    assert abs(res.d_m - series.mean()) < 0.005
    assert 0 < res.u_rep_m < 0.1 and res.u_abs_m >= res.u_rep_m
    assert 2 <= res.n_eff <= 60 and 0 <= res.rho1 <= 0.99


def test_refuses_when_frames_low():
    toks, water, lab = _clip([13.3] * 10)
    _, res = measure.measure_clip(toks, water, lab, marks.SHIP)
    assert res.refused and res.reason == "FRAMES_LOW"


def test_track_swap_drops_the_frame():
    from api._core import marks
    objs, water = ship_frame()
    toks = marks.group_glyphs(objs, marks.SHIP)
    labs = ["12M", "2", "4", "6", "8", "13M", "2", "4"]
    drafts = dict(zip([t.track for t in toks], marks.labels_to_drafts(labs)))
    ok = measure.frame_draft(0, toks, drafts, [water], marks.SHIP)
    a, b = toks[-1].track, toks[-2].track  # SAM swapped two dry ids: their stored drafts no longer follow height
    drafts[a], drafts[b] = drafts[b], drafts[a]
    bad = measure.frame_draft(0, toks, drafts, [water], marks.SHIP)
    assert ok.kept and (bad.kept, bad.drop_reason) == (False, "TRACK_UNSTABLE")


def test_water_edge_ignores_a_detached_spray_blob():
    from api._core.sam import SamObject
    body = np.zeros((40, 10), dtype=bool)
    body[:, :] = True  # water from y=100 down to the crop bottom
    spray = np.ones((3, 10), dtype=bool)  # a reflection blob 12 px above the surface, not connected
    objs = [SamObject(0, 1, (0.0, 100.0, 10.0, 140.0), body), SamObject(0, 2, (0.0, 85.0, 10.0, 88.0), spray)]
    w, mad, n = measure.water_edge(objs, 0, 10)
    assert (w, mad, n) == (100.0, 0.0, 10)
    joined = [SamObject(0, 1, (0.0, 97.0, 10.0, 140.0), np.ones((43, 10), dtype=bool))]  # touching = one surface
    assert measure.water_edge(joined, 0, 10)[0] == 97.0


def test_cross_frame_needs_three_shared_tokens():
    toks = marks.group_glyphs(ship_frame()[0])
    labs = ["12M", "2", "4", "6", "8", "13M", "2", "4"]
    read = {t.track: lab for t, lab in zip(toks, labs)}
    one = {toks[2].track: read[toks[2].track]}  # the second read kept a single agreeing token
    assert not marks.check_labels(toks, read, one)[1].cross_frame
    three = {t.track: read[t.track] for t in toks[:3]}
    assert marks.check_labels(toks, read, three)[1].cross_frame
