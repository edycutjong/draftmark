import os
import pytest
from unittest.mock import Mock, patch

from api._core import meta


def test_meta_error_status():
    """Test MetaError status handling for lines 45-46."""
    error = meta.MetaError(500, "Internal error with longer text that exceeds 300 chars limit")
    assert error.status == 500
    assert "HTTP 500: Internal error" in str(error)


def test_load_local_env(tmp_path, monkeypatch):
    """Test load_local_env for lines 66-72."""
    env_file = tmp_path / "meta.env"
    env_file.write_text("""MODEL_API_KEY=env_key_value
EXPORTED_VAR=exported_value
invalid_line_without_equal
export ANOTHER_VAR=another_value
""")
    
    # Remove MODEL_API_KEY from environment before calling load_local_env
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    meta.load_local_env(str(env_file))
    
    assert os.environ.get("MODEL_API_KEY") == "env_key_value"
    assert os.environ.get("EXPORTED_VAR") == "exported_value"
    assert os.environ.get("ANOTHER_VAR") == "another_value"


def test_data_url(tmp_path):
    """Test data_url function for lines 85-86."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    result = meta.data_url(test_file)
    assert result.startswith("data:text/plain;base64,")
    assert "dGVzdCBjb250ZW50" in result


def test_bytes_data_url():
    """Test bytes_data_url function for line 89."""
    test_bytes = b"binary content"
    
    result = meta.bytes_data_url(test_bytes, "application/octet-stream")
    assert result.startswith("data:application/octet-stream;base64,")
    assert "YmluYXJ5IGNvbnRlbnQ" in result


def test_estimate_usd_edge_cases():
    """Test estimate_usd for line 97."""
    # Test with unknown model
    assert meta.estimate_usd("unknown-model", {"input_tokens": 100}) == 0.0
    
    # Test with None usage
    assert meta.estimate_usd(meta.WONDER, None) == 0.0
    
    # Test with SAM model and no frames
    assert meta.estimate_usd(meta.SAM, {"input_tokens": 100}) == 0.0


def test_ledger_total_nonexistent(tmp_path):
    """Test ledger_total for line 107."""
    ledger_path = tmp_path / "nonexistent.md"
    assert meta.ledger_total(ledger_path) == 0.0


def test_append_ledger_new_file(tmp_path):
    """Test append_ledger for line 123."""
    ledger_path = tmp_path / "test_ledger.md"
    row = meta.UsageRow(
        ts="2023-01-01 12:00",
        model=meta.WONDER,
        feature="test",
        latency_ms=100,
        est_usd=0.5,
        tokens_in=1000,
        tokens_out=500,
        tokens_cached=200,
        frames=1
    )
    
    meta.append_ledger(row, ledger_path)
    
    assert ledger_path.exists()
    content = ledger_path.read_text()
    assert "Meta API usage ledger" in content
    assert "test" in content
    assert "0.5000" in content


def test_client_init_without_key(monkeypatch):
    """Test Client initialization without API key for line 147."""
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    
    with pytest.raises(RuntimeError, match="MODEL_API_KEY not set"):
        meta.Client()


def test_client_with_custom_key(tmp_path):
    """Test Client with custom key for line 143-148."""
    ledger_path = tmp_path / "test.md"
    
    client = meta.Client(key="custom_key", ledger=ledger_path)
    assert client.key == "custom_key"
    assert client.ledger == ledger_path


def test_check_cap_raises_for_high_usage(tmp_path, monkeypatch):
    """Test _check_cap raises BudgetError for high usage for line 159."""
    ledger_path = tmp_path / "high_usage.md"
    
    # Create a ledger with usage exceeding cap
    ledger_path.write_text(
        "# Meta API usage ledger\n\n" + meta.LEDGER_HEADER +
        "| 2023-01-01 12:00 | run1 | muse-wonder-1.0 | test |  | 35.0 | 100 |  |\n"
    )
    
    monkeypatch.setattr(meta, "DEV_CAP_USD", 30.0)
    client = meta.Client(ledger=ledger_path)
    
    with pytest.raises(meta.BudgetError):
        client._check_cap()


def test_request_rate_limiting(tmp_path, monkeypatch):
    """Test request rate limiting for lines 168-188."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    
    ledger_path = tmp_path / "test.md"
    client = meta.Client(key="test_key", ledger=ledger_path)
    
    # Mock the httpx request to return a rate limit error
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.text = "rate limit exceeded"
    mock_response.headers = {"retry-after": "0.001"}
    
    with patch.object(client._http, 'request', return_value=mock_response):
        with patch('time.sleep') as mock_sleep:
            with pytest.raises(meta.MetaError):
                client.request("POST", "/responses", {"model": meta.WONDER})
            # Verify sleep was called for the retry
            assert mock_sleep.called


