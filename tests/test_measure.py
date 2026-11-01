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
    assert res.as_dict()["refused"] is True


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


def test_water_edge_bridges_a_small_hole_below_the_surface():
    from api._core.sam import SamObject
    m = np.ones((40, 10), dtype=bool)
    m[5:7, :] = False  # a 2-px glare hole just under the surface at y=100
    w, _, _ = measure.water_edge([SamObject(0, 1, (0.0, 100.0, 10.0, 140.0), m)], 0, 10)
    assert w == 100.0


def test_numeral_cut_by_the_frame_top_is_not_perspective():
    from synth import glyph

    from api._core.sam import SamObject
    # four dry numerals on a 120 px pitch (bottoms 400, 280, 160, 40); the top one is cut by the frame edge (box top 0,
    # 40 px tall against 60), its bottom edge is still where the print puts it
    objs = [glyph(0, k, 100, b - h, 40, h) for k, (b, h) in enumerate([(400, 60), (280, 60), (160, 60), (40, 40)])]
    toks = marks.group_glyphs(objs, marks.BARGE)
    z = {t.track: 0.02 * (k + 1) for k, t in enumerate(toks)}
    water = [SamObject(0, 99, (0.0, 500.0, 300.0, 600.0), np.ones((100, 300), dtype=bool))]
    fg = measure.frame_draft(0, toks, z, water, marks.BARGE)
    assert fg.drop_reason != "PERSPECTIVE" and fg.kept


def test_column_top_without_mask():
    from api._core.sam import SamObject
    o_no_mask = SamObject(0, 1, (0.0, 100.0, 10.0, 140.0), mask=None)
    o_mask = SamObject(0, 2, (0.0, 100.0, 10.0, 140.0), mask=np.ones((40, 10), dtype=bool))
    assert measure.column_top([o_no_mask, o_mask], 5) == 100.0


def test_frame_draft_drop_reasons():
    from api._core.sam import SamObject

    def _setup():
        t1 = marks.Token("1", (0,), (0, 200, 10, 260), bottom_px=260.0,
                         glyphs=[SamObject(0, 0, (0, 200, 10, 260))])
        t2 = marks.Token("2", (1,), (0, 140, 10, 200), bottom_px=200.0,
                         glyphs=[SamObject(0, 1, (0, 140, 10, 200))])
        t3 = marks.Token("3", (2,), (0, 80, 10, 140), bottom_px=140.0,
                         glyphs=[SamObject(0, 2, (0, 80, 10, 140))])
        drafts = {"1": 10.0, "2": 10.2, "3": 10.4}
        w = [SamObject(0, 99, (0, 280, 50, 350), np.ones((70, 50), dtype=bool))]
        return [t1, t2, t3], drafts, w

    toks, drafts, w = _setup()

    # 82-83: NO_LABELLED_MARKS
    fg_no_lab = measure.frame_draft(0, toks, {}, w, marks.SHIP)
    assert fg_no_lab.drop_reason == "NO_LABELLED_MARKS"

    # 88-89: NO_WATER_EDGE
    fg_no_water = measure.frame_draft(0, toks, drafts, [], marks.SHIP)
    assert fg_no_water.drop_reason == "NO_WATER_EDGE"

    # 117-118: SCALE_SIGN (b >= 0)
    toks_zero = [
        marks.Token("1", (0,), (0, 0, 10, 0), bottom_px=0.0),
        marks.Token("2", (1,), (20, 0, 30, 0), bottom_px=0.0),
        marks.Token("3", (2,), (40, 0, 50, 0), bottom_px=0.0),
    ]
    fg_scale = measure.frame_draft(0, toks_zero, {"1": 1.0, "2": 2.0, "3": 3.0},
                                   [SamObject(0, 0, (0, 50, 60, 100), np.ones((50, 60), dtype=bool))],
                                   marks.SHIP)
    assert fg_scale.drop_reason == "SCALE_SIGN"

    # 120-121: PITCH
    fg_pitch = measure.frame_draft(0, toks, drafts, w, marks.SHIP, pitch_ref_px=100.0)
    assert fg_pitch.drop_reason == "PITCH"

    # 123-124: RESIDUAL
    toks_r, drafts_r, w_r = _setup()
    toks_r[1] = marks.Token("2", (1,), (0, 120, 10, 180), bottom_px=180.0,
                            glyphs=[SamObject(0, 1, (0, 120, 10, 180))])
    fg_resid = measure.frame_draft(0, toks_r, drafts_r, w_r, marks.SHIP)
    assert fg_resid.drop_reason == "RESIDUAL"

    # 126-127: EDGE_NOISY
    toks_n, drafts_n, _ = _setup()
    noisy_mask = np.zeros((100, 50), dtype=bool)
    for col in range(50):
        noisy_mask[(16 if col % 2 == 0 else 48):, col] = True
    w_noisy = [SamObject(0, 99, (0, 370, 50, 470), noisy_mask)]
    fg_noisy = measure.frame_draft(0, toks_n, drafts_n, w_noisy, marks.SHIP)
    assert fg_noisy.drop_reason == "EDGE_NOISY"

    # 131-132: PERSPECTIVE
    toks_p, drafts_p, w_p = _setup()
    toks_p[0] = marks.Token("1", (0,), (0, 240, 10, 260), bottom_px=260.0,
                            glyphs=[SamObject(0, 0, (0, 240, 10, 260))])
    toks_p[1] = marks.Token("2", (1,), (0, 140, 10, 200), bottom_px=200.0,
                            glyphs=[SamObject(0, 1, (0, 140, 10, 200))])
    fg_persp = measure.frame_draft(0, toks_p, drafts_p, w_p, marks.SHIP)
    assert fg_persp.drop_reason == "PERSPECTIVE"


def test_lag1_short_series():
    # 185: len(x) < 3 returns 0.0
    assert measure.lag1(np.array([1.0, 2.0])) == 0.0
    assert measure.lag1(np.array([])) == 0.0

