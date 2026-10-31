import pytest

from api._core import selftest as T
from api._core import survey as S

COND = {c["cond_id"]: c for c in T.conditions()}


def drafts_of(cid):
    return {k: COND[cid]["inputs"][k] for k in S.POSITIONS}


def run(d, live=("mid_p", "mid_s"), u=0.01, **kw):
    src = {p: ("live" if p in live else "entered") for p in S.POSITIONS}
    return S.ship({"drafts": d, "sources": src, "u_live_m": u, "sg": 1.025, **kw})


def test_proven_program_reproduces_printed_condition():
    r = run(drafts_of("4.1"))
    assert abs(r["disp"] - COND["4.1"]["expected"]) / COND["4.1"]["expected"] * 100 <= T.tol_pct(17827.7)
    assert r["program_author"] == "muse-wonder-1.0" and r["n_cases"] == 9


def test_sensitivity_and_finite_difference_u():
    r = run(drafts_of("4.1"))
    assert r["t_per_mm"]["mid_p"] > r["t_per_mm"]["aft_p"] > r["t_per_mm"]["fore_p"] > 0
    expect = (r["t_per_mm"]["mid_p"] + r["t_per_mm"]["mid_s"]) * 10  # u = 10 mm on both live positions
    assert r["u_disp"] == pytest.approx(expect, rel=0.02)
    assert r["n_entered"] == 4 and r["consequence"]["tpc_t_per_cm"] > 0


def test_out_of_table_refuses_to_extrapolate():
    r = run({p: 12.76 for p in S.POSITIONS})
    assert r["out_of_table"] and "OutOfTable" in r["error"] and "disp" not in r


def test_perturbation_off_table():
    r = run({p: 8.78 for p in S.POSITIONS}, live=S.POSITIONS, u=0.05)  # +u walks past 8.8 m (Nemoto edge)
    assert not r["out_of_table"] and r["perturb_oot"]


def test_nemoto_points_never_extrapolate():
    # 9.0 m is inside the printed table (0.5-9.3 m) but MTC at 9.5 m is not: refuse, never extrapolate
    r = run({p: 9.0 for p in S.POSITIONS})
    assert r["out_of_table"] and "MTC" in r["error"] and "cargo" not in r


@pytest.mark.parametrize("change,frag", [({"fore_s": 0.4}, "port/starboard"), ({"mid_p": 0.25, "mid_s": 0.25}, "hog/sag")])
def test_entered_gate(change, frag):
    d = drafts_of("4.1")
    for k, v in change.items():
        d[k] += v
    r = run(d)
    assert r["entered_inconsistent"] and any(frag in g for g in r["gate_fail"])


def test_cargo_kinds():
    d = drafts_of("4.1")
    ded = {"ballast": 500, "fw": 100}
    single = run(d, deductibles=ded, lightship_constant=11000)
    paired = run(d, deductibles=ded, initial_net=12000)
    none = run(d, deductibles=ded)
    assert single["cargo_kind"] == "single" and single["cargo"] == pytest.approx(single["disp"] - 600 - 11000)
    assert paired["cargo_kind"] == "paired" and paired["cargo"] == pytest.approx(paired["net"] - 12000)
    assert none["cargo"] is None and none["u_cargo"] is None


def test_barge_analytic_and_what_if():
    r = S.barge({"d_m": 0.12, "u_m": 0.0006})
    b = r["barge"]
    assert r["cargo"] == pytest.approx(b["rho_kg_m3"] * b["L_m"] * b["B_m"] * 0.12 - b["light_kg"])
    assert r["program_author"] == "analytic" and not r["what_if"]
    assert S.barge({"d_m": 0.12, "u_m": 0.0006, "what_if": {"rho_kg_m3": 1000}})["what_if"]
    assert S.barge({"d_m": 0.45, "u_m": 0.0006})["out_of_table"]


def test_proven_refuses_a_stale_selftest(tmp_path, monkeypatch):
    import json
    import shutil

    from api._core import survey as S
    src = S.DATA / "programs" / "trieste"
    dst = tmp_path / "programs" / "trieste"
    shutil.copytree(src, dst)
    run = dst / json.loads((dst / "proven.json").read_text())["default_program"]
    st = json.loads((run.parent / "selftest.json").read_text())
    (run.parent / "selftest.json").write_text(json.dumps({**st, "verdict": "FAIL"}))
    monkeypatch.setattr(S, "DATA", tmp_path)
    with pytest.raises(RuntimeError):
        S.proven("trieste")


def test_a_clip_reading_stands_only_for_midships():
    r = run(drafts_of("4.1"), live=S.POSITIONS)
    assert [p for p in S.POSITIONS if r["sources"][p] == "live"] == ["mid_p", "mid_s"] and r["n_entered"] == 4


def test_a_program_failure_is_not_an_issue(monkeypatch):
    monkeypatch.setattr(S.sandbox, "run", lambda code, req: S.sandbox.RunResult(False, {}, "exit 1: boom", 5, 1))
    r = run(drafts_of("4.1"))
    assert r["program_error"] and not r["out_of_table"] and "cargo" not in r


def test_survey_inputs_are_validated():
    ok = {"drafts": drafts_of("4.1"), "sg": 1.025, "deductibles": {"fuel": 120}}
    assert S.validate(ok, {}) == []
    bad = {**ok, "sg": 2.0, "deductibles": {"fuel": -500}, "lightship_constant": float("nan")}
    msgs = S.validate(bad, {"tol_pct": 1e9})
    assert len(msgs) == 4 and any("sg" in m for m in msgs) and any("tol_pct" in m for m in msgs)


def test_non_finite_or_mislabelled_program_output_is_a_program_error(monkeypatch):
    real = S.sandbox.run

    def nan_run(code, req):
        rr = real(code, req)
        rr.data["results"][0]["out"]["disp_final"] = float("nan")
        return rr
    monkeypatch.setattr(S.sandbox, "run", nan_run)
    assert run(drafts_of("4.1"))["program_error"]
    monkeypatch.setattr(S.sandbox, "run", lambda code, req: S.sandbox.RunResult(
        True, {"ok": True, "results": [{"ok": False, "error": "KeyError: 'OutOfTable'"}]}, None, 5, 0))
    r = run(drafts_of("4.1"))
    assert r["program_error"] and not r["out_of_table"]
    assert S.clean_sources({"mid_p": "foo", "mid_s": "live", "fore_p": "live"}) == \
        {"mid_p": "entered", "mid_s": "live", "fore_p": "entered"}
