"""Run model-written survey code: static AST gate, then a resource-limited subprocess.

Never eval/exec generated code in the server process. The child runs
`python -I -S runner.py` in a fresh temp dir with an empty environment, rlimits
(CPU, address space, files, processes, file size), an audit hook that refuses
sockets/subprocesses/signals/directory listing and files outside its dir (path
normalised, so `dir/../..` is refused), an allowlisted __builtins__, and proxy modules:
`import re` binds a namespace holding only MODULE_API["re"], so `re.enum.sys` does not
exist at runtime and the gate rejects it statically. Defense in depth, not a hard
security boundary: the AST gate + proxies + rlimits + no secrets in the child env carry
the weight.
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
BANNED_ATTRS = BANNED_NAMES - {"compile"}  # x.open / x.eval / x.getattr on any object; re.compile stays legal
MAX_BYTES = 64 * 1024
# The only module attributes generated code may touch (gate) and the only ones the child's proxy modules hold
# (runtime). Real modules leak their own imports as attributes (re.enum.sys -> sys.modules -> builtins.open).
MODULE_API = {
    "math": sorted(n for n in dir(__import__("math")) if not n.startswith("_")),
    "bisect": ["bisect", "bisect_left", "bisect_right", "insort", "insort_left", "insort_right"],
    "json": ["dumps", "loads", "JSONDecodeError"],
    "statistics": ["StatisticsError", "fmean", "geometric_mean", "harmonic_mean", "linear_regression", "mean",
                   "median", "median_high", "median_low", "mode", "multimode", "pstdev", "pvariance", "quantiles",
                   "stdev", "variance"],
    "re": ["A", "ASCII", "DOTALL", "I", "IGNORECASE", "M", "MULTILINE", "S", "VERBOSE", "X", "compile", "error",
           "escape", "findall", "finditer", "fullmatch", "match", "search", "split", "sub", "subn"],
}
assert set(MODULE_API) == ALLOWED_IMPORTS


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
    aliases: dict[str, str] = {}  # local name -> module
    parent: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for ch in ast.iter_child_nodes(node):
            parent[ch] = node
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name not in ALLOWED_IMPORTS:  # no submodules: re._parser, json.decoder ...
                    v.append(f"line {node.lineno}: import {a.name} not allowed")
                else:
                    aliases[a.asname or a.name] = a.name
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "") not in ALLOWED_IMPORTS or node.level:
                v.append(f"line {node.lineno}: from {node.module} import not allowed")
            else:
                for a in node.names:
                    if a.name not in MODULE_API[node.module]:
                        v.append(f"line {node.lineno}: from {node.module} import {a.name} not allowed")
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in aliases:
            par = parent.get(node)
            if not (isinstance(par, ast.Attribute) and par.value is node):
                v.append(f"line {node.lineno}: module {node.id} used as a value")
            elif par.attr not in MODULE_API[aliases[node.id]]:
                v.append(f"line {node.lineno}: {aliases[node.id]}.{par.attr} not allowed")
        if isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            v.append(f"line {node.lineno}: name {node.id} not allowed")
        elif isinstance(node, ast.Attribute) and node.attr in BANNED_ATTRS:
            v.append(f"line {node.lineno}: attribute {node.attr} not allowed")
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
import sys, json, resource, types, os.path
import math, bisect, statistics, re  # preload before the hook
API = json.loads(__API__)
PROXY = {m: types.SimpleNamespace(**{n: getattr(sys.modules[m], n) for n in names}) for m, names in API.items()}
def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level or name not in PROXY:
        raise ImportError("import of " + name + " blocked")
    return PROXY[name]  # a namespace of the allowed names only: no re.enum, no json.decoder
WORKDIR = os.path.normpath(sys.argv[1])
ROOTS = tuple(os.path.normpath(r) for r in {WORKDIR, sys.prefix, sys.base_prefix})
BLOCKED = ("socket.", "subprocess.", "os.system", "os.exec", "os.spawn", "os.fork", "os.posix_spawn", "os.kill",
           "os.killpg", "signal.", "os.listdir", "os.scandir", "os.remove", "os.unlink", "os.rename", "os.rmdir",
           "os.mkdir", "os.chmod", "os.chown", "os.chdir", "os.link", "os.symlink", "os.truncate", "os.putenv",
           "os.unsetenv", "shutil.", "ctypes.", "urllib.", "http.", "sys._getframe", "sys._current_frames")
def _inside(p):
    p = os.path.normpath(os.path.join(WORKDIR, p))  # string-only: no syscalls inside the hook
    return any(p == r or p.startswith(r + os.sep) for r in ROOTS)
def _hook(event, args):
    if event.startswith(BLOCKED):
        raise RuntimeError("blocked: " + event)
    if event == "open":
        path = args[0]
        if not (isinstance(path, int) or (isinstance(path, str) and _inside(path))):
            raise RuntimeError("blocked open: " + str(path))
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
            f.write(runner_source())
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


def runner_source() -> str:
    return RUNNER.replace("__API__", repr(json.dumps(MODULE_API)))


def sha256(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()
