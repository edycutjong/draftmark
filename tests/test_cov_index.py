import base64
import io
import pathlib
import time
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from api.index import app
from api._core import marks, pipeline, sign, meta
from test_pipeline import clip


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "test-not-a-key")
    monkeypatch.setenv("JUDGE_CODE", "j" * 32)
    yield


def test_health_endpoint_basic():
    """Test health endpoint for lines 45-55."""
    c = TestClient(app)
    
    with patch('api.index.meta.key_present', return_value=True):
        with patch('api.index.limits.budget_reason', return_value=""):
            r = c.get("/api/py/health").json()
            assert r["ok"] is True
            assert r["key_present"] is True
            assert r["models"] == ["sam-3.1", "muse-spark-1.3", "muse-wonder-1.0"]
            assert r["version"] == "0.3.0-p1d"
            assert r["live_mode"] == "on"


def test_health_without_key():
    """Test health endpoint when key is not present for line 90."""
    c = TestClient(app)
    
    with patch('api.index.meta.key_present', return_value=False):
        r = c.get("/api/py/health").json()
        assert r["key_present"] is False


def test_health_budget_limit():
    """Test health endpoint with budget limit for line 53."""
    c = TestClient(app)
    
    with patch('api.index.meta.key_present', return_value=True):
        with patch('api.index.limits.budget_reason', return_value="Budget exceeded"):
            r = c.get("/api/py/health").json()
            assert r["budget"] == "Budget exceeded"


def test_health_fixtures():
    """Test health endpoint with fixtures for line 54."""
    c = TestClient(app)
    
    with patch('api.index.meta.key_present', return_value=True):
        with patch('api.index.limits.budget_reason', return_value=""):
            with patch('api.index._clips', return_value=[{"id": "clip1"}, {"id": "clip2"}]):
                r = c.get("/api/py/health").json()
                assert r["fixtures"] == ["clip1", "clip2"]


def test_ip_extraction_with_forwarded_for():
    """Test _ip function for line 66-67."""
    from api.index import _ip
    
    # Create a mock request with x-forwarded-for header
    class MockRequest:
        def __init__(self):
            self.client = Mock()
            self.client.host = "original"
    
    req = MockRequest()
    req.headers = {"x-forwarded-for": "192.168.1.100, 10.0.0.1"}
    
    result = _ip(req)
    assert result == "192.168.1.100"


def test_ip_extraction_without_forwarded_for():
    """Test _ip function for line 66-67 when no x-forwarded-for."""
    from api.index import _ip
    
    class MockRequest:
        def __init__(self):
            self.client = Mock()
            self.client.host = "client.host"
    
    req = MockRequest()
    req.headers = {}
    
    result = _ip(req)
    assert result == "client.host"


def test_client_creation(monkeypatch):
    """Test _client function for lines 70-72."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    from api.index import _client
    
    # Test client creation with run_id
    client = _client("test-run-id")
    assert client.run_id == "test-run-id"
    assert client.ledger is None
    assert client.enforce_cap is False
    assert client.timeout == 120.0
    assert client.key == "test_key"


def test_client_creation_default(monkeypatch):
    """Test _client function with default parameters."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    from api.index import _client
    
    # _client requires run_id as first parameter
    client = _client("")
    assert client.run_id == ""
    assert client.ledger is None
    assert client.enforce_cap is False
    assert client.timeout == 120.0
    assert client.key == "test_key"


def test_meta_fail_budget_error():
    """Test _meta_fail function for lines 75-82."""
    from api.index import _meta_fail
    from api._core import meta
    
    # Test BudgetError - looking at index.py line 77, it returns 503
    budget_error = meta.BudgetError("Budget error")
    with patch('api.index.limits.trip_budget') as mock_trip:
        mock_trip.return_value = None
        result = _meta_fail(budget_error)
        assert result.status_code == 503
        body = result.body.decode() if isinstance(result.body, bytes) else result.body
        assert "BUDGET" in body


def test_meta_fail_meta_error():
    """Test _meta_fail function for lines 79-82."""
    from api.index import _meta_fail
    from api._core import meta
    
    # Test MetaError
    meta_error = meta.MetaError(500, "Server error")
    result = _meta_fail(meta_error)
    assert result.status_code == 502
    body = result.body.decode() if isinstance(result.body, bytes) else result.body
    assert "UPSTREAM" in body


