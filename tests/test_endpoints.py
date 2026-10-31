import base64

import pytest
from fastapi.testclient import TestClient
from test_pipeline import clip, labelled

from api import index
from api._core import limits, marks, pipeline

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
    r = api.post("/api/py/measure", json={"upload": mp4(3 * 1024 * 1024 + 3)})
    assert r.status_code == 413 and r.json()["reason"] == "PAYLOAD"
    r = api.post("/api/py/measure", json={"upload": mp4(), "fps": 12, "frames": 30})
    assert r.status_code == 413
    r = api.post("/api/py/measure", json={"upload": mp4(), "judge_code": "wrong"})
    assert r.status_code == 403 and r.json()["reason"] == "JUDGE_CODE"


def test_kill_switch_and_unknown_fixture(monkeypatch):
    assert api.post("/api/py/measure", json={"fixture": "nope"}).json()["reason"] == "NO_FIXTURE"
    monkeypatch.setenv("LIVE_MODE", "off")
    r = api.post("/api/py/measure", json={"upload": mp4(), "judge_code": "j" * 32})
    assert r.status_code == 503 and r.json()["reason"] == "BUDGET"
    assert api.get("/api/py/health").json()["budget"] == "LIVE_MODE=off"


def test_budget_trip_fails_closed():
    limits.trip_budget("HTTP 402")
    r = api.post("/api/py/measure", json={"upload": mp4(), "judge_code": "j" * 32})
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
    return pipeline.geometry_from_objects(num, wat, 12, 6.0, marks.SHIP)


def test_typed_labels_then_draft():
    g = _geom()
    r = api.post("/api/py/labels", json={"geometry": g, "typed": labelled(g)}).json()
    assert r["typed"] and r["checks"]["ok"] and r["usage"] == []
    d = api.post("/api/py/draft", json={"geometry": g, "drafts": r["drafts"]}).json()
    assert d["result"]["n_kept"] == 12 and 12.6 < d["result"]["d_m"] < 12.8


def test_survey_ship_out_of_table_refuses_without_cargo():
    s = {"drafts": {p: 12.73 for p in ("fore_p", "fore_s", "mid_p", "mid_s", "aft_p", "aft_s")}, "sg": 1.025}
    c = api.post("/api/py/survey", json={"mode": "ship", "survey": s, "measure": {"n_frames": 12, "n_kept": 12}})
    cert = c.json()["certificate"]
    assert (cert["decision"], cert["reason"]) == ("REFUSE", "OUT_OF_TABLE") and "cargo" not in cert["survey"]
    assert cert["footer"].startswith("Prototype")


def test_survey_barge_issue_and_what_if():
    m = {"d_m": 0.12, "u_abs_m": 0.0005, "n_frames": 32, "n_kept": 32}
    c = api.post("/api/py/survey", json={"mode": "barge", "measure": m}).json()["certificate"]
    assert c["decision"] == "ISSUE" and c["program_author"] == "analytic" and c["proof"] == "measurement"
    c = api.post("/api/py/survey", json={"mode": "barge", "measure": m, "what_if": {"rho_kg_m3": 1000}}).json()
    assert c["certificate"]["decision"] == "NOT_SCORED"


def test_selftest_rerun_and_program():
    st = api.post("/api/py/selftest/rerun").json()["selftest"]
    assert st["verdict"] == "PASS" and st["pass_count"] == 22
    p = api.get("/api/py/program").json()
    assert p["meta"]["program_author"] == "muse-wonder-1.0" and "def survey" in p["code"]
