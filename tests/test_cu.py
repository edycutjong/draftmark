from api._core import cu


def test_allowlist_hosts():
    assert cu.host_allowed("http://127.0.0.1:8765/portal/index.html")
    assert cu.host_allowed("https://en.wikipedia.org/wiki/Ever_Given")
    assert cu.host_allowed("https://draftmark.edycu.dev/portal")
    assert not cu.host_allowed("https://example.com/")
    assert not cu.host_allowed("https://evilwikipedia.org/")
    assert not cu.host_allowed("https://draftmark.edycu.dev.attacker.net/")


def test_read_back_compare_and_fault():
    cert = {"vessel": "X", "displacement": "17825.8", "cargo": "6581.8", "decision": "ISSUE"}
    ok = cu.compare(cert, {"vessel": "x", "displacement": "17,825.8", "cargo": "6581.80", "decision": "ISSUE"})
    assert ok["ok"]
    bad = cu.compare(cert, {"vessel": "X", "displacement": "17825.8", "cargo": "6582.8", "decision": "ISSUE"})
    assert not bad["ok"] and not bad["fields"]["cargo"]["match"]
    missing = cu.compare(cert, {"vessel": "X"})
    assert not missing["ok"]