def test_meta_fail_other_error():
    """Test _meta_fail function for line 82."""
    from api.index import _meta_fail
    
    # Test other error
    other_error = ValueError("Some other error")
    result = _meta_fail(other_error)
    assert result.status_code == 502
    body = result.body.decode() if isinstance(result.body, bytes) else result.body
    assert "UPSTREAM" in body


def test_gate_no_key():
    """Test _gate function for line 91."""
    from api.index import _gate
    
    class MockRequest:
        headers = {}
    
    req = MockRequest()
    
    # Test when key is not present
    with patch('api.index.meta.key_present', return_value=False):
        result = _gate(req, False, None, "test")
        assert result.status_code == 503
        body = result.body.decode() if isinstance(result.body, bytes) else result.body
        assert "BUDGET" in body
        assert "no API key" in body


def test_gate_budget():
    """Test _gate function for line 87-89."""
    from api.index import _gate
    
    class MockRequest:
        headers = {}
    
    req = MockRequest()
    
    # Test when budget reason is not empty
    with patch('api.index.meta.key_present', return_value=True):
        with patch('api.index.limits.budget_reason', return_value="Budget exceeded"):
            result = _gate(req, False, None, "test")
            assert result.status_code == 503
            body = result.body.decode() if isinstance(result.body, bytes) else result.body
            assert "BUDGET" in body
            assert "Budget exceeded" in body


def test_gate_judge_code():
    """Test _gate function for line 92-93."""
    from api.index import _gate
    
    class MockRequest:
        headers = {}
    
    req = MockRequest()
    
    # Test when judge code is invalid
    with patch('api.index.meta.key_present', return_value=True):
        with patch('api.index.limits.budget_reason', return_value=""):
            with patch('api.index.limits.judge_ok', return_value=False):
                result = _gate(req, True, "invalid_code", "test")
                assert result.status_code == 403
                body = result.body.decode() if isinstance(result.body, bytes) else result.body
                assert "JUDGE_CODE" in body
                assert "judge code" in body


def test_gate_rate_limited():
    """Test _gate function for line 96."""
    from api.index import _gate

    class MockRequest:
        headers = {}
        client = None

    req = MockRequest()
    with patch("api.index.meta.key_present", return_value=True), \
         patch("api.index.limits.budget_reason", return_value=""), \
         patch("api.index.limits.take", return_value=(False, "Rate limit exceeded")):
        res = _gate(req, False, None, "test")
        assert res.status_code == 429
        body = res.body.decode() if isinstance(res.body, bytes) else res.body
        assert "RATE" in body
        assert "Rate limit exceeded" in body


def test_measure_invalid_scale():
    """Test measure endpoint for line 115."""
    c = TestClient(app)
    payload = {
        "upload": "data:video/mp4;base64," + base64.b64encode(b"0" * 20).decode(),
        "fps": 6,
        "frames": 10,
        "scale": 9.99,
        "judge_code": "j" * 32,
    }
    with patch("api.index.meta.key_present", return_value=True), \
         patch("api.index.limits.budget_reason", return_value=""), \
         patch("api.index.limits.judge_ok", return_value=True):
        r = c.post("/api/py/measure", json=payload)
        assert r.status_code == 400
        assert r.json()["reason"] == "PAYLOAD"
        assert "scale must be one of" in r.json()["detail"]


def test_measure_fixture_success():
    """Test measure endpoint for lines 127, 132-156."""
    c = TestClient(app)
    data_dir = pathlib.Path(__file__).parent / "data"
    num_txt = (data_dir / "sam_video_3frames.txt").read_text()
    wat_txt = (data_dir / "sam_water_3frames.txt").read_text()

    clip_info = [{
        "id": "fix_test",
        "file": "/clips/fix_test.mp4",
        "frames": 3,
        "fps": 5.0,
        "scale": 1.0,
        "source": "fixture",
        "label": "Test Clip",
        "crop": None,
    }]

    mock_cl = Mock()
    mock_cl.rows = []
    mock_cl.sam.side_effect = [
        {"id": "r1", "output": [{"content": [{"type": "output_text", "text": num_txt}]}]},
        {"id": "r2", "output": [{"content": [{"type": "output_text", "text": wat_txt}]}]},
    ]

    with patch("api.index._clips", return_value=clip_info), \
         patch("api.index._client", return_value=mock_cl), \
         patch("pathlib.Path.read_bytes", return_value=b"fake-mp4-data"), \
         patch("api.index.meta.key_present", return_value=True), \
         patch("api.index.limits.budget_reason", return_value=""):
        r = c.post("/api/py/measure", json={"fixture": "fix_test"})
        assert r.status_code == 200
        res = r.json()
        assert res["ok"] is True
        assert res["clip"]["id"] == "fix_test"
        assert res["geometry"]["fps"] == 5.0
        assert sign.geometry_ok(res["geometry"]) is True


