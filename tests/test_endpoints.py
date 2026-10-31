import base64

import pytest
from fastapi.testclient import TestClient
from test_pipeline import clip, labelled

from api import index
from api._core import limits, marks, pipeline, sign

api = TestClient(index.app)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    limits.reset()
    monkeypatch.setenv("JUDGE_CODE", "j" * 32)
    monkeypatch.setenv("MODEL_API_KEY", "test-not-a-key")
    monkeypatch.delenv("LIVE_MODE", raising=False)
    yield
    limits.reset()


def mp4(n=10):
    return "data:video/mp4;base64," + base64.b64encode(b"\0" * n).decode()


def test_upload_mime_size_and_judge_code():
    r = api.post("/api/py/measure", json={"upload": "data:video/webm;base64,AAAA"})
    assert r.status_code == 415 and r.json()["reason"] == "PAYLOAD"
    r = api.post("/api/py/measure", json={"upload": mp4(), "fps": 6})
    assert r.status_code == 400 and r.json()["reason"] == "PAYLOAD"  # frame count required
    r = api.post("/api/py/measure", json={"upload": mp4(3 * 1024 * 1024 + 3)})
    assert r.status_code == 413 and r.json()["reason"] == "PAYLOAD"
    r = api.post("/api/py/measure", json={"upload": mp4(), "fps": 12, "frames": 30})
    assert r.status_code == 413
    r = api.post("/api/py/measure", json={"upload": mp4(), "judge_code": "wrong", "fps": 6, "frames": 30})
    assert r.status_code == 403 and r.json()["reason"] == "JUDGE_CODE"


def test_kill_switch_and_unknown_fixture(monkeypatch):
    assert api.post("/api/py/measure", json={"fixture": "nope"}).json()["reason"] == "NO_FIXTURE"
    monkeypatch.setenv("LIVE_MODE", "off")
    r = api.post("/api/py/measure", json={"upload": mp4(), "judge_code": "j" * 32, "fps": 6, "frames": 30})
    assert r.status_code == 503 and r.json()["reason"] == "BUDGET"
    assert api.get("/api/py/health").json()["budget"] == "LIVE_MODE=off"


def test_budget_trip_fails_closed():
    limits.trip_budget("HTTP 402")
    r = api.post("/api/py/measure", json={"upload": mp4(), "judge_code": "j" * 32, "fps": 6, "frames": 30})
    assert r.status_code == 503 and r.json()["reason"] == "BUDGET"


def test_rate_limit_per_ip_then_instance():
    for _ in range(limits.PER_IP_H):
        assert limits.take("1.1.1.1", now=1000.0)[0]
    ok, why = limits.take("1.1.1.1", now=1001.0)
    assert not ok and "per IP" in why
    assert limits.take("1.1.1.1", now=1000.0 + 3601)[0]  # window slides
    for i in range(limits.PER_INSTANCE_H):
        limits.take(f"2.2.2.{i}", now=5000.0)
    assert "per instance" in limits.take("3.3.3.3", now=5001.0)[1]


def _geom():
    num, wat = clip()
    return sign.seal_geometry(pipeline.geometry_from_objects(num, wat, 12, 6.0, marks.SHIP))


def seal(m, lab=None, models=(), scale=0.1):
    """A measure token as /draft would issue it for this measurement (tests of the /survey decision logic)."""
    lab = lab or {}
    payload = {**{k: m.get(k) for k in index.MEAS_KEYS}, "scale": scale, "run_id": "t", "source": "upload",
               "clip": "upload", "typed": bool(lab.get("typed")), "checks": lab.get("checks") or {},
               "models": list(models)}
    return {**m, "token": sign.token("measure", payload)}


def test_typed_labels_then_draft():
    g = _geom()
    r = api.post("/api/py/labels", json={"geometry": g, "typed": labelled(g)}).json()
    assert r["typed"] and r["checks"]["ok"] and r["usage"] == []
    d = api.post("/api/py/draft", json={"geometry": g, "drafts": r["drafts"], "labels_token": r["labels_token"]}).json()
    assert d["result"]["n_kept"] == 12 and 12.6 < d["result"]["d_m"] < 12.8
    assert sign.token_ok("measure", d["result"]["token"])["d_m"] == d["result"]["d_m"]


OK_LABELS = {"checks": {k: True for k in ("monotone", "pitch", "residual", "cross_frame", "anchor", "ok")},
             "anchor_confirmed": True}


