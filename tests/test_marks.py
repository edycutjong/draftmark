import pytest
from synth import glyph, ship_frame

from api._core import marks


def test_metre_mark_glyphs_group_into_one_token():
    objs, _ = ship_frame()
    toks = marks.group_glyphs(objs)
    assert len(objs) == 8 + 2 + 2  # "12M" and "13M" each split into 3 glyphs
    assert len(toks) == 8
    assert sorted(t.n_glyphs for t in toks)[-2:] == [3, 3]


def test_barge_1m_split_in_two():
    objs = [glyph(0, 0, 100, 500, 10, 20), glyph(0, 1, 112, 500, 13, 20), glyph(0, 2, 103, 460, 10, 20),
            glyph(0, 3, 103, 420, 10, 20)]
    toks = marks.group_glyphs(objs, marks.BARGE)
    assert len(toks) == 3 and toks[0].n_glyphs == 2


def test_metre_token_groups_when_the_water_cuts_one_glyph():
    # "1" is cut by the water (bottom 8 px higher than "M"'s) but both keep the cap line: still one token
    objs = [glyph(0, 0, 100, 500, 10, 12), glyph(0, 1, 115, 500, 20, 20), glyph(0, 2, 103, 460, 10, 20),
            glyph(0, 3, 103, 420, 10, 20)]
    toks = marks.group_glyphs(objs, marks.BARGE)
    assert len(toks) == 3 and toks[0].n_glyphs == 2


def test_other_marks_do_not_group_by_cap_line():
    objs = [glyph(0, 0, 100, 500, 10, 20), glyph(0, 1, 100, 380, 10, 20)]  # a full pitch apart, same column
    assert len(marks.group_glyphs(objs, marks.BARGE)) == 2


def test_object_cap():
    objs = [glyph(0, i, 100, 40 * i, 10, 20) for i in range(16)]
    with pytest.raises(marks.ObjectCapError):
        marks.group_glyphs(objs)


def test_labels_to_drafts_ship_and_barge():
    assert marks.labels_to_drafts(["8", "12M", "2", "4"]) == [11.8, 12.0, 12.2, 12.4]
    assert marks.labels_to_drafts(["2", "4", "6", "8", "1M", "2"], marks.BARGE) == [0.02, 0.04, 0.06, 0.08, 0.1, 0.12]
    assert marks.labels_to_drafts(["2", "4"]) == [None, None]


def _tokens_and_labels():
    objs, _ = ship_frame()
    toks = marks.group_glyphs(objs)
    labs = ["12M", "2", "4", "6", "8", "13M", "2", "4"]
    return toks, {t.track: lab for t, lab in zip(toks, labs)}


def test_five_checks_pass_on_consistent_reads():
    toks, read = _tokens_and_labels()
    drafts, chk = marks.check_labels(toks, read, dict(read))
    assert chk.ok, chk.as_dict()
    assert drafts[toks[0].track] == 12.0 and drafts[toks[-1].track] == 13.4


def test_checks_catch_misreads():
    toks, read = _tokens_and_labels()
    bad = dict(read)
    bad[toks[3].track] = "8"  # duplicate digit -> not monotone
    assert not marks.check_labels(toks, bad, dict(bad))[1].monotone
    shifted = dict(read)
    shifted[toks[0].track], shifted[toks[5].track] = "2", "4"  # metre marks read as digits -> no wide anchor
    assert not marks.check_labels(toks, shifted, dict(shifted))[1].ok
    other = dict(read)
    other[toks[1].track] = "4"
    assert not marks.check_labels(toks, read, other)[1].cross_frame


def test_barge_strip_sequence_anchor():
    seq = marks.strip_sequence()
    assert seq[:6] == ["2", "4", "6", "8", "1M", "2"] and seq[-1] == "6" and "2M" in seq