def test_request_transport_error_retry(tmp_path, monkeypatch):
    """Test request retry on transport error for lines 173-176."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    
    ledger_path = tmp_path / "test.md"
    client = meta.Client(key="test_key", ledger=ledger_path)
    
    import httpx
    
    # First two calls raise TransportError, third succeeds
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "resp-123", "model": meta.WONDER, "usage": {"input_tokens": 100, "output_tokens": 50}}
    
    with patch.object(client._http, 'request', side_effect=[httpx.TransportError("timeout"), httpx.TransportError("reset"), mock_response]):
        with patch('time.sleep') as mock_sleep:
            resp, ms = client.request("POST", "/responses", {"model": meta.WONDER})
            assert resp["id"] == "resp-123"
            assert mock_sleep.call_count == 2


def test_request_budget_error_402(tmp_path, monkeypatch):
    """Test request raises BudgetError on 402 for line 181-182."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    
    ledger_path = tmp_path / "test.md"
    client = meta.Client(key="test_key", ledger=ledger_path)
    
    mock_response = Mock()
    mock_response.status_code = 402
    mock_response.text = "billing limit exceeded"
    mock_response.headers = {}
    
    with patch.object(client._http, 'request', return_value=mock_response):
        with pytest.raises(meta.BudgetError):
            client.request("POST", "/responses", {"model": meta.WONDER})


def test_request_budget_error_429_billing(tmp_path, monkeypatch):
    """Test request raises BudgetError on 429 with billing text for line 181-182."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    
    ledger_path = tmp_path / "test.md"
    client = meta.Client(key="test_key", ledger=ledger_path)
    
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.text = "quota exceeded billing limit"
    mock_response.headers = {}
    
    with patch.object(client._http, 'request', return_value=mock_response):
        with pytest.raises(meta.BudgetError):
            client.request("POST", "/responses", {"model": meta.WONDER})


def test_request_500_retry_then_fail(tmp_path, monkeypatch):
    """Test request retries on 500 then fails for lines 183-187."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    
    ledger_path = tmp_path / "test.md"
    client = meta.Client(key="test_key", ledger=ledger_path)
    
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "internal server error"
    mock_response.headers = {}
    
    with patch.object(client._http, 'request', return_value=mock_response):
        with patch('time.sleep') as mock_sleep:
            with pytest.raises(meta.MetaError):
                client.request("POST", "/responses", {"model": meta.WONDER}, retries=2)
            assert mock_sleep.call_count == 2  # retries=2 means 2 retries after initial failure


