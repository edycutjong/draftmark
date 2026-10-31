"""P1b core run: the whole flow through the HTTP endpoints (FastAPI TestClient, same code as deployed).

  python scripts/core_run.py clip dB7X_t45        # live SAM + Spark via /measure (upload path) + /labels
  python scripts/core_run.py trieste [--cond 4.1] # Wonder's proven program: /selftest/rerun + ship /survey
  python scripts/core_run.py synth [--seed 3]     # barge on synthetic geometry (no SAM: synthetic water is
                                                  # not detected by SAM), /draft + barge /survey
Writes evidence/core-run-<name>.md and public/runs/<run_id>.json (the recorded run the UI renders).
Third-party clips stay in .cache/ (gitignored): only derived geometry (boxes, water edges) is committed.
"""
import argparse
import base64
import json
import os
import secrets
import sys
import time
from pathlib import Path

from _common import CACHE, EVIDENCE, ROOT, meta

os.environ.setdefault("JUDGE_CODE", secrets.token_hex(16))  # local only: unlocks the upload path in-process
from fastapi.testclient import TestClient  # noqa: E402

from api._core import barge as B  # noqa: E402
from api._core import marks, pipeline, selftest, survey  # noqa: E402
from api.index import app  # noqa: E402

RUNS = ROOT / "public" / "runs"
CLIP_SRC = {"dB7X_t45": "https://www.youtube.com/watch?v=dB7X-manr10",
            "UKTRQ_t20": "https://www.youtube.com/watch?v=UKTRQ1KJ4G4",
            "eeLL_t8": "https://www.youtube.com/watch?v=eeLL1kt2KiU"}
api = TestClient(app)


def post(path, body):
    t0 = time.time()
    r = api.post(path, json=body)
    ms = int((time.time() - t0) * 1000)
    if r.status_code != 200:
        raise SystemExit(f"{path} -> {r.status_code}: {r.text[:300]}")
    return r.json(), ms


def ledger(rows):
    for row in rows:
        meta.append_ledger(meta.UsageRow(**row))


def jpeg_frames(clip: Path, idx):
    import cv2
    out = {}
    cap = cv2.VideoCapture(str(clip))
    for i in idx:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, fr = cap.read()
        if not ok:
            raise SystemExit(f"cannot read frame {i}")
        ok, buf = cv2.imencode(".jpg", fr, [cv2.IMWRITE_JPEG_QUALITY, 90])
        out[str(i)] = "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()
    cap.release()
    return out


def save_run(run: dict) -> Path:
    RUNS.mkdir(parents=True, exist_ok=True)
    p = RUNS / f"{run['run_id']}.json"
    p.write_text(json.dumps(run, separators=(",", ":"), default=float))
    idx = RUNS / "index.json"
    cur = json.loads(idx.read_text()) if idx.exists() else {"runs": []}
    cur["runs"] = [r for r in cur["runs"] if r["run_id"] != run["run_id"]] + [
        {"run_id": run["run_id"], "kind": run["kind"], "title": run["title"], "date": run["date"],
         "decision": run["certificate"]["decision"], "reason": run["certificate"]["reason"]}]
    idx.write_text(json.dumps(cur, indent=1))
    return p