def test_survey_ship_out_of_table_refuses_without_cargo():
    s = {"drafts": {p: 12.73 for p in ("fore_p", "fore_s", "mid_p", "mid_s", "aft_p", "aft_s")}, "sg": 1.025}
    c = api.post("/api/py/survey", json={"mode": "ship", "survey": s, "measure": seal({"d_m": 12.73, "u_rep_m": 0.01, "n_frames": 12, "n_kept": 12}, OK_LABELS, scale=1.0),
                                          "labels": OK_LABELS})
    cert = c.json()["certificate"]
    assert (cert["decision"], cert["reason"]) == ("REFUSE", "OUT_OF_TABLE") and "cargo" not in cert["survey"]
    assert cert["footer"].startswith("Prototype")


def test_survey_barge_issue_and_what_if():
    m = {"d_m": 0.12, "u_abs_m": 0.0005, "n_frames": 32, "n_kept": 32}
    c = api.post("/api/py/survey", json={"mode": "barge", "measure": seal(m, OK_LABELS), "labels": OK_LABELS}).json()["certificate"]
    assert c["decision"] == "ISSUE" and c["program_author"] == "analytic" and c["proof"] == "measurement"
    assert c["models"] == []  # no model was called in this request
    c = api.post("/api/py/survey", json={"mode": "barge", "measure": seal(m, OK_LABELS), "labels": OK_LABELS,
                                         "what_if": {"rho_kg_m3": 1000}}).json()
    assert c["certificate"]["decision"] == "NOT_SCORED"


def test_selftest_rerun_and_program():
    st = api.post("/api/py/selftest/rerun").json()["selftest"]
    assert st["verdict"] == "PASS" and st["pass_count"] == 22
    p = api.get("/api/py/program").json()
    assert p["meta"]["program_author"] == "muse-wonder-1.0" and "def survey" in p["code"]


def test_measured_clip_without_labels_fails_closed():
    m = {"d_m": 0.12, "u_abs_m": 0.0005, "n_frames": 32, "n_kept": 32}
    c = api.post("/api/py/survey", json={"mode": "barge", "measure": seal(m)}).json()["certificate"]
    assert (c["decision"], c["reason"]) == ("REFUSE", "LABEL_FAIL")


def test_rejected_anchor_refuses():
    m = {"d_m": 0.12, "u_abs_m": 0.0005, "n_frames": 32, "n_kept": 32}
    lab = {**OK_LABELS, "anchor_confirmed": False}
    c = api.post("/api/py/survey", json={"mode": "barge", "measure": seal(m, lab), "labels": lab}).json()["certificate"]
    assert (c["decision"], c["reason"]) == ("REFUSE", "NO_ANCHOR") and c["labels"]["anchor_confirmed"] is False


def test_ship_measurement_refusal_is_certified_without_a_survey():
    m = {"d_m": None, "refused": True, "reason": "FRAMES_LOW", "n_frames": 60, "n_kept": 20}
    c = api.post("/api/py/survey", json={"mode": "ship", "measure": seal(m, OK_LABELS, ["sam-3.1"], 1.0),
                                         "labels": OK_LABELS, "survey": None,
                                         "models": ["muse-wonder-1.0", "not-a-model"]}).json()["certificate"]
    assert (c["decision"], c["reason"]) == ("REFUSE", "FRAMES_LOW") and c["models"] == ["sam-3.1"]
    assert "cargo" not in c["facts"]


def test_labels_require_the_measure_label_frames():
    g = _geom()
    r = api.post("/api/py/labels", json={"geometry": g, "frames": {"0": "data:image/jpeg;base64,AA"}})
    assert r.status_code == 400 and r.json()["reason"] == "LABEL_FRAMES"


def test_refusal_prints_no_computed_figures():
    d = {p: 6.5 for p in ("fore_p", "fore_s", "mid_p", "mid_s", "aft_p", "aft_s")}
    d["mid_p"] = d["mid_s"] = 6.9  # implied sag 0.4 m: ENTERED_INCONSISTENT
    c = api.post("/api/py/survey", json={"mode": "ship", "survey": {"drafts": d, "sg": 1.025},
                                         "booklet_info": {"id": "trieste"}}).json()["certificate"]
    assert (c["decision"], c["reason"]) == ("REFUSE", "ENTERED_INCONSISTENT")
    assert not {"trace", "t_per_mm", "disp", "deductions", "consequence"} & set(c["survey"]) and c["survey"]["gate_fail"]


