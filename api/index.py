"""FastAPI app for the Python Vercel functions, routed at /api/py/*."""
from __future__ import annotations

import os
import platform
import re
import resource
import subprocess
import sys
import tempfile
import time

import base64
import io
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from PIL import Image

from api._core import certificate, decision, labels, limits, marks, meta, pipeline, sandbox, selftest, sign, survey

VERSION = "0.2.0-p1b"
ROOT = Path(__file__).resolve().parents[1]
CLIPS = ROOT / "data" / "clips.json"  # registry of OUR committed fixture clips (public/clips/<id>.mp4)
MAX_UPLOAD = 3 * 1024 * 1024
# frozen nominal systematic terms for the barge strip (k=1, m): scripts/error_model_synthetic.py U_SYS
BARGE_U_SYS = {"scale": 0.0004, "edge": 0.5 / 6.0 / 1000, "par": 0.0003}
app = FastAPI(title="DraftMark API", docs_url="/api/py/docs", openapi_url="/api/py/openapi.json")
SCALES = (1.0, 0.1)  # ship metric marks; the 1:10 barge strip
MEAS_KEYS = ("d_m", "u_rep_m", "u_abs_m", "n_frames", "n_kept", "refused", "reason", "row1")


@app.exception_handler(KeyError)
@app.exception_handler(TypeError)
@app.exception_handler(ValueError)
async def _bad_payload(req: Request, e: Exception):  # a malformed body is the caller's error, not a 500
    return JSONResponse({"ok": False, "reason": "PAYLOAD", "detail": f"bad request body: {type(e).__name__}"},
                        status_code=400)


@app.get("/api/py/health")
def health():
    return {
        "ok": True,
        "version": VERSION,
        "key_present": meta.key_present(),
        "models": [meta.SAM, meta.SPARK, meta.WONDER],
        "live_mode": os.environ.get("LIVE_MODE", "on"),
        "budget": limits.budget_reason(),
        "fixtures": [c["id"] for c in _clips()],
    }


def _err(status: int, reason: str, detail: str = "", **kw) -> JSONResponse:
    return JSONResponse({"ok": False, "reason": reason, "detail": detail, **kw}, status_code=status)


def _clips() -> list[dict]:
    return json.loads(CLIPS.read_text())["clips"] if CLIPS.exists() else []


def _ip(req: Request) -> str:
    return (req.headers.get("x-forwarded-for") or (req.client.host if req.client else "?")).split(",")[0].strip()


def _client(run_id: str) -> meta.Client:
    # deployed: no ledger file (read-only FS); usage rows travel back in every response instead
    return meta.Client(ledger=None, enforce_cap=False, run_id=run_id, timeout=120.0)


def _meta_fail(e: Exception) -> JSONResponse:
    if isinstance(e, meta.BudgetError):
        limits.trip_budget(str(e))
        return _err(503, "BUDGET", "Meta API billing limit: live runs are off on this instance")
    if isinstance(e, meta.MetaError):
        return _err(502, "UPSTREAM", f"Meta API HTTP {str(e.args[0])[:1]}xx" if e.args else "Meta API error")
    return _err(502, "UPSTREAM", type(e).__name__)


def _gate(req: Request, upload: bool, code: str | None, run_id: str | None = None,
          ride: bool = False) -> JSONResponse | None:
    why = limits.budget_reason()
    if why:
        return _err(503, "BUDGET", why)
    if not meta.key_present():
        return _err(503, "BUDGET", "no API key on this deployment")
    if upload and not limits.judge_ok(code):
        return _err(403, "JUDGE_CODE", "uploads need the judge code from the submission notes")
    ok, why = limits.take(_ip(req), run_id=run_id, ride=ride)
    if not ok:
        return _err(429, "RATE", why or "")
    return None