def test_sam_method(tmp_path, monkeypatch):
    """Test sam method for lines 233-237."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    
    client = meta.Client(key="test_key", ledger=tmp_path / "test.md")
    
    # Mock the responses method to return a valid response
    mock_response = {
        "id": "test-response-id",
        "status": "completed",
        "model": meta.SAM,
        "usage": {"input_tokens": 100, "output_tokens": 50}
    }
    
    with patch.object(client, 'responses', return_value=mock_response):
        result = client.sam("test concept", "https://example.com/test.mp4", video=True, frames=10, feature="test")
        assert result == mock_response


def test_close_client(tmp_path):
    """Test close method for line 241."""
    client = meta.Client(key="test_key", ledger=tmp_path / "test.md")
    
    with patch.object(client._http, 'close'):
        client.close()


def test_output_text():
    """Test output_text function for line 244."""
    resp = {
        "output": [
            {"content": [{"type": "output_text", "text": "Hello"}]},
            {"content": [{"type": "output_text", "text": "World"}]},
            {"content": [{"type": "other", "data": "ignored"}]}
        ]
    }
    
    result = meta.output_text(resp)
    assert result == "HelloWorld"


def test_function_calls():
    """Test function_calls function for line 255."""
    resp = {
        "output": [
            {"type": "function_call", "name": "test_func", "arguments": "{}"},
            {"type": "output_text", "text": "text"},
            {"type": "function_call", "name": "another_func", "arguments": "{}"}
        ]
    }
    
    result = meta.function_calls(resp)
    assert len(result) == 2
    assert result[0]["name"] == "test_func"
    assert result[1]["name"] == "another_func"


def test_as_dict():
    """Test as_dict function for line 259."""
    row = meta.UsageRow(
        ts="2023-01-01 12:00",
        model=meta.WONDER,
        feature="test",
        latency_ms=100,
        est_usd=0.5,
        tokens_in=1000,
        tokens_cached=200,
        tokens_out=500,
        frames=1,
        response_id="test-id",
        run_id="run1",
        extra={"key": "value"}
    )
    
    result = meta.as_dict(row)
    assert result["ts"] == "2023-01-01 12:00"
    assert result["model"] == meta.WONDER
    assert result["extra"] == {"key": "value"}


def test_load_local_env_early_return_when_key_set(tmp_path, monkeypatch):
    """Test load_local_env early return for line 68 when key already set."""
    monkeypatch.setenv("MODEL_API_KEY", "already_set")
    env_file = tmp_path / "meta.env"
    env_file.write_text("MODEL_API_KEY=should_not_overwrite\n")
    
    meta.load_local_env(str(env_file))
    
    # Key should not be overwritten
    assert os.environ.get("MODEL_API_KEY") == "already_set"


def test_load_local_env_early_return_when_file_missing(tmp_path, monkeypatch):
    """Test load_local_env early return for line 68 when file doesn't exist."""
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    nonexistent = tmp_path / "nonexistent.env"
    
    meta.load_local_env(str(nonexistent))
    
    # Should not raise and key should not be set
    assert os.environ.get("MODEL_API_KEY") is None


def test_request_transport_error_all_retries_exhausted(tmp_path, monkeypatch):
    """Test request raises MetaError after all retries exhausted for line 188."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    
    ledger_path = tmp_path / "test.md"
    client = meta.Client(key="test_key", ledger=ledger_path)
    
    import httpx
    
    # All retries raise TransportError
    with patch.object(client._http, 'request', side_effect=httpx.TransportError("persistent failure")):
        with patch('time.sleep'):
            with pytest.raises(meta.MetaError, match="transport"):
                client.request("POST", "/responses", {"model": meta.WONDER}, retries=2)


def test_log_method(tmp_path, monkeypatch):
    """Test _log method for lines 192-203."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    
    ledger_path = tmp_path / "test.md"
    client = meta.Client(key="test_key", ledger=ledger_path)
    
    resp = {
        "id": "resp-123",
        "model": meta.WONDER,
        "usage": {
            "input_tokens": 1000,
            "output_tokens": 500,
            "input_tokens_details": {"cached_tokens": 200}
        }
    }
    
    row = client._log(meta.WONDER, "test_feature", resp, 150, frames=5, images=2, custom_extra="value")
    
    assert row.model == meta.WONDER
    assert row.feature == "test_feature"
    assert row.latency_ms == 150
    assert row.tokens_in == 1000
    assert row.tokens_out == 500
    assert row.tokens_cached == 200
    assert row.frames == 5  # frames takes precedence over images
    assert row.response_id == "resp-123"
    assert row.run_id == ""
    assert row.extra == {"custom_extra": "value"}
    assert len(client.rows) == 1
    assert ledger_path.exists()


def test_log_method_images_only(tmp_path, monkeypatch):
    """Test _log method with images only (no frames) for line 198."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    
    ledger_path = tmp_path / "test.md"
    client = meta.Client(key="test_key", ledger=ledger_path)
    
    resp = {
        "id": "resp-123",
        "model": meta.SPARK,
        "usage": {"input_tokens": 100, "output_tokens": 50}
    }
    
    row = client._log(meta.SPARK, "test_feature", resp, 100, images=3)
    
    assert row.frames == 3  # uses images when frames is None
    assert row.model == meta.SPARK


def test_responses_method(tmp_path, monkeypatch):
    """Test responses method for lines 208-210."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    
    ledger_path = tmp_path / "test.md"
    client = meta.Client(key="test_key", ledger=ledger_path)
    
    mock_resp = {
        "id": "resp-123",
        "model": meta.WONDER,
        "usage": {"input_tokens": 100, "output_tokens": 50}
    }
    
    with patch.object(client, 'request', return_value=(mock_resp, 100)):
        result = client.responses({"model": meta.WONDER}, "test_feature", frames=5)
        assert result == mock_resp
        assert len(client.rows) == 1


