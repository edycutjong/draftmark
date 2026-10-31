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