def test_survey_needs_evidence():
    assert api.post("/api/py/survey", json={"mode": "ship"}).json()["reason"] == "NO_EVIDENCE"
    r = api.post("/api/py/survey", json={"mode": "barge", "measure": {"d_m": 0.1, "u_rep_m": 0.0005}})
    assert r.status_code == 400
    m = {"n_frames": 32, "n_kept": 32, "d_m": None}  # measured but no draft: certified as a refusal
    c = api.post("/api/py/survey", json={"mode": "barge", "measure": seal(m, OK_LABELS), "labels": OK_LABELS}).json()["certificate"]
    assert (c["decision"], c["reason"]) == ("REFUSE", "FRAMES_LOW")


def test_label_quota_rides_once_on_its_measure():
    assert limits.take("9.9.9.9", now=10.0, run_id="r1")[0]  # the measure call
    for _ in range(limits.PER_IP_H - 1):
        limits.take("9.9.9.9", now=11.0)
    assert limits.take("9.9.9.9", now=12.0, run_id="r1", ride=True)[0]  # first labels call is free
    assert not limits.take("9.9.9.9", now=13.0, run_id="r1", ride=True)[0]  # a second one is not
    assert not limits.take("9.9.9.9", now=14.0, run_id="r1")[0]  # re-using the id never frees a measure


def test_reread_carries_failed_checks_by_box_number(monkeypatch):
    import io

    from PIL import Image

    from api._core import labels as L
    g = _geom()
    good = labelled(g)
    buf = io.BytesIO()
    Image.new("RGB", (400, 1000)).save(buf, "JPEG")
    url = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    calls = []

    def fake_read(client, img, numbering, system, feature="", hint=None):
        calls.append(hint)
        by = dict(good)
        if len(calls) <= 2:  # attempt 1: one frame swaps two labels -> cross-frame + monotone fail
            ks = sorted(by)[:2]
            by[ks[0]], by[ks[1]] = by[ks[1]], by[ks[0]]
            if len(calls) == 2:
                by = dict(good)
        return {t: v for t, v in by.items() if t in numbering.values()}, {"response_id": f"r{len(calls)}"}

    class Dummy:
        rows: list = []

    monkeypatch.setattr(L, "read", fake_read)
    monkeypatch.setattr(index, "_client", lambda run_id: Dummy())
    r = api.post("/api/py/labels", json={"geometry": g, "frames": {str(f): url for f in g["label_frames"]}})
    out = r.json()
    assert sign.token_ok("labels", out["labels_token"])["models"] == ["muse-spark-1.3"]
    assert r.status_code == 200 and out["attempts"] == 2 and out["checks"]["ok"]
    assert calls[0] is None and calls[1] is None and calls[2] and calls[3]
    assert all(("box" in h or "increase" in h or "disagree" in h) for h in calls[2:])
    assert not any(t in (calls[2] or "") for t in good)  # track ids never reach the prompt


def test_live_run_needs_the_users_anchor_confirmation():
    m = {"d_m": 0.12, "u_abs_m": 0.0005, "n_frames": 32, "n_kept": 32}
    lab = {"checks": OK_LABELS["checks"]}  # no confirmation sent
    live = api.post("/api/py/survey", json={"mode": "barge", "measure": seal(m, lab), "labels": lab}).json()["certificate"]
    rec = api.post("/api/py/survey", json={"mode": "barge", "measure": seal(m, lab), "labels": lab,
                                           "run_mode": "RECORDED"}).json()["certificate"]
    assert live["reason"] == "NO_ANCHOR" and rec["decision"] == "ISSUE"


def test_typed_labels_must_pass_the_checks():
    m = {"d_m": 0.12, "u_abs_m": 0.0005, "n_frames": 32, "n_kept": 32}
    bad = {"typed": True, "checks": {**OK_LABELS["checks"], "monotone": False, "ok": False}}
    c = api.post("/api/py/survey", json={"mode": "barge", "measure": seal(m, bad), "labels": bad}).json()["certificate"]
    assert (c["decision"], c["reason"]) == ("REFUSE", "LABEL_FAIL") and "d_m" not in c["draft"]
    good = {"typed": True, "checks": OK_LABELS["checks"]}
    c = api.post("/api/py/survey", json={"mode": "barge", "measure": seal(m, good), "labels": good}).json()["certificate"]
    assert c["decision"] == "ISSUE_WITH_WARNING" and [w["code"] for w in c["warnings"]] == ["LABELS_TYPED"]


