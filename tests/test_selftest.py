from unittest.mock import patch
from api._core import selftest, reference_survey as R
from api._core.sandbox import RunResult


def test_first_diverging():
    # Base dictionary matching TRACE
    ref = {k: 10.0 for k in selftest.TRACE}
    got = dict(ref)
    assert selftest.first_diverging(got, ref) is None

    # Line 89-90: not isinstance(g, (int, float))
    got_non_num = dict(ref)
    first_k = selftest.TRACE[0]
    got_non_num[first_k] = "not_a_number"
    assert selftest.first_diverging(got_non_num, ref) == first_k

    # Line 92-93: d_ / disp divergence (1e-4 threshold)
    got_d = dict(ref)
    d_key = next(k for k in selftest.TRACE if k.startswith(("d_", "disp")))
    got_d[d_key] = ref[d_key] + 0.1  # error 0.01 > 1e-4
    assert selftest.first_diverging(got_d, ref) == d_key

    # Line 92-93: other key divergence (2e-2 threshold)
    got_other = dict(ref)
    other_key = next(k for k in selftest.TRACE if not k.startswith(("d_", "disp")))
    got_other[other_key] = ref[other_key] + 1.0  # error 0.1 > 2e-2
    assert selftest.first_diverging(got_other, ref) == other_key


def test_selftest_booklet_mode_and_sandbox_error():
    # Line 105: ship is None -> req["booklet"] = booklet
    # Line 109: rr.ok is False
    with patch("api._core.selftest.sandbox.run") as mock_run:
        mock_run.return_value = RunResult(False, {}, "sandbox error", 12, -1)
        st = selftest.run("code", booklet={"id": "trieste"}, ship=None, n_diff=1)
        assert mock_run.call_args[0][1]["booklet"] == {"id": "trieste"}
        assert st.verdict == "FAIL"
        assert st.error == "sandbox error"
        d = st.as_dict()
        assert d["verdict"] == "FAIL"
        assert "ship" not in d


def test_selftest_row_failure_and_diff_cases():
    # Line 115-116: r["ok"] is False in conds
    # Line 130-131: R.survey raises OutOfTable in diff
    # Line 133-134: r["ok"] is False or disp_final not numeric in diff
    conds = selftest.conditions()
    n_conds = len(conds)
    n_diff = 3

    # Prepare mocked results
    # 1. conds results: first condition fails, rest succeed
    res_conds = [{"ok": False, "error": "division by zero"}]
    for c in conds[1:]:
        res_conds.append({
            "ok": True,
            "out": {**{k: 10.0 for k in selftest.TRACE}, "disp_final": c["expected"]}
        })

    # 2. probes results
    res_probes = [{"ok": False, "error": "OutOfTable: probe 1"},
                  {"ok": False, "error": "OutOfTable: probe 2"}]

    # 3. diff results:
    # case 0: R.survey raises OutOfTable -> hits 130-131
    # case 1: r not ok -> hits 133-134
    # case 2: r ok with disp_final -> hits 135
    res_diff = [
        {"ok": True, "out": {"disp_final": 50000.0}},
        {"ok": False, "error": "diff fail"},
        {"ok": True, "out": {"disp_final": 50000.0}},
    ]

    all_res = res_conds + res_probes + res_diff

    with patch("api._core.selftest.sandbox.run") as mock_run:
        mock_run.return_value = RunResult(True, {"results": all_res}, None, 50, 0)

        # Make R.survey raise OutOfTable on the first diff case (hits 130-131)
        orig_survey = R.survey
        call_count = [0]

        def patched_survey(inputs, **kwargs):
            call_count[0] += 1
            if call_count[0] == n_conds + 1:  # first diff case
                raise R.OutOfTable("diff out of table")
            return orig_survey(inputs, **kwargs)

        with patch.object(R, "survey", side_effect=patched_survey):
            st = selftest.run("code", ship={"id": "ship1"}, n_diff=n_diff)
            assert st.verdict == "FAIL"
            assert st.pass_count == n_conds - 1
            assert st.differential_failures == 1
            assert st.rows[0].first_diverging == "raised"
            assert st.rows[0].error == "division by zero"
