from fastapi.testclient import TestClient

from api.index import app

c = TestClient(app)


def test_health_reports_booleans_only(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "sk-secret-value")
    r = c.get("/api/py/health").json()
    assert r["ok"] and r["key_present"] is True
    assert "sk-secret-value" not in str(r)
    assert r["models"] == ["sam-3.1", "muse-spark-1.3", "muse-wonder-1.0"]


def test_sandbox_probe_runs():
    r = c.get("/api/py/probe/sandbox").json()
    assert r["launch_ok"] and r["cpu_limit_kills"][0] and r["audit_hook_blocks_open"][0]