def fmt(x, nd=3):
    return "-" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def run_clip(name: str):
    spent = meta.ledger_total()
    if spent >= meta.DEV_CAP_USD:  # the server client has no ledger; the local cap is enforced here
        raise SystemExit(f"dev cap ${meta.DEV_CAP_USD} reached (${spent:.2f})")
    clip = CACHE / "clips" / f"{name}.mp4"
    info = json.loads(clip.with_suffix(".json").read_text())
    run_id = f"rec-{name.split('_')[0].lower()}-{time.strftime('%Y%m%d')}"
    upload = "data:video/mp4;base64," + base64.b64encode(clip.read_bytes()).decode()
    m, ms_m = post("/api/py/measure", {"upload": upload, "judge_code": os.environ["JUDGE_CODE"], "fps": info["fps"],
                                       "frames": info["frames"], "scale": 1.0, "run_id": run_id})
    g = m["geometry"]
    usage = list(m["usage"])
    steps = [("measure", "SAM 3.1 video x2 concepts", ms_m, ", ".join(m["response_ids"]))]
    lab = None
    if g["row1"] is None and g["label_frames"]:
        lab, ms_l = post("/api/py/labels", {"geometry": g, "frames": jpeg_frames(clip, g["label_frames"]),
                                            "run_id": run_id})
        usage += lab["usage"]
        steps.append(("labels", f"Spark 1.3 x{len(lab['response_ids'])} + 5 code checks", ms_l,
                      ", ".join(lab["response_ids"])))
    d = None
    if lab and lab["checks"]["ok"]:
        d, ms_d = post("/api/py/draft", {"geometry": g, "drafts": lab["drafts"]})
        steps.append(("draft", "pure code", ms_d, ""))
    res = (d or {}).get("result") or {}
    measure_facts = {**res, "row1": g["row1"], "n_frames": g["n_frames"],
                     "n_kept": res.get("n_kept", 0)}
    dm = res.get("d_m")
    srv_in = None
    if dm is not None:
        drafts = {p: dm for p in survey.POSITIONS}
        sources = {p: ("live" if p.startswith("mid") else "entered") for p in survey.POSITIONS}
        srv_in = {"drafts": drafts, "sources": sources, "u_live_m": res.get("u_rep_m"), "sg": 1.025}
    cert = None
    if srv_in:
        c, ms_s = post("/api/py/survey", {"mode": "ship", "run_mode": "RECORDED", "measure": measure_facts,
                                          "labels": {"checks": lab["checks"]} if lab else None,
                                          "survey": srv_in, "run_id": run_id,
                                          "clip": {"id": name, "source": CLIP_SRC.get(name),
                                                   "note": "third-party test clip, no ground truth, not re-hosted"}})
        cert = c["certificate"]
        steps.append(("survey + certificate", "proven program, one sandbox launch", ms_s, ""))
    ledger(usage)
    run = {"run_id": run_id, "kind": "public-clip", "title": f"Real hull test clip {name} (no ground truth)",
           "date": time.strftime("%Y-%m-%d %H:%M %z"), "clip": {"id": name, "source": CLIP_SRC.get(name), **info},
           "geometry": g, "labels": lab, "draft": d, "certificate": cert or {"decision": "REFUSE",
                                                                              "reason": g["row1"] or "LABEL_FAIL"},
           "usage": usage, "timing_ms": {s[0]: s[2] for s in steps}}
    path = save_run(run)
    usd = sum(u["est_usd"] for u in usage)
    L = [f"# Core run: {name} (real hull, third-party clip, no ground truth)", "",
         f"Run `{run_id}` on {run['date']} by `scripts/core_run.py clip {name}` through the HTTP endpoints "
         "(FastAPI TestClient, the deployed code). Source: " + f"[{name}]({CLIP_SRC.get(name)}); frames are not re-hosted.",
         "", "| station | what ran | ms | Meta response ids |", "|---|---|---|---|"]
    L += [f"| {a} | {b} | {c} | {e} |" for a, b, c, e in steps]
    L += ["", "| measure | value |", "|---|---|",
          f"| frames | {g['n_frames']} @ {info['fps']} fps |",
          f"| frames with >= 3 numeral tokens | {g['frames_with_3_tokens']}/{g['n_frames']} |",
          f"| frames with water | {g['frames_with_water']}/{g['n_frames']} |",
          f"| decision row 1 (masks / cap / water) | {g['row1'] or 'pass'} |",
          f"| label checks | {json.dumps({k: lab['checks'][k] for k in ('monotone', 'pitch', 'residual', 'cross_frame', 'anchor')}) if lab else '-'} |",
          f"| frames kept | {res.get('n_kept', '-')}/{g['n_frames']} |",
          f"| draft d (m) | {fmt(dm)} |", f"| u_rep (m, k=1, repeatability only) | {fmt(res.get('u_rep_m'))} |",
          f"| N_eff · rho1 | {fmt(res.get('n_eff'), 2)} · {fmt(res.get('rho1'), 3)} |",
          f"| one-pitch label error would shift d by (m) | {fmt(res.get('label_shift_sensitivity_m'), 2)} |"]
    if cert:
        L += [f"| certificate decision | **{cert['decision']}** {cert['reason'] or ''} |",
              f"| why | {cert['hint'] or ''} {cert['survey'].get('error') or ''} |"]
    L += ["", "The survey step runs Wonder's proven Trieste program on this draft (midships live, the other four",
          "positions entered at the same value). This ship is not the Trieste booklet's vessel, so a draft outside",
          "the booklet's 0.5-9.3 m table is refused by the program (OutOfTable) and the certificate is REFUSE: the",
          "code refuses to extrapolate. The measurement itself stands (repeatability only, no ground truth).",
          "", f"Cost of this run (price-list estimate): ${usd:.4f}; rows appended to `evidence/api-usage.md`.",
          f"Recorded run JSON: `public/runs/{path.name}`.", ""]
    (EVIDENCE / f"core-run-{name.split('_')[0]}.md").write_text("\n".join(L))
    print(json.dumps({"run": run_id, "d": dm, "u_rep": res.get("u_rep_m"), "kept": res.get("n_kept"),
                      "decision": run["certificate"]["decision"], "reason": run["certificate"]["reason"],
                      "usd": round(usd, 4), "timing": run["timing_ms"]}, indent=1))