def test_bad_labels_request_is_a_400():
    assert api.post("/api/py/labels", json={"frames": {}}).status_code == 400


def test_booklet_param_is_an_allowlist_not_a_path():
    for path in ("/api/py/program?booklet=../../api", "/api/py/program?booklet=nope"):
        r = api.get(path)
        assert r.status_code == 404 and r.json()["reason"] == "NO_BOOKLET"
    r = api.post("/api/py/selftest/rerun?booklet=..%2F..")
    assert r.status_code == 404
    r = api.post("/api/py/survey", json={"mode": "ship", "booklet": "../x", "survey": {}, "booklet_info": {}})
    assert r.status_code == 404 and r.json()["reason"] == "NO_BOOKLET"


def test_sandbox_endpoints_are_rate_limited(monkeypatch):
    monkeypatch.setattr(limits, "FREE_PER_IP_H", 1)
    assert limits.take_free("1.2.3.4") == (True, None)
    r = api.post("/api/py/selftest/rerun")  # testclient ip: first call allowed
    assert r.status_code == 200 and r.json()["selftest"]["verdict"] == "PASS"
    r = api.post("/api/py/selftest/rerun")
    assert r.status_code == 429 and r.json()["reason"] == "RATE"


def test_probes_need_the_judge_code_on_production(monkeypatch):
    monkeypatch.setenv("VERCEL_ENV", "production")
    assert api.get("/api/py/probe/sleep?s=0").status_code == 403
    assert api.get("/api/py/probe/sandbox").status_code == 403
    assert api.get("/api/py/probe/sleep?s=0&code=" + "j" * 32).status_code == 200


def test_forged_or_edited_measurements_are_refused():
    m = {"d_m": 0.12, "u_abs_m": 0.0005, "n_frames": 32, "n_kept": 32}
    c = api.post("/api/py/survey", json={"mode": "barge", "measure": m, "labels": OK_LABELS,
                                         "models": ["sam-3.1"]}).json()["certificate"]
    assert (c["decision"], c["reason"]) == ("REFUSE", "UNSIGNED") and c["inputs"] == "unsigned" and c["models"] == []
    tok = seal(m, OK_LABELS)["token"]
    edited = {**m, "d_m": 0.15, "token": {**tok, "payload": {**tok["payload"], "d_m": 0.15}}}
    c = api.post("/api/py/survey", json={"mode": "barge", "measure": edited, "labels": OK_LABELS}).json()["certificate"]
    assert c["reason"] == "UNSIGNED"
    body_only = {**m, "d_m": 0.15, "token": tok}  # body edited, token intact: the token's numbers win
    c = api.post("/api/py/survey", json={"mode": "barge", "measure": body_only, "labels": OK_LABELS}).json()["certificate"]
    assert c["inputs"] == "signed" and c["draft"]["d_m"] == 0.12
    s = {"drafts": {p: 6.5 for p in ("fore_p", "fore_s", "mid_p", "mid_s", "aft_p", "aft_s")}, "sg": 1.025,
         "sources": {"mid_p": "live", "mid_s": "live"}}
    c = api.post("/api/py/survey", json={"mode": "ship", "survey": s, "booklet_info": {"id": "trieste"}}).json()
    assert c["certificate"]["reason"] == "UNSIGNED"


def test_edited_geometry_is_refused_before_any_model_call():
    g = _geom()
    g["frames"][0]["tokens"][0]["bottom"] = 1.0 if g["frames"][0]["tokens"] else None
    r = api.post("/api/py/labels", json={"geometry": g, "typed": {"x": "8"}})
    assert r.status_code == 400 and r.json()["reason"] == "UNSIGNED"
    g = _geom()
    r = api.post("/api/py/labels", json={"geometry": g, "typed": labelled(g)}).json()
    d = api.post("/api/py/draft", json={"geometry": g, "drafts": r["drafts"]}).json()  # no labels token
    assert "token" not in d["result"]


def test_malformed_bodies_are_400_not_500():
    assert api.post("/api/py/draft", json={}).status_code == 400
    assert api.post("/api/py/survey", json={"mode": "ship", "survey": {"drafts": {}}, "booklet_info": {}}).status_code == 400
