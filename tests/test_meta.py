import pytest

from api.core import meta


def test_estimate_usd():
    u = {"input_tokens": 1_000_000, "output_tokens": 100_000, "input_tokens_details": {"cached_tokens": 500_000}}
    assert meta.estimate_usd(meta.WONDER, u) == pytest.approx(0.5 * 4 + 0.5 * 0.2 + 0.1 * 20)
    assert meta.estimate_usd(meta.SAM, None, frames=60) == pytest.approx(0.012)


def test_ledger_roundtrip_and_cap(tmp_path, monkeypatch):
    led = tmp_path / "usage.md"
    row = meta.UsageRow(ts="t", model=meta.SPARK, feature="f", latency_ms=1, est_usd=12.5)
    meta.append_ledger(row, led)
    meta.append_ledger(row, led)
    assert meta.ledger_total(led) == 25.0
    monkeypatch.setenv("MODEL_API_KEY", "k")
    monkeypatch.setattr(meta, "DEV_CAP_USD", 20.0)
    c = meta.Client(ledger=led)
    with pytest.raises(meta.BudgetError):
        c.request("POST", "/responses", {"model": meta.SPARK})


def test_only_standard_models(monkeypatch, tmp_path):
    monkeypatch.setenv("MODEL_API_KEY", "k")
    c = meta.Client(ledger=tmp_path / "u.md")
    with pytest.raises(ValueError):
        c.request("POST", "/responses", {"model": "muse-spark-1.3-contributor"})


def test_redact(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "secret123")
    assert "secret123" not in meta.redact("x secret123 y")
