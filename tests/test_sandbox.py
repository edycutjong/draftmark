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
