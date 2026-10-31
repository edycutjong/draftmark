"""Run model-written survey code: static AST gate, then a resource-limited subprocess.

Never eval/exec generated code in the server process. The child runs
`python -I -S runner.py` in a fresh temp dir with an empty environment, rlimits
(CPU, address space, files, processes, file size), an audit hook that refuses
sockets/subprocesses/files outside its dir, and an allowlisted __builtins__.
Defense in depth, not a hard security boundary: the AST gate + rlimits + no secrets
in the child env carry the weight.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field

ALLOWED_IMPORTS = {"math", "bisect", "json", "statistics", "re"}  # re: the program parses raw page text
BANNED_NAMES = {"eval", "exec", "open", "compile", "__import__", "getattr", "setattr", "delattr", "vars", "locals",
                "globals", "__builtins__", "breakpoint", "input", "memoryview", "help", "exit", "quit"}
MAX_BYTES = 64 * 1024


@dataclass
class GateResult:
    ok: bool
    violations: list[str] = field(default_factory=list)


def static_gate(code: str) -> GateResult:
    v: list[str] = []
    if len(code.encode()) > MAX_BYTES:
        v.append(f"file larger than {MAX_BYTES} bytes")
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return GateResult(False, [f"syntax error: {e}"])
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORTS:
                    v.append(f"line {node.lineno}: import {a.name} not allowed")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in ALLOWED_IMPORTS or node.level:
                v.append(f"line {node.lineno}: from {node.module} import not allowed")
        elif isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            v.append(f"line {node.lineno}: name {node.id} not allowed")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__") and node.attr.endswith("__"):
            v.append(f"line {node.lineno}: dunder attribute {node.attr} not allowed")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and \
                node.value.startswith("__") and node.value.endswith("__"):
            v.append(f"line {node.lineno}: dunder string not allowed")
    names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    for need in ("parse_booklet", "survey"):
        if need not in names:
            v.append(f"missing function {need}()")
    return GateResult(not v, v)


RUNNER = r'''
import sys, json, resource
SAFE_MODS = {"math", "bisect", "json", "statistics", "re"}
_imp = __import__
def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level or name.split(".")[0] not in SAFE_MODS:
        raise ImportError("import of " + name + " blocked")
    return _imp(name, globals, locals, fromlist, level)
import math, bisect, statistics, re  # preload before the hook
WORKDIR = sys.argv[1]
def _hook(event, args):
    if event.startswith(("socket.", "subprocess.", "os.system", "os.exec", "os.spawn", "os.fork", "os.posix_spawn",
                         "ctypes.", "urllib.", "http.")):
        raise RuntimeError("blocked: " + event)
    if event == "open":
        path = str(args[0])
        if not (path.startswith(WORKDIR) or path.startswith(sys.prefix) or path.startswith(sys.base_prefix)
                or path.isdigit()):
            raise RuntimeError("blocked open: " + path)
sys.addaudithook(_hook)
class OutOfTable(ValueError):
    pass
SAFE = {k: __builtins__.__dict__[k] if hasattr(__builtins__, "__dict__") else __builtins__[k] for k in (
    "abs", "min", "max", "round", "len", "range", "enumerate", "zip", "sorted", "sum", "float", "int", "dict",
    "list", "tuple", "isinstance", "str", "bool", "pow", "any", "all", "set", "map", "filter", "reversed",
    "ValueError", "KeyError", "IndexError", "ZeroDivisionError", "TypeError", "ArithmeticError", "Exception",
    "print", "divmod", "frozenset", "iter", "next", "StopIteration", "RuntimeError")}
SAFE["OutOfTable"] = OutOfTable
SAFE["__import__"] = _safe_import
SAFE["__build_class__"] = __builtins__.__dict__["__build_class__"] if hasattr(__builtins__, "__dict__") else __builtins__["__build_class__"]
req = json.loads(sys.stdin.read())
code = open(WORKDIR + "/program.py").read()
g = {"__builtins__": SAFE, "__name__": "program", "OutOfTable": OutOfTable}
exec(compile(code, "program.py", "exec"), g)
out = {"ok": True}
try:
    ship = req.get("ship")
    if ship is None:
        ship = g["parse_booklet"](req["booklet"])
        out["ship"] = ship
    res = []
    for case in req.get("cases", []):
        try:
            r = g["survey"](case, ship)
            res.append({"ok": True, "out": {k: (float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v)
                                              for k, v in (r or {}).items()}})
        except Exception as e:
            res.append({"ok": False, "error": type(e).__name__ + ": " + str(e)[:300]})
    out["results"] = res
except Exception as e:
    out = {"ok": False, "error": type(e).__name__ + ": " + str(e)[:500]}
sys.stdout.write(json.dumps(out, default=str))
'''


def _limits(cpu_s: int, mem_mb: int, nproc: bool):
    def apply():  # runs in the child before exec
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s))
        try:
            resource.setrlimit(resource.RLIMIT_AS, (mem_mb << 20, mem_mb << 20))
        except (ValueError, OSError):
            pass  # macOS does not support RLIMIT_AS; Linux (Vercel) does
        resource.setrlimit(resource.RLIMIT_NOFILE, (16, 16))
        resource.setrlimit(resource.RLIMIT_FSIZE, (1 << 20, 1 << 20))
        if nproc:
            try:
                resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
            except (ValueError, OSError):
                pass
    return apply


@dataclass
class RunResult:
    ok: bool
    data: dict
    error: str | None
    wall_ms: int
    returncode: int


def run(code: str, request: dict, cpu_s: int = 5, mem_mb: int = 512, wall_s: float = 10.0,
        nproc: bool = True) -> RunResult:
    gate = static_gate(code)
    if not gate.ok:
        return RunResult(False, {}, "static gate: " + "; ".join(gate.violations[:10]), 0, -1)
    with tempfile.TemporaryDirectory(prefix="dm-sbx-") as d:
        d = os.path.realpath(d)
        with open(os.path.join(d, "program.py"), "w") as f:
            f.write(code)
        with open(os.path.join(d, "runner.py"), "w") as f:
            f.write(RUNNER)
        t0 = time.time()
        try:
            p = subprocess.run([sys.executable, "-I", "-S", os.path.join(d, "runner.py"), d],
                               input=json.dumps(request), capture_output=True, text=True, cwd=d, env={},
                               timeout=wall_s, preexec_fn=_limits(cpu_s, mem_mb, nproc))
        except subprocess.TimeoutExpired:
            return RunResult(False, {}, f"wall timeout {wall_s}s", int((time.time() - t0) * 1000), -9)
        ms = int((time.time() - t0) * 1000)
        if p.returncode != 0:
            return RunResult(False, {}, f"exit {p.returncode}: {p.stderr.strip()[-400:]}", ms, p.returncode)
        try:
            data = json.loads(p.stdout)
        except json.JSONDecodeError:
            return RunResult(False, {}, "bad JSON from child: " + p.stdout[:200], ms, p.returncode)
        return RunResult(bool(data.get("ok")), data, data.get("error"), ms, p.returncode)


def sha256(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()
