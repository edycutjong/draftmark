from unittest.mock import Mock
from api._core import cu


def test_host_allowed_localhost():
    """Test host_allowed for localhost for line 40."""
    assert cu.host_allowed("http://127.0.0.1:8765/portal/index.html")
    assert cu.host_allowed("https://localhost:8080/api")


def test_host_allowed_internal():
    """Test host_allowed for internal networks for line 40."""
    assert cu.host_allowed("http://127.0.0.1:8765/portal/index.html")
    assert cu.host_allowed("https://en.wikipedia.org/wiki/Ever_Given")
    assert cu.host_allowed("https://draftmark.edycu.dev/portal")


def test_host_allowed_rejected():
    """Test host_allowed for rejected hosts for lines 44-65."""
    # Direct rejection
    assert not cu.host_allowed("https://example.com/")
    assert not cu.host_allowed("https://evilwikipedia.org/")
    assert not cu.host_allowed("https://draftmark.edycu.dev.attacker.net/")
    
    # Whitelist rejection
    assert not cu.host_allowed("http://evil-internal.com/")


def test_host_allowed_edge_cases():
    """Test host_allowed edge cases for lines 70-112."""
    # Empty port
    assert cu.host_allowed("https://draftmark.edycu.dev")
    
    # Different ports for allowed hosts
    assert cu.host_allowed("https://draftmark.edycu.dev:443")
    assert cu.host_allowed("http://wikipedia.org:80")
    
    # localhost variations
    assert cu.host_allowed("https://localhost")
    assert cu.host_allowed("http://127.0.0.1")
    
    # subdomain of allowed host
    assert cu.host_allowed("https://portal.draftmark.edycu.dev")
    
    # subdomain of another allowed host
    assert cu.host_allowed("https://en.wikipedia.org/wiki/Example")
    
    # IP addresses (not explicitly allowed)
    assert not cu.host_allowed("https://192.168.1.1:8080")


def test_compare_basic_match():
    """Test compare function for basic matching."""
    cert = {"vessel": "X", "displacement": "17825.8", "cargo": "6581.8", "decision": "ISSUE"}
    ok = cu.compare(cert, {"vessel": "x", "displacement": "17,825.8", "cargo": "6581.80", "decision": "ISSUE"})
    assert ok["ok"]


def test_compare_field_mismatch():
    """Test compare function for field mismatch."""
    cert = {"vessel": "X", "displacement": "17825.8", "cargo": "6581.8", "decision": "ISSUE"}
    bad = cu.compare(cert, {"vessel": "X", "displacement": "17825.8", "cargo": "6582.8", "decision": "ISSUE"})
    assert not bad["ok"] and not bad["fields"]["cargo"]["match"]


def test_compare_missing_fields():
    """Test compare function for missing fields."""
    cert = {"vessel": "X", "displacement": "17825.8", "cargo": "6581.8", "decision": "ISSUE"}
    missing = cu.compare(cert, {"vessel": "X"})
    assert not missing["ok"]


def test_compare_case_insensitive():
    """Test compare function for case insensitive matching."""
    cert = {"vessel": "X", "value": "100"}
    result = cu.compare(cert, {"vessel": "x", "value": "100"})
    assert result["ok"]


def test_compare_special_formats():
    """Test compare function for special value formats."""
    cert = {"vessel": "X", "displacement": "17,825.8", "decimal": "3.14"}
    result = cu.compare(cert, {"vessel": "X", "displacement": "17825.8", "decimal": "3.14"})
    assert result["ok"]


def test_compare_whitespace():
    """Test compare function for whitespace handling."""
    cert = {"value": "100"}
    result = cu.compare(cert, {"value": " 100 "})
    assert result["ok"] is True


def test_shot_helper():
    """Test _shot helper function (line 40)."""
    page = Mock()
    page.screenshot.return_value = b"fake-png-data"
    data_url = cu._shot(page)
    assert data_url.startswith("data:image/png;base64,")
    assert "ZmFrZS1wbmctZGF0YQ==" in data_url


