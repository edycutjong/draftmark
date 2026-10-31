import pytest

from api._core import decision as D

from decision_cases import CASES, OK_BARGE, OK_SHIP


@pytest.mark.parametrize("name", sorted(CASES))
def test_reason(name):
    facts, decision, reason = CASES[name]
    d = D.decide(facts)
    assert (d.decision, d.reason) == (decision, reason), d
    if decision == "ISSUE_WITH_WARNING":
        assert name in [w["code"] for w in d.warnings]


def test_every_reason_has_a_fixture():
    covered = {c[2] for c in CASES.values()} | set(CASES)
    for code in D.HINTS:
        assert code in covered or code == "BL_DIFFERENCE" and "PROTEST" in CASES, code


def test_order_first_refuse_wins():
    d = D.decide({**OK_SHIP, "row1": "OBJECT_CAP", "n_kept": 1, "out_of_table": True})
    assert d.reason == "OBJECT_CAP" and d.row == 1


def test_protest_keeps_warnings():
    d = D.decide({**OK_SHIP, "bl": 5200.0, "tol_pct": 0.5, "n_entered": 2})
    assert d.decision == "PROTEST" and [w["code"] for w in d.warnings] == ["POSITIONS_ENTERED"]


def test_no_protest_in_barge_mode():
    assert D.decide({**OK_BARGE, "bl": 2.0, "tol_pct": 0.5}).decision == "ISSUE"


def test_what_if_never_issues():
    assert D.decide({**OK_BARGE, "what_if": True, "n_kept": 25}).decision == "NOT_SCORED"


def test_frames_gate_boundaries():
    assert D.decide({**OK_BARGE, "n_frames": 10, "n_kept": 6}).decision == "ISSUE_WITH_WARNING"
    assert D.decide({**OK_BARGE, "n_frames": 10, "n_kept": 5}).reason == "FRAMES_LOW"
    assert D.decide({**OK_BARGE, "n_frames": 10, "n_kept": 9}).decision == "ISSUE"


def test_zero_cargo_with_uncertainty_never_passes():
    d = D.decide({**OK_SHIP, "cargo": 0.0, "u_cargo": 5.0})
    assert (d.decision, d.reason) == ("REFUSE", "U_TOO_WIDE")
