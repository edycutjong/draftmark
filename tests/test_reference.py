import pytest

from api.core import reference_survey as R
from api.core import selftest


def test_reference_reproduces_all_printed_conditions():
    for c in selftest.conditions():
        got = R.survey(c["inputs"])["disp_final"]
        assert abs(got - c["expected"]) / c["expected"] * 100 <= selftest.tol_pct(c["expected"]), c["cond_id"]


def test_booklet_verbatim_fails_high_trim_rows():
    passed = sum(abs(R.survey(c["inputs"], second_trim=False)["disp_final"] - c["expected"]) / c["expected"] * 100
                 <= 0.1 for c in selftest.conditions())
    assert passed == 14


def test_lightship_intermediates_match_booklet_printout():
    c = selftest.conditions()[0]
    o = R.survey(c["inputs"])
    assert round(o["d_fp"], 3) == 4.732 and round(o["d_ap"], 3) == 4.529


def test_out_of_table_raises():
    with pytest.raises(R.OutOfTable):
        R.survey(selftest.PROBES[0])
    with pytest.raises(R.OutOfTable):
        R.survey(selftest.PROBES[1])


def test_conditions_have_page_refs_and_22_rows():
    conds = selftest.conditions()
    assert len(conds) == 22 and all(c["page"] > 0 for c in conds)