def test_get_response_method(tmp_path, monkeypatch):
    """Test get_response method for lines 212-214."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    
    ledger_path = tmp_path / "test.md"
    client = meta.Client(key="test_key", ledger=ledger_path)
    
    mock_resp = {"id": "resp-123", "status": "completed", "model": meta.WONDER}
    
    with patch.object(client, 'request', return_value=(mock_resp, 50)):
        result = client.get_response("resp-123")
        assert result == mock_resp


def test_poll_completes_successfully(tmp_path, monkeypatch):
    """Test poll method for lines 218-226 when response completes."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    
    client = meta.Client(key="test_key", ledger=tmp_path / "test.md")
    
    # First call returns queued, second returns completed
    responses = [
        {"status": "queued", "model": meta.WONDER},
        {"status": "completed", "model": meta.WONDER, "id": "resp-123", "usage": {"input_tokens": 100, "output_tokens": 50}}
    ]
    
    with patch.object(client, 'get_response', side_effect=responses):
        with patch('time.sleep') as mock_sleep:
            result = client.poll("resp-123", "test_feature", every=0.001, max_wait=10)
            assert result["status"] == "completed"
            assert result["id"] == "resp-123"
            assert mock_sleep.call_count == 1  # only slept once between checks
            assert len(client.rows) == 1


def test_poll_in_progress_then_completes(tmp_path, monkeypatch):
    """Test poll method with in_progress status for lines 218-226."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    
    client = meta.Client(key="test_key", ledger=tmp_path / "test.md")
    
    responses = [
        {"status": "in_progress", "model": meta.WONDER},
        {"status": "completed", "model": meta.WONDER, "id": "resp-123", "usage": {"input_tokens": 100, "output_tokens": 50}}
    ]
    
    with patch.object(client, 'get_response', side_effect=responses):
        with patch('time.sleep'):
            result = client.poll("resp-123", "test_feature", every=0.001, max_wait=10)
            assert result["status"] == "completed"


def test_poll_model_fallback_to_wonder(tmp_path, monkeypatch):
    """Test poll method falls back to WONDER model for lines 223-225."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    
    client = meta.Client(key="test_key", ledger=tmp_path / "test.md")
    
    # Response has unknown model
    responses = [
        {"status": "queued", "model": meta.WONDER},
        {"status": "completed", "model": "unknown-model", "id": "resp-123", "usage": {"input_tokens": 100, "output_tokens": 50}}
    ]
    
    with patch.object(client, 'get_response', side_effect=responses):
        with patch('time.sleep'):
            result = client.poll("resp-123", "test_feature", every=0.001, max_wait=10)
            assert result["status"] == "completed"
            # The _log should have been called with WONDER as fallback
            assert len(client.rows) == 1
            assert client.rows[0].model == meta.WONDER


def test_poll_sleeps_between_checks(tmp_path, monkeypatch):
    """Test poll method sleeps between checks for line 229."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    
    client = meta.Client(key="test_key", ledger=tmp_path / "test.md")
    
    # Multiple queued responses before completion
    responses = [
        {"status": "queued", "model": meta.WONDER},
        {"status": "queued", "model": meta.WONDER},
        {"status": "completed", "model": meta.WONDER, "id": "resp-123", "usage": {"input_tokens": 100, "output_tokens": 50}}
    ]
    
    with patch.object(client, 'get_response', side_effect=responses):
        with patch('time.sleep') as mock_sleep:
            result = client.poll("resp-123", "test_feature", every=0.001, max_wait=10)
            assert result["status"] == "completed"
            assert mock_sleep.call_count == 2  # slept twice between three checks


def test_poll_timeout_exception(tmp_path, monkeypatch):
    """Test poll method raises MetaError on timeout for line 228."""
    monkeypatch.setenv("MODEL_API_KEY", "test_key")
    
    client = meta.Client(key="test_key", ledger=tmp_path / "test.md")
    
    # Mock get_response to always return queued status
    with patch.object(client, 'get_response', return_value={"status": "queued", "model": meta.WONDER}):
        with patch('time.time', side_effect=[0, 0, 100]):  # First call t0=0, second check t0=0, third check time.time()-t0=100 > max_wait
            with patch('time.sleep'):
                with pytest.raises(meta.MetaError, match="background.*still queued after 1s"):
                    client.poll("resp-123", "test_feature", every=0.001, max_wait=1)
