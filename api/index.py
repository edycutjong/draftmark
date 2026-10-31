"""FastAPI app for the Python Vercel functions, routed at /api/py/*."""
from __future__ import annotations

import os
import platform
import resource
import subprocess
import sys
import tempfile
import time

from fastapi import FastAPI

from api._core import meta, sandbox

VERSION = "0.1.0-p1a"
app = FastAPI(title="DraftMark API", docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")


@app.get("/api/py/health")
def health():
    return {
        "ok": True,
        "version": VERSION,
        "key_present": meta.key_present(),
        "models": [meta.SAM, meta.SPARK, meta.WONDER],
        "live_mode": os.environ.get("LIVE_MODE", "on"),
    }


_PROBE_OK = '''import math
def parse_booklet(b):
    return {"n": 1}
def survey(c, ship):
    return {"disp_final": math.sqrt(c["x"])}
'''
_PROBE_LOOP = "def parse_booklet(b):\n    while True:\n        pass\ndef survey(c, s):\n    return {}\n"
_PROBE_MEM = "def parse_booklet(b):\n    x = [0] * (400 * 1024 * 1024)\n    return {}\ndef survey(c, s):\n    return {}\n"
_PROBE_OPEN = ("import json\ndef parse_booklet(b):\n    return {}\n"
               "def survey(c, s):\n    return {'n': len(json.load(c['f']))}\n")


@app.get("/api/py/probe/sandbox")
def probe_sandbox():
    """Deployed-runtime probe (no API cost): subprocess launch, each rlimit, audit hook, temp dir."""
    out: dict = {"python": sys.version.split()[0], "platform": platform.platform(), "tmp": tempfile.gettempdir()}
    t0 = time.time()
    r = sandbox.run(_PROBE_OK, {"booklet": {}, "cases": [{"x": 9}]})
    out["launch_ok"] = r.ok and r.data["results"][0]["out"]["disp_final"] == 3.0
    out["launch_ms"] = r.wall_ms
    out["launch_error"] = r.error
    r = sandbox.run(_PROBE_LOOP, {"booklet": {}}, cpu_s=1, wall_s=5)
    out["cpu_limit_kills"] = (not r.ok, r.error, r.wall_ms)
    r = sandbox.run(_PROBE_MEM, {"booklet": {}}, mem_mb=256)
    out["mem_limit_blocks"] = (not r.ok, (r.error or "")[-120:])
    # audit hook: a file object passed in cannot exist (JSON), so test open() via the hook directly
    code = "import json\ndef parse_booklet(b):\n    return {}\ndef survey(c, s):\n    return {}\n"
    hook_test = sandbox.RUNNER.replace('req = json.loads(sys.stdin.read())',
                                       'open("/etc/hostname")\nreq = json.loads(sys.stdin.read())')
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "program.py"), "w").write(code)
        open(os.path.join(d, "runner.py"), "w").write(hook_test)
        p = subprocess.run([sys.executable, "-I", "-S", os.path.join(d, "runner.py"), d], input="{}",
                           capture_output=True, text=True, env={}, timeout=10)
        out["audit_hook_blocks_open"] = ("blocked open" in p.stderr, p.stderr.strip()[-120:])
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NPROC)
        out["nproc_limit_parent"] = [soft, hard]
    except Exception as e:  # pragma: no cover
        out["nproc_limit_parent"] = str(e)
    r = sandbox.run(_PROBE_OK, {"booklet": {}, "cases": [{"x": 4}]}, nproc=True)
    out["nproc0_launch_ok"] = r.ok
    out["total_ms"] = int((time.time() - t0) * 1000)
    return out


@app.get("/api/py/probe/sleep")
def probe_sleep(s: float = 1.0):
    """maxDuration probe: sleeps s seconds (capped at 300)."""
    s = max(0.0, min(300.0, s))
    t0 = time.time()
    time.sleep(s)
    return {"slept_s": round(time.time() - t0, 2)}