@app.post("/api/py/measure")
async def measure_ep(req: Request):
    """Fixture id (open, rate-limited) or an MP4 data URL upload (JUDGE_CODE) -> SAM 3.1 video, two concepts
    concurrently -> compact geometry (tokens + water profile per frame) + decision-matrix row 1."""
    body = await req.json()
    upload = body.get("upload")
    if upload:
        if not str(upload).startswith("data:video/mp4;base64,"):
            return _err(415, "PAYLOAD", "MP4 only (SAM rejects WebM)")
        raw_len = len(upload.split(",", 1)[1]) * 3 // 4
        if raw_len > MAX_UPLOAD:
            return _err(413, "PAYLOAD", f"{raw_len} bytes > 3 MB")
        info = {"id": "upload", "source": "upload", "fps": float(body.get("fps") or 8),
                "frames": int(body.get("frames") or 0), "scale": float(body.get("scale") or 1.0)}
        if info["scale"] not in SCALES:
            return _err(400, "PAYLOAD", f"scale must be one of {SCALES}")
        if info["fps"] <= 0:
            return _err(400, "PAYLOAD", "fps > 0")
        if info["fps"] > 8.01 or info["frames"] > 64:
            return _err(413, "PAYLOAD", "<= 8 s at <= 8 fps")
        if info["frames"] <= 0:
            return _err(400, "PAYLOAD", "send the clip's frame count (frames > 0)")
        url = upload
    else:
        info = next((c for c in _clips() if c["id"] == body.get("fixture")), None)
        if info is None:
            return _err(404, "NO_FIXTURE", "unknown fixture id")
        url = meta.bytes_data_url((ROOT / "public" / info["file"].lstrip("/")).read_bytes(), "video/mp4")
    run_id = body.get("run_id") or f"live-{int(time.time())}"
    blocked = _gate(req, bool(upload), body.get("judge_code"), run_id)
    if blocked:
        return blocked
    cl = _client(run_id)
    concepts = ("white number", "water")
    t0 = time.time()
    try:
        with ThreadPoolExecutor(2) as ex:
            resps = list(ex.map(lambda c: cl.sam(c, url, video=True, frames=info["frames"] or None,
                                                 feature=f"sam video '{c}' {info['id']}"), concepts))
    except Exception as e:  # noqa: BLE001
        return _meta_fail(e)
    sam_ms = int((time.time() - t0) * 1000)
    texts = [meta.output_text(r) for r in resps]
    system = marks.SHIP if float(info.get("scale", 1.0)) == 1.0 else marks.BARGE
    observed = 1 + max((int(m) for t in texts for m in re.findall(r"<(\d+)f>", t)), default=0)
    n = max(int(info["frames"] or 0), observed)  # never trust a client-declared count below what SAM returned
    t1 = time.time()
    geom = pipeline.geometry(texts[0], texts[1], n, info["fps"], system, info.get("crop"))
    geom["provenance"] = {"run_id": run_id, "source": info["source"], "clip": info["id"], "models": [meta.SAM],
                          "response_ids": [r.get("id") for r in resps]}
    geom = sign.seal_geometry(geom)  # /labels and /draft refuse an edited geometry
    return {"ok": True, "run_id": run_id, "clip": {k: info.get(k) for k in ("id", "source", "fps", "frames",
                                                                           "scale", "crop", "file", "label")},
            "geometry": geom, "row1_hint": decision.HINTS.get(geom["row1"]) if geom["row1"] else None,
            "response_ids": [r.get("id") for r in resps],
            "timing_ms": {"sam": sam_ms, "decode": int((time.time() - t1) * 1000)},
            "usage": [meta.as_dict(r) for r in cl.rows]}


MAX_IMG_BYTES, MAX_IMG_PX = 2 * 1024 * 1024, 4_000_000


def _img(data_url: str) -> Image.Image:
    if not str(data_url).startswith(("data:image/jpeg;base64,", "data:image/png;base64,")):
        raise ValueError("frames must be JPEG/PNG data URLs")
    raw = base64.b64decode(data_url.split(",", 1)[1])
    if len(raw) > MAX_IMG_BYTES:
        raise ValueError("frame image > 2 MB")
    try:
        im = Image.open(io.BytesIO(raw))
    except Exception as e:  # noqa: BLE001
        raise ValueError("unreadable frame image") from e
    if im.width * im.height > MAX_IMG_PX:
        raise ValueError("frame image > 4 MP")
    return im.convert("RGB")