def run_trieste(cond_id: str):
    run_id = f"rec-trieste-{time.strftime('%Y%m%d')}"
    t0 = time.time()
    st = api.post("/api/py/selftest/rerun").json()["selftest"]
    ms_st = int((time.time() - t0) * 1000)
    prog = api.get("/api/py/program").json()
    c = next(x for x in selftest.conditions() if x["cond_id"] == cond_id)
    drafts = {p: c["inputs"][p] for p in survey.POSITIONS}
    srv_in = {"drafts": drafts, "sources": {p: "entered" for p in survey.POSITIONS}, "sg": c["inputs"]["sg"]}
    out, ms_s = post("/api/py/survey", {"mode": "ship", "run_mode": "RECORDED", "survey": srv_in, "run_id": run_id,
                                        "booklet_info": {"id": "trieste", "condition": cond_id,
                                                         "printed_disp_t": c["expected"], "page": c["page"]}})
    cert = out["certificate"]
    s = cert["survey"]
    run = {"run_id": run_id, "kind": "booklet-proof", "title": "Wonder's survey program proves itself on the Trieste "
           "booklet (no scale truth)", "date": time.strftime("%Y-%m-%d %H:%M %z"), "selftest": st,
           "program": {"meta": prog["meta"], "attempts": prog["attempts"], "code": prog["code"]},
           "certificate": cert, "usage": [], "timing_ms": {"selftest_rerun": ms_st, "survey": ms_s}}
    path = save_run(run)
    err = (s["disp"] - c["expected"]) / c["expected"] * 100
    L = ["# Core run: Trieste booklet, Wonder's proven program (no scale truth)", "",
         f"Run `{run_id}` on {run['date']} by `scripts/core_run.py trieste --cond {cond_id}` (no Meta call: the",
         f"program was written by {prog['meta']['program_author']} in P1a, response `{prog['meta']['response_id']}`, "
         f"{prog['meta']['regen_count']} regenerations; sha `{prog['meta']['sha256'][:12]}`).", "",
         "| step | result |", "|---|---|",
         f"| self-test re-run in the sandbox | {st['verdict']}: {st['pass_count']}/{st['n']} printed conditions, "
         f"probes raised {sum(st['probes_raised'])}/{len(st['probes_raised'])}, differential max "
         f"{st['differential_max_err_pct']:.5f} % over {st['differential_n']} cases, {ms_st} ms |",
         f"| survey on condition {cond_id} (p.{c['page']}) drafts, all six entered | disp {s['disp']:.1f} t vs printed "
         f"{c['expected']:.1f} t ({err:+.4f} %), {s['n_cases']} cases in one sandbox launch, {s['sandbox_ms']} ms |",
         f"| t per mm (fore / mid / aft, each side) | {s['t_per_mm']['fore_p']:.3f} / {s['t_per_mm']['mid_p']:.3f} / "
         f"{s['t_per_mm']['aft_p']:.3f} |",
         f"| consequence (Ro-Ro test ship, illustrative, not a bulk carrier) | 1 cm at d_mm {s['d_mm']:.3f} m = "
         f"{s['consequence']['tpc_t_per_cm']:.2f} t (TPC from the extracted table) |",
         f"| certificate decision | **{cert['decision']}** "
         f"{', '.join(w['code'] + ' (' + w.get('detail', '') + ')' for w in cert['warnings'])} |", "",
         "No cargo figure: no lightship constant or initial survey was entered, so cargo is not computed.",
         f"Recorded run JSON: `public/runs/{path.name}`.", ""]
    (EVIDENCE / "core-run-trieste.md").write_text("\n".join(L))
    print(json.dumps({"run": run_id, "selftest": f"{st['pass_count']}/{st['n']} {st['verdict']}",
                      "disp": s["disp"], "printed": c["expected"], "decision": cert["decision"]}, indent=1))


def label_of(z: float) -> str:
    cm = int(round(z * 100))
    return f"{cm // 10}M" if cm % 10 == 0 else str(cm % 10)


