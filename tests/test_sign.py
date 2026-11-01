import pathlib
from api._core import sign


def test_sign_norm_other_type():
    # 35: _norm returns str(x) for non-dict/list/primitive types
    p = pathlib.Path("/dummy/path")
    assert sign._norm(p) == "/dummy/path"


def test_sign_mac_no_key(monkeypatch):
    # 41: _mac returns empty string when key is empty
    monkeypatch.delenv("DRAFTMARK_SIGNING_KEY", raising=False)
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    assert sign._key() == b""
    assert sign._mac("test", {}) == ""


def test_sign_roundtrip(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "secret-test-key")
    # seal_geometry and geometry_ok
    geom = sign.seal_geometry({"frames": 10, "scale": 1.0, "sub": [1, 2, {"a": True, "b": None}]})
    assert sign.geometry_ok(geom) is True
    assert sign.geometry_ok({"invalid": "sig"}) is False

    # token and token_ok
    tok = sign.token("test_kind", {"val": 42.0})
    assert sign.token_ok("test_kind", tok) == tok["payload"]
    assert sign.token_ok("wrong_kind", tok) is None
    assert sign.token_ok("test_kind", {"corrupt": True}) is None