@app.post("/api/py/labels")
async def labels_ep(req: Request):
    """Two frames >= 1 s apart (JPEG data URLs, cropped like the clip) + geometry -> Spark 1.3 reads both
    (strict json_schema) -> five code checks. One re-read on failure; typed labels skip Spark (degraded)."""
    body = await req.json()
    try:
        geom = body["geometry"]
        system = pipeline.system_of(geom)
        toks, _ = pipeline.rebuild(geom)
        [int(k) for k in (body.get("frames") or {})]
    except (KeyError, TypeError, ValueError) as e:
        return _err(400, "PAYLOAD", f"bad labels request: {type(e).__name__}")
    if not sign.geometry_ok(geom):
        return _err(400, "UNSIGNED", "this geometry was not produced by /measure on this deployment, or was edited")
    strip = marks.strip_sequence() if system.scale < 1 else None
    typed = body.get("typed")
    lf = geom.get("label_frames")
    if typed:  # {track: label}; the user typed the values: same checks, run marked degraded
        if body.get("frame") is None and not lf:
            return _err(400, "LABEL_FRAMES", "no label frame in this geometry")
        f1 = int(body.get("frame") if body.get("frame") is not None else lf[0])
        if f1 not in toks:
            return _err(400, "LABEL_FRAMES", "frame not in geometry")
        drafts, chk = marks.check_labels(toks[f1], typed, typed, system, strip)
        return {"ok": True, "typed": True, "drafts": drafts, "checks": chk.as_dict(), "reads": {}, "usage": [],
                "labels_token": _labels_token(geom, drafts, chk, True)}
    frames = {int(k): v for k, v in (body.get("frames") or {}).items()}
    if not lf or set(frames) != set(lf):  # exactly the two frames >= 1 s apart chosen by /measure
        return _err(400, "LABEL_FRAMES", f"send exactly the label frames {lf}")
    try:
        imgs = {f: _img(u) for f, u in frames.items()}
    except ValueError as e:
        return _err(400, "PAYLOAD", str(e))
    run_id = body.get("run_id") or f"live-{int(time.time())}"
    blocked = _gate(req, False, None, run_id, ride=True)
    if blocked:
        return blocked
    cl = _client(run_id)
    reads, rids = {}, []
    try:
        hints: dict[int, str] | None = None
        for attempt in (1, 2):
            def one(item, attempt=attempt, hints=hints):
                f, im = item
                img, numbering = labels.annotate(im, toks[f])
                by_track, m = labels.read(cl, img, numbering, system, feature=f"spark labels f{f} try {attempt}",
                                          hint=(hints or {}).get(f))
                return f, by_track, m, numbering

            with ThreadPoolExecutor(2) as ex:  # the two reads are independent: run them concurrently
                got = list(ex.map(one, imgs.items()))
            reads = {f: by_track for f, by_track, _, _ in got}
            rids += [m.get("response_id") for _, _, m, _ in got]
            drafts, chk = pipeline.check(geom, reads, strip)
            if chk.ok:
                break
            hints = {f: _retry_hint(chk, numbering) for f, _, _, numbering in got}
    except Exception as e:  # noqa: BLE001
        return _meta_fail(e)
    return {"ok": True, "typed": False, "drafts": drafts, "checks": chk.as_dict(), "attempts": attempt,
            "reads": {str(k): v for k, v in reads.items()}, "response_ids": rids,
            "usage": [meta.as_dict(r) for r in cl.rows], "labels_token": _labels_token(geom, drafts, chk, False)}


def _labels_token(geom: dict, drafts: dict, chk: marks.CheckResult, typed: bool) -> dict:
    c = chk.as_dict()
    return sign.token("labels", {"geometry_sig": geom["sig"], "drafts": drafts, "typed": typed,
                                 "checks": {k: c.get(k) for k in ("monotone", "pitch", "residual", "cross_frame",
                                                                  "anchor", "ok")},
                                 "models": [] if typed else [meta.SPARK]})


