import json
import subprocess
import sys

from api._core import sandbox

OK = '''import math
def parse_booklet(b):
    return {"n": len(b["pages"])}
def survey(c, ship):
    if c["x"] < 0:
        raise OutOfTable("neg")
    return {"disp_final": math.sqrt(c["x"]) + ship["n"]}
'''


def test_runs_and_reports_per_case_errors():
    r = sandbox.run(OK, {"booklet": {"pages": {"1": ""}}, "cases": [{"x": 4}, {"x": -1}]})
    assert r.ok and r.data["ship"] == {"n": 1}
    assert r.data["results"][0]["out"]["disp_final"] == 3.0
    assert not r.data["results"][1]["ok"] and "OutOfTable" in r.data["results"][1]["error"]


def test_static_gate_rejects():
    for src in ("import os\n", "import socket\n", "x = open('f')\n", "y = eval('1')\n", "z = (1).__class__\n",
                "w = '__globals__'\n", "from subprocess import run\n"):
        g = sandbox.static_gate(src + OK)
        assert not g.ok, src
    assert not sandbox.static_gate("def survey(c, s): return {}\n").ok  # parse_booklet missing


def test_cpu_limit_kills_infinite_loop():
    src = "def parse_booklet(b):\n    while True:\n        pass\ndef survey(c, s):\n    return {}\n"
    r = sandbox.run(src, {"booklet": {}}, cpu_s=1, wall_s=5)
    assert not r.ok


def test_child_env_is_empty_and_open_blocked_at_runtime():
    src = ("import re\ndef parse_booklet(b):\n    return {}\n"
           "def survey(c, s):\n    import json\n    return {'k': len(json.dumps(c))}\n")
    r = sandbox.run(src, {"booklet": {}, "cases": [{"a": 1}]})
    assert r.ok and r.data["results"][0]["ok"]
    sneaky = "import json\ndef parse_booklet(b):\n    import math\n    return {}\ndef survey(c, s):\n    import os\n    return {}\n"
    assert not sandbox.static_gate(sneaky).ok


ESCAPE = '''import re
def parse_booklet(b):
    return {}
def survey(c, s):
    sy = re.enum.sys
    return {"disp_final": 1.0, "leak": sy.modules["builtins"].open("/etc/hosts").read()[:20]}
'''


def test_gate_rejects_module_internals_and_aliasing():
    for src in ("import re\nx = re.enum\n", "import re as r\nx = r\n", "from re import enum\n", "import re._parser\n",
                "import json.decoder\n", "import json\nx = json.decoder\n", "x = [].open\n", "import math\ny = [math]\n"):
        g = sandbox.static_gate(src + OK)
        assert not g.ok, src
    assert sandbox.static_gate("import re\nfrom bisect import bisect_left\np = re.compile('x')\n" + OK).ok
    assert not sandbox.static_gate(ESCAPE).ok


def test_runtime_proxies_hold_even_if_the_gate_is_bypassed(monkeypatch):
    monkeypatch.setattr(sandbox, "static_gate", lambda code: sandbox.GateResult(True))
    r = sandbox.run(ESCAPE, {"booklet": {}, "cases": [{}]})
    assert r.ok and not r.data["results"][0]["ok"]
    assert "AttributeError" in r.data["results"][0]["error"] and "Host" not in json.dumps(r.data)


def test_audit_hook_normalises_paths(tmp_path):
    runner = sandbox.runner_source().replace(
        "req = json.loads(sys.stdin.read())", 'open(WORKDIR + "/../../../../../../etc/hosts")\nreq = 1')
    (tmp_path / "runner.py").write_text(runner)
    (tmp_path / "program.py").write_text(OK)
    p = subprocess.run([sys.executable, "-I", "-S", str(tmp_path / "runner.py"), str(tmp_path)], input="{}",
                       capture_output=True, text=True, env={}, timeout=10)
    assert "blocked open" in p.stderr