def test_apply_actions():
    """Test _apply function for all action types (lines 44-65)."""
    page = Mock()

    # Click left/right/default
    cu._apply(page, {"type": "click", "x": 10, "y": 20, "button": "right"})
    page.mouse.click.assert_called_with(10, 20, button="right")

    cu._apply(page, {"type": "click", "x": 10, "y": 20, "button": "middle"})
    page.mouse.click.assert_called_with(10, 20, button="middle")

    cu._apply(page, {"type": "click", "x": 10, "y": 20, "button": "invalid_btn"})
    page.mouse.click.assert_called_with(10, 20, button="left")

    # Double click
    cu._apply(page, {"type": "double_click", "x": 15, "y": 25})
    page.mouse.dblclick.assert_called_with(15, 25)

    # Type
    cu._apply(page, {"type": "type", "text": "Draftmark text"})
    page.keyboard.type.assert_called_with("Draftmark text")

    # Keypress
    cu._apply(page, {"type": "keypress", "keys": ["Control", "Shift", "A"]})
    page.keyboard.press.assert_called_with("Control+Shift+A")

    # Scroll
    cu._apply(page, {"type": "scroll", "x": 30, "y": 40, "scroll_x": 2, "scroll_y": -3})
    page.mouse.move.assert_called_with(30, 40)
    page.mouse.wheel.assert_called_with(200, -300)

    # Move
    cu._apply(page, {"type": "move", "x": 50, "y": 60})
    page.mouse.move.assert_called_with(50, 60)

    # Drag
    cu._apply(page, {"type": "drag", "path": [{"x": 1, "y": 2}, {"x": 3, "y": 4}, {"x": 5, "y": 6}]})
    page.mouse.down.assert_called()
    page.mouse.up.assert_called()


def test_cu_run_scenarios(monkeypatch):
    """Test cu.run branches (lines 70-112)."""
    monkeypatch.setattr("time.sleep", lambda s: None)
    page = Mock()
    page.screenshot.return_value = b"png"
    client = Mock()

    # 1. Message response (out.final, no computer_call)
    page.url = "http://127.0.0.1:8765/portal"
    client.responses.return_value = {
        "output": [
            {"type": "message", "content": [{"type": "text", "text": "Task finished successfully"}]}
        ]
    }
    res_final = cu.run(client, page, "task message")
    assert res_final.final == "Task finished successfully"
    assert res_final.steps == []

    # 2. Checks on non-allowlisted host
    page.url = "https://unauthorized.com/test"
    client.responses.return_value = {
        "id": "r1",
        "output": [
            {
                "type": "computer_call",
                "call_id": "c1",
                "actions": [{"type": "move", "x": 1, "y": 2}],
                "pending_safety_checks": [{"code": "C1"}],
            }
        ],
    }
    res_checks = cu.run(client, page, "task safety")
    assert res_checks.stopped == "confirmation requested on non-allowlisted host unauthorized.com"

    # 3. Navigated off allowlist after apply
    page.url = "http://127.0.0.1:8765/portal"
    def navigate_away(*a, **kw):
        page.url = "https://unauthorized.com/navigated"

    page.mouse.move.side_effect = navigate_away
    client.responses.return_value = {
        "id": "r2",
        "output": [
            {
                "type": "computer_call",
                "call_id": "c2",
                "actions": [{"type": "move", "x": 1, "y": 2}],
            }
        ],
    }
    res_nav = cu.run(client, page, "task navigate")
    assert res_nav.stopped == "navigated off the allowlist to unauthorized.com"

    # 4. Multi-step with on_step callback and max steps reached
    page.url = "http://127.0.0.1:8765/portal"
    page.mouse.move.side_effect = None
    steps_recorded = []
    client.responses.return_value = {
        "id": "r3",
        "output": [
            {
                "type": "computer_call",
                "call_id": "c3",
                "action": {"type": "move", "x": 10, "y": 20},
                "pending_safety_checks": [{"id": "s1", "code": "chk1", "message": "msg"}],
            }
        ],
    }
    res_max = cu.run(client, page, "task max steps", max_steps=2, on_step=lambda s, p: steps_recorded.append(s))
    assert res_max.stopped == "max steps 2"
    assert steps_recorded == [0, 1]
    assert len(res_max.steps) == 2

