import pytest
from synth import glyph, ship_frame

from api.core import marks


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