def test_measure_sam_exception():
    """Test measure endpoint for lines 139-140."""
    c = TestClient(app)
    clip_info = [{
        "id": "fix_test",
        "file": "/clips/fix_test.mp4",
        "frames": 3,
        "fps": 5.0,
        "scale": 1.0,
        "source": "fixture",
    }]
    mock_cl = Mock()
    mock_cl.sam.side_effect = meta.MetaError(500, "SAM service down")
    with patch("api.index._clips", return_value=clip_info), \
         patch("api.index._client", return_value=mock_cl), \
         patch("pathlib.Path.read_bytes", return_value=b"fake-mp4-data"), \
         patch("api.index.meta.key_present", return_value=True), \
         patch("api.index.limits.budget_reason", return_value=""):
        r = c.post("/api/py/measure", json={"fixture": "fix_test"})
        assert r.status_code == 502
        assert r.json()["reason"] == "UPSTREAM"


def test_img_helper_errors():
    """Test _img helper for lines 164, 167, 170-171, 173."""
    from api.index import _img

    # 164: not jpeg/png
    with pytest.raises(ValueError, match="frames must be JPEG/PNG data URLs"):
        _img("data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")

    # 167: > 2 MB
    big_b64 = "data:image/jpeg;base64," + base64.b64encode(b"a" * (2 * 1024 * 1024 + 10)).decode()
    with pytest.raises(ValueError, match="frame image > 2 MB"):
        _img(big_b64)

    # 170-171: unreadable frame image
    corrupt_b64 = "data:image/jpeg;base64," + base64.b64encode(b"not-an-image-data").decode()
    with pytest.raises(ValueError, match="unreadable frame image"):
        _img(corrupt_b64)

    # 173: > 4 MP
    huge_img = Image.new("RGB", (2500, 2000), color="blue")
    buf = io.BytesIO()
    huge_img.save(buf, format="JPEG")
    huge_b64 = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    with pytest.raises(ValueError, match="frame image > 4 MP"):
        _img(huge_b64)


def _geom():
    num, wat = clip()
    return sign.seal_geometry(pipeline.geometry_from_objects(num, wat, 12, 6.0, marks.SHIP))


def _sample_jpeg(w=10, h=10):
    im = Image.new("RGB", (w, h), color="white")
    buf = io.BytesIO()
    im.save(buf, format="JPEG")
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def test_labels_bad_payload_and_rebuild():
    """Test labels endpoint for lines 193-194."""
    c = TestClient(app)
    # sealed geometry with corrupted frames type causing AttributeError in rebuild
    fake_geom = sign.seal_geometry({"iat": int(time.time()), "frames": "invalid"})
    r = c.post("/api/py/labels", json={"geometry": fake_geom})
    assert r.status_code == 400
    assert r.json()["reason"] == "PAYLOAD"
    assert "bad labels request: TypeError" in r.json()["detail"]

    # invalid non-int frame key causing ValueError in [int(k) for k in frames]
    g = _geom()
    r = c.post("/api/py/labels", json={"geometry": g, "frames": {"bad_key": _sample_jpeg()}})
    assert r.status_code == 400
    assert r.json()["reason"] == "PAYLOAD"
    assert "bad labels request: ValueError" in r.json()["detail"]