def run_synth(seed: int):
    sys.path.insert(0, str(ROOT / "scripts"))
    import error_model_synthetic as E
    toks, water, track_z, calm = E.clip(seed)
    n, fps = 60, 6.0
    raw = {i: sum(t.n_glyphs for t in ts) for i, ts in toks.items()}
    g = pipeline.geometry_from_tokens(toks, raw, [], water, n, fps, marks.BARGE,
                                      {"note": "synthetic geometry, no pixels"})
    f1, f2 = g["label_frames"]
    t1, _ = pipeline.rebuild(g)
    reads = {f: {t.track: label_of(track_z[t.track]) for t in t1[f]} for f in (f1, f2)}
    drafts, chk = pipeline.check(g, reads, marks.strip_sequence())
    d, ms_d = post("/api/py/draft", {"geometry": g, "drafts": drafts})
    res = d["result"]
    run_id = f"synth-barge-s{seed}"
    c, ms_s = post("/api/py/survey", {"mode": "barge", "run_mode": "RECORDED", "run_id": run_id,
                                      "measure": {**res, "row1": g["row1"]},
                                      "labels": {"checks": chk.as_dict()},
                                      "clip": {"id": run_id, "source": "synthetic (scripts/error_model_synthetic.py)"}})
    cert = c["certificate"]
    bk = survey.barge_booklet()
    truth = B.survey(survey.barge_from(bk), calm)["cargo_kg"]
    s = cert["survey"]
    run = {"run_id": run_id, "kind": "synthetic", "title": f"Mini-barge, SYNTHETIC geometry (seed {seed}; not SAM, "
           "not the scale)", "date": time.strftime("%Y-%m-%d %H:%M %z"), "geometry": g,
           "labels": {"typed": False, "synthetic": True, "checks": chk.as_dict(), "drafts": drafts},
           "draft": d, "certificate": cert, "truth": {"calm_draft_m": calm, "cargo_kg": truth}, "usage": [],
           "timing_ms": {"draft": ms_d, "survey": ms_s}}
    path = save_run(run)
    cargo = s.get("cargo")
    L = [f"# Core run: mini-barge on SYNTHETIC geometry (seed {seed})", "",
         f"Run `{run_id}` on {run['date']} by `scripts/core_run.py synth --seed {seed}`. Geometry from",
         "`scripts/error_model_synthetic.py` (two-harmonic swell, edge jitter, occlusion bias, print stretch, dropped",
         "frames). No SAM call: SAM does not detect synthetic water (P1a), so this exercises the code path from",
         "geometry to certificate, not the model. Labels come from the synthetic truth and pass the same five checks.",
         f"Barge booklet: `{bk['id']}` ({bk['note']}).", "",
         "| quantity | value |", "|---|---|",
         f"| frames kept | {res['n_kept']}/{res['n_frames']} (drops {res['drops']}) |",
         f"| label checks | {'all 5 pass' if chk.ok else chk.as_dict()} |",
         f"| draft d (m) vs synthetic calm truth | {res['d_m']:.5f} vs {calm:.5f} ({(res['d_m'] - calm) * 1000:+.3f} mm) |",
         f"| u_abs (mm, k=1) · u_rep (mm) | {res['u_abs_m'] * 1000:.3f} · {res['u_rep_m'] * 1000:.3f} |",
         f"| cargo (kg) vs synthetic truth | {fmt(cargo, 4)} +- {fmt(s.get('u_cargo'), 4)} vs {truth:.4f} "
         f"({(cargo - truth) / truth * 100:+.2f} %) |" if cargo is not None else "| cargo | - |",
         f"| 1 mm of draft = | {s['consequence']['g_per_mm']:.2f} g |" if s.get("consequence") else "",
         f"| certificate decision | **{cert['decision']}** {cert['reason'] or ''} "
         f"{', '.join(w['code'] for w in cert['warnings'])} |", "",
         "This is a code-path check on geometry we control, not a physical scale check (the synthetic eval is P1e).",
         f"Recorded run JSON: `public/runs/{path.name}`.", ""]
    (EVIDENCE / "core-run-synth-barge.md").write_text("\n".join(x for x in L if x is not None))
    print(json.dumps({"run": run_id, "d": res["d_m"], "calm": calm, "cargo": cargo, "truth": truth,
                      "decision": cert["decision"], "warnings": [w["code"] for w in cert["warnings"]]}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["clip", "trieste", "synth"])
    ap.add_argument("name", nargs="?")
    ap.add_argument("--cond", default="4.1")
    ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()
    meta.load_local_env()
    if a.what == "clip":
        run_clip(a.name)
    elif a.what == "trieste":
        run_trieste(a.cond)
    else:
        run_synth(a.seed)


if __name__ == "__main__":
    main()