_CHECK_TEXT = {"monotone": "the marks must increase upward", "pitch": "spacing does not match 20 cm per step",
               "residual": "the marks do not lie on one straight scale", "cross_frame": "the two frames disagree",
               "anchor": "the whole-metre mark ('NM') is not on a wide box"}


def _retry_hint(chk: marks.CheckResult, numbering: dict[str, str]) -> str:
    """The re-read prompt for ONE image: what failed, in the box numbers drawn on that image (never the answer)."""
    d = chk.as_dict()
    box_of = {track: n for n, track in numbering.items()}
    parts = [_CHECK_TEXT[k] for k in _CHECK_TEXT if not d.get(k)]
    boxes = sorted({box_of[t] for t in d.get("disagree") or [] if t in box_of}, key=int)
    if boxes:
        parts.append(f"check boxes {', '.join(boxes)} again")
    return "; ".join(parts) + ". Read each box again exactly as painted; answer '?' if unsure."


@app.post("/api/py/draft")
async def draft_ep(req: Request):
    """Geometry + confirmed drafts -> per-frame drafts and the clip average with u (pure code, no API)."""
    body = await req.json()
    geom = body["geometry"]
    system = pipeline.system_of(geom)
    u_sys = BARGE_U_SYS if system.scale < 1 else None
    lt = sign.token_ok("labels", body.get("labels_token")) if sign.geometry_ok(geom) else None
    if lt and lt["geometry_sig"] != geom["sig"]:
        lt = None
    drafts = lt["drafts"] if lt else body["drafts"]  # a signed run uses the labels /labels confirmed
    frames, res = pipeline.finish(geom, {k: float(v) for k, v in drafts.items()}, u_sys)
    result = res.as_dict()
    if lt:  # only a fully signed chain gets a measure token; anything else is certified as UNSIGNED
        prov = geom.get("provenance") or {}
        result["token"] = sign.token("measure", {
            **{k: result.get(k) for k in MEAS_KEYS if k != "row1"}, "row1": geom.get("row1"),
            "scale": system.scale, "run_id": prov.get("run_id"), "source": prov.get("source"),
            "clip": prov.get("clip"), "typed": lt["typed"], "checks": lt["checks"],
            "models": sorted(set(prov.get("models") or []) | set(lt["models"]))})
    return {"ok": True, "result": result, "frames": pipeline.frames_json(frames), "row1": geom.get("row1")}


@app.get("/api/py/program")
def program_ep(booklet: str = "trieste"):
    """The cached proven program: code, sha, author, response id, attempts and the recorded self-test."""
    if booklet not in survey.booklets():
        return _err(404, "NO_BOOKLET", "unknown booklet")
    p = survey.proven(booklet)
    return {"ok": True, "meta": p["meta"], "code": p["code"], "selftest": p["selftest"], "attempts": p["attempts"],
            "run": p["run"]}


@app.post("/api/py/selftest/rerun")
def selftest_rerun(req: Request, booklet: str = "trieste"):
    """Re-run the cached program on the booklet's printed rows + probes + differential in the sandbox (no API)."""
    if booklet not in survey.booklets():
        return _err(404, "NO_BOOKLET", "unknown booklet")
    ok, why = limits.take_free(_ip(req))
    if not ok:
        return _err(429, "RATE", why or "")
    p = survey.proven(booklet)
    st = selftest.run(p["code"], ship=p["ship"])
    return {"ok": True, "selftest": st.as_dict() if hasattr(st, "as_dict") else st.__dict__}