def test_labels_typed_rate_and_frame_errors():
    """Test labels endpoint for lines 203, 205, 208."""
    c = TestClient(app)
    g = _geom()

    # 203: typed rate limit
    with patch("api.index.limits.take_free", return_value=(False, "Rate free limit")):
        r = c.post("/api/py/labels", json={"geometry": g, "typed": {"1": "10M"}})
        assert r.status_code == 429
        assert r.json()["reason"] == "RATE"

    # 205: body.get("frame") is None and not lf
    g_no_lf = dict(g)
    g_no_lf["label_frames"] = []
    g_no_lf = sign.seal_geometry(g_no_lf)
    with patch("api.index.limits.take_free", return_value=(True, "")):
        r = c.post("/api/py/labels", json={"geometry": g_no_lf, "typed": {"1": "10M"}})
        assert r.status_code == 400
        assert r.json()["reason"] == "LABEL_FRAMES"
        assert "no label frame in this geometry" in r.json()["detail"]

    # 208: f1 not in toks
    with patch("api.index.limits.take_free", return_value=(True, "")):
        r = c.post("/api/py/labels", json={"geometry": g, "typed": {"1": "10M"}, "frame": 9999})
        assert r.status_code == 400
        assert r.json()["reason"] == "LABEL_FRAMES"
        assert "frame not in geometry" in r.json()["detail"]


def test_labels_image_error_and_gate_and_meta_fail():
    """Test labels endpoint for lines 217-219, 224, 245-246."""
    c = TestClient(app)
    g = _geom()
    lf = g["label_frames"]

    # 217-219: ValueError from _img handled with _IMG_ERRORS ("unreadable frame image")
    unreadable_b64 = "data:image/jpeg;base64," + base64.b64encode(b"not-an-image").decode()
    bad_frames = {str(lf[0]): unreadable_b64, str(lf[1]): _sample_jpeg()}
    r = c.post("/api/py/labels", json={"geometry": g, "frames": bad_frames})
    assert r.status_code == 400
    assert r.json()["reason"] == "PAYLOAD"
    assert r.json()["detail"] == "unreadable frame image"

    # 217-219: generic bad frame image (e.g. invalid base64 padding)
    corrupt_b64_frames = {str(lf[0]): "data:image/jpeg;base64,not-valid-b64", str(lf[1]): _sample_jpeg()}
    r2 = c.post("/api/py/labels", json={"geometry": g, "frames": corrupt_b64_frames})
    assert r2.status_code == 400
    assert r2.json()["reason"] == "PAYLOAD"
    assert r2.json()["detail"] == "bad frame image"

    # 224: blocked by _gate
    valid_frames = {str(f): _sample_jpeg() for f in lf}
    with patch("api.index.meta.key_present", return_value=False):
        r = c.post("/api/py/labels", json={"geometry": g, "frames": valid_frames})
        assert r.status_code == 503
        assert r.json()["reason"] == "BUDGET"

    # 245-246: Exception in spark reading map
    with patch("api.index.meta.key_present", return_value=True), \
         patch("api.index.limits.budget_reason", return_value=""), \
         patch("api.index.limits.take", return_value=(True, "")), \
         patch("api.index.labels.read", side_effect=meta.MetaError(500, "Spark failed")):
        r = c.post("/api/py/labels", json={"geometry": g, "frames": valid_frames})
        assert r.status_code == 502
        assert r.json()["reason"] == "UPSTREAM"


def test_draft_mismatched_sig():
    """Test draft endpoint for line 285."""
    c = TestClient(app)
    g1 = _geom()
    g2 = dict(_geom())
    g2["scale"] = 0.2
    g2 = sign.seal_geometry(g2)
    mismatched_token = sign.token("labels", {
        "geometry_sig": g2["sig"],
        "drafts": {"1": 12.0},
        "typed": True,
        "checks": {},
        "models": []
    })
    r = c.post("/api/py/draft", json={
        "geometry": g1,
        "drafts": {"1": 12.0},
        "labels_token": mismatched_token,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "token" not in data["result"]


def test_survey_rate_limit():
    """Test survey endpoint for line 331."""
    c = TestClient(app)
    with patch("api.index.limits.take_free", return_value=(False, "Survey limit exceeded")):
        r = c.post("/api/py/survey", json={"mode": "ship", "booklet": "trieste"})
        assert r.status_code == 429
        assert r.json()["reason"] == "RATE"
        assert "Survey limit exceeded" in r.json()["detail"]

