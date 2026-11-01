from conftest import DATA

from api._core import sam


def test_parsers_agree_on_real_output():
    text = (DATA / "sam_video_3frames.txt").read_text()
    a, b = sam.parse_own(text), sam.parse_msp(text)
    assert len(a) == len(b) > 20
    for x, y in zip(a, b):
        assert (x.frame, x.obj_id, x.box) == (y.frame, y.obj_id, y.box)
        assert x.mask.shape == y.mask.shape and (x.mask == y.mask).all()


def test_boxes_are_half_open_and_masks_box_local():
    objs = sam.parse_own("<0f>0<|box;x1=529;y1=454;x2=559;y2=489;w=1120;h=1120|>")
    assert objs[0].box == (529.0, 454.0, 560.0, 490.0)
    real = sam.parse((DATA / "sam_video_3frames.txt").read_text())
    o = real[0]
    assert o.mask.shape == (int(o.h), int(o.w))


def test_frames_and_water_mask_top():
    water = sam.parse((DATA / "sam_water_3frames.txt").read_text())
    fr = sam.by_frame(water)
    assert set(fr) == {0, 1, 2}
    w = fr[0][0]
    top = sam.mask_top_at(w, w.cx)
    assert top is not None and w.box[1] <= top < w.box[3]


def test_sam_object_cy():
    # 51: cy
    o = sam.SamObject(0, 1, (10.0, 20.0, 30.0, 40.0))
    assert o.cy == 30.0


def test_decode_and_parse_msp_without_msp(monkeypatch):
    # 72: _decode when msp is None
    monkeypatch.setattr(sam, "msp", None)
    assert sam._decode("~", "payload", 10, 10) is None

    # 99: parse_msp when msp is None
    import pytest
    with pytest.raises(ImportError, match="meta_sam_parser not installed"):
        sam.parse_msp("text")


def test_parse_msp_error_clears_raster(monkeypatch):
    # 110: sys.exc_info() in parse_msp
    import pytest
    from unittest.mock import Mock
    mock_parser = Mock()
    mock_parser.push.side_effect = RuntimeError("push error")
    mock_fmt = Mock()
    mock_fmt.create_parser.return_value = mock_parser
    monkeypatch.setattr(sam.msp, "video_segmentation_format", lambda: mock_fmt)
    with pytest.raises(RuntimeError, match="push error"):
        sam.parse_msp("corrupted text")


def test_parse_fallback_to_own(monkeypatch):
    # 132-134: parse_msp raises exception -> fallback to parse_own
    from unittest.mock import Mock
    monkeypatch.setattr(sam, "parse_msp", Mock(side_effect=RuntimeError("MSP boom")))
    objs = sam.parse("<0f>0<|box;x1=10;y1=20;x2=30;y2=40;w=100;h=100|>")
    assert len(objs) == 1
    assert objs[0].box == (10.0, 20.0, 31.0, 41.0)


def test_mask_top_and_bottom():
    import numpy as np
    # 147: mask_top_at with mask is None
    o_no_mask = sam.SamObject(0, 1, (10.0, 20.0, 30.0, 40.0), mask=None)
    assert sam.mask_top_at(o_no_mask, 15.0) is None

    # 161-164: mask_bottom
    assert sam.mask_bottom(o_no_mask) is None
    o_empty = sam.SamObject(0, 1, (10.0, 20.0, 30.0, 40.0), mask=np.zeros((10, 10), dtype=bool))
    assert sam.mask_bottom(o_empty) is None

    mask = np.zeros((10, 10), dtype=bool)
    mask[5, 5] = True
    o_valid = sam.SamObject(0, 1, (10.0, 20.0, 30.0, 40.0), mask=mask)
    assert sam.mask_bottom(o_valid) == 26.0

