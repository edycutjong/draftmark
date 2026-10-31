import pytest

from api._core import barge


def test_box_displacement_and_cargo():
    b = barge.Barge(L_m=0.1, B_m=0.1, light_kg=0.2, rho_kg_m3=1000.0)
    out = barge.survey(b, 0.12)
    assert out["disp_kg"] == pytest.approx(1.2)
    assert out["cargo_kg"] == pytest.approx(1.0)
    assert out["program_author"] == "analytic"


def test_zero_offset_and_uncertainty():
    b = barge.Barge(L_m=0.1, B_m=0.1, light_kg=0.2, zero_offset_m=0.002, rho_kg_m3=1000.0)
    out = barge.survey(b, 0.118, u_draft_m=0.001, u_geom={"u_L": 0.0005, "u_B": 0.0005})
    assert out["disp_kg"] == pytest.approx(1.2)
    # 1 mm of draft on 100 cm^2 = 10 g; 0.5 mm on 100 mm sides = 0.5 % each
    assert out["u_disp_kg"] == pytest.approx((0.01 ** 2 + 2 * (0.006) ** 2 + 0.001 ** 2) ** 0.5, rel=1e-3)


def test_out_of_box_raises():
    with pytest.raises(ValueError):
        barge.displacement_kg(barge.Barge(0.1, 0.1, 0.2), -0.01)