@app.post("/api/py/survey")
async def survey_ep(req: Request):
    """Measurement + labels + survey inputs -> survey (one sandbox launch) -> code-only decision -> certificate."""
    body = await req.json()
    mode = body.get("mode", "ship")
    if mode == "ship" and body.get("booklet", "trieste") not in survey.booklets():
        return _err(404, "NO_BOOKLET", "unknown booklet")
    ok, why = limits.take_free(_ip(req))
    if not ok:
        return _err(429, "RATE", why or "")
    meas = body.get("measure") or {}
    lab = body.get("labels")
    if not meas.get("n_frames") and not (mode == "ship" and body.get("survey") and body.get("booklet_info")):
        return _err(400, "NO_EVIDENCE", "a certificate needs a measured clip, or a ship survey on a named booklet")
    # the measurement, label checks and called models come from the signed token, never from the body
    tok = sign.token_ok("measure", meas.get("token"))
    srv_in = dict(body.get("survey") or {}) if body.get("survey") else None
    claims_live = bool(meas.get("n_frames")) or any(v in ("live", "clip") for v in ((srv_in or {}).get("sources") or {}).values())
    unsigned = claims_live and tok is None
    models: list[str] = []
    if tok:
        mode = "barge" if tok["scale"] < 1 else "ship"
        meas = {**meas, **{k: tok.get(k) for k in MEAS_KEYS}}
        lab = {**(lab or {}), "typed": tok["typed"], "checks": tok["checks"]}
        lab.pop("synthetic", None)
        models = list(tok["models"])
        body = {**body, "run_mode": "LIVE"}  # a signed measurement was made live: the anchor needs the user
        if srv_in and srv_in.get("drafts") and tok.get("d_m") is not None:
            src = srv_in.get("sources") or {}
            srv_in["drafts"] = {p: (tok["d_m"] if src.get(p) in ("live", "clip") else v) for p, v in srv_in["drafts"].items()}
            srv_in["u_live_m"] = tok.get("u_rep_m")
    if meas.get("n_frames") and meas.get("d_m") is None and not meas.get("refused") and not meas.get("row1"):
        meas = {**meas, "refused": True, "reason": meas.get("reason") or "FRAMES_LOW"}  # no draft = refused
    if mode == "barge":
        u = meas.get("u_abs_m") if meas.get("u_abs_m") is not None else meas.get("u_rep_m")
        if meas.get("d_m") is None:
            srv = {"program_author": "analytic", "out_of_table": False}
        else:
            srv = survey.barge({"d_m": meas["d_m"], "u_m": u, "what_if": body.get("what_if"),
                                "expected_u_kg": body.get("expected_u_kg")})
        st = None
    else:
        p = survey.proven(body.get("booklet", "trieste"))
        if srv_in:
            srv = survey.ship(srv_in, p)
        else:  # the measurement refused before any draft existed: certify the refusal, run no program
            srv = {"program_author": p["meta"]["program_author"], "response_id": p["meta"].get("response_id"),
                   "regen_count": p["meta"].get("regen_count"), "out_of_table": False}
        st = survey.selftest_summary(p["selftest"])
        st["failed_rows"] = survey.failed_rows(p["selftest"])
        st["fallback"] = None
    extra = {k: body.get(k) for k in ("bl", "tol_pct") if body.get(k) is not None}
    if unsigned:
        extra["unsigned"] = True
    cert = certificate.build(mode, body.get("run_mode", "LIVE"), meas, lab, srv, st, extra=extra,
                             clip=body.get("clip"), booklet=body.get("booklet_info"), run_id=body.get("run_id"),
                             models=models)
    cert["inputs"] = "signed" if tok else ("unsigned" if unsigned else "entered")
    return {"ok": True, "certificate": cert}


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
def probe_sandbox(code: str | None = None):
    """Deployed-runtime probe (no API cost): subprocess launch, each rlimit, audit hook, temp dir."""
    if not limits.probes_open(code):
        return _err(403, "JUDGE_CODE", "probes need the judge code on production")
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
    hook_test = sandbox.runner_source().replace('req = json.loads(sys.stdin.read())',
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
def probe_sleep(s: float = 1.0, code: str | None = None):
    """maxDuration probe: sleeps s seconds (capped at 300)."""
    if not limits.probes_open(code):
        return _err(403, "JUDGE_CODE", "probes need the judge code on production")
    s = max(0.0, min(300.0, s))
    t0 = time.time()
    time.sleep(s)
    return {"slept_s": round(time.time() - t0, 2)}