def test_a_merged_metre_box_read_as_a_digit_fails_the_anchor():
    import dataclasses
    toks, read = _tokens_and_labels()
    t0 = toks[0]  # "12M" as ONE merged glyph box (SAM sometimes returns one box for "12M")
    toks[0] = dataclasses.replace(t0, glyph_ids=t0.glyph_ids[:1], glyphs=t0.glyphs[:1])
    assert toks[0].n_glyphs == 1 and marks.check_labels(toks, read, dict(read))[1].anchor
    shifted = {**read, toks[0].track: "8", toks[5].track: "12M"}  # merged 12M box read as a digit
    assert not marks.check_labels(toks, shifted, dict(shifted))[1].anchor


def test_mark_system_properties_and_token_cy():
    # 37: digit_h_m
    assert marks.SHIP.digit_h_m == 0.10
    assert marks.BARGE.digit_h_m == pytest.approx(0.010)

    # 40, 43: label_pattern, labels_enum
    pat = marks.SHIP.label_pattern()
    assert pat == r"^(?:[1-9][0-9]?M|[2468])$"
    assert "1M" in marks.SHIP.labels_enum()

    # 68, 72: Token.h, Token.cy
    t = marks.Token(track="t0", glyph_ids=(0,), box=(10, 20, 30, 40))
    assert t.h == 20.0
    assert t.cy == 30.0

    # 78: bottom_px cached
    t_cached = marks.Token(track="t0", glyph_ids=(0,), box=(10, 20, 30, 40), bottom_px=42.0)
    assert t_cached.mask_bottom() == 42.0

    # 99: group_glyphs empty
    assert marks.group_glyphs([]) == []


def test_mask_bottom_fallback_and_empty():
    import numpy as np
    from api._core.sam import SamObject

    # 82, 89: glyph without mask or with all-false mask
    g1 = SamObject(frame=0, obj_id=0, box=(10, 20, 30, 40), mask=None)
    g2 = SamObject(frame=0, obj_id=1, box=(10, 20, 30, 40), mask=np.zeros((20, 20), dtype=bool))
    t = marks.Token(track="t0", glyph_ids=(0, 1), box=(10, 20, 30, 40), glyphs=(g1, g2))
    assert t.mask_bottom() == 40.0


def test_resolve_drafts_unknown_label():
    # 155-156: unknown label appends None
    res = marks.labels_to_drafts(["?", "12M", "2"])
    assert res == [None, 12.0, 12.2]


def test_check_labels_no_second_read_and_table_range_and_strip():
    toks, read = _tokens_and_labels()

    # 180: as_dict
    drafts, chk_init = marks.check_labels(toks, read, dict(read))
    d_dict = chk_init.as_dict()
    assert d_dict["ok"] is True and "monotone" in d_dict

    # 211-212: read2 is None
    _, chk_none = marks.check_labels(toks, read, read2=None)
    assert chk_none.cross_frame is False
    assert chk_none.detail["cross_frame_note"] == "no second read"

    # 230: table_range
    _, chk_in_range = marks.check_labels(toks, read, dict(read), table_range=(10.0, 15.0))
    assert chk_in_range.anchor is True
    _, chk_out_range = marks.check_labels(toks, read, dict(read), table_range=(1.0, 2.0))
    assert chk_out_range.anchor is False

    # 226-227, 239-240: strip_sequence and _is_subsequence
    labs = [read[t.track] for t in toks]
    # Pass matching strip sequence
    _, chk_strip = marks.check_labels(toks, read, dict(read), strip_sequence=labs)
    assert chk_strip.anchor is True

    # Pass subsequence strip sequence
    sub_seq = ["12M", "6", "13M", "4"]
    sub_toks = [t for t in toks if read[t.track] in sub_seq]
    sub_read = {t.track: read[t.track] for t in sub_toks}
    _, chk_sub = marks.check_labels(sub_toks, sub_read, dict(sub_read), strip_sequence=labs)
    assert chk_sub.anchor is True

    # Directly test _is_subsequence
    sub = ["2", "4", "1M"]
    seq = marks.strip_sequence()
    assert marks._is_subsequence(sub, seq) is True
    assert marks._is_subsequence(["1M", "1M"], seq) is False

