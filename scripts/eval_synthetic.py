"""P1e synthetic barge eval: the whole flow (SAM 3.1 -> Spark labels + 5 code checks -> code draft -> barge survey ->
certificate) on each rendered load, scored against the physics truth in data/synthetic/truth.csv.

The flow only receives the MP4. Truth is read after the flow returned. Run once with live Meta calls (cached per load in
data/synthetic/results/); `--reuse` re-scores the cached results with no Meta call, which is how the numbers are
regenerated on HEAD.

  python scripts/render_synthetic.py            # renders .cache/synthetic/loadNN.mp4 (deterministic, fixed seeds)
  python scripts/eval_synthetic.py [--only 7] [--reuse]
Writes evidence/eval-synthetic.md + evidence/eval-synthetic.csv.
"""
import argparse
import csv
import json
import statistics
import time

from _common import CACHE, EVIDENCE, ROOT, meta
from core_run import jpeg_frames, ledger, api

from api._core import marks, pipeline, sam, sign
from api._core.sam import SamObject
from api.index import _client

CLIPS = CACHE / "synthetic"
RESULTS = ROOT / "data" / "synthetic" / "results"  # committed: per-load flow outputs, so --reuse regenerates the table
SAM_CACHE = CLIPS / "sam"
TRUTH = ROOT / "data" / "synthetic" / "truth.csv"
BANDS = [("0.5-0.8", 0.5, 0.8), ("0.8-1.2", 0.8, 1.2), ("1.2-1.5", 1.2, 1.51)]
PASS_PCT = 2.0


def call(path, body):
    r = api.post(path, json=body)
    return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text)


def water_stand_in(clip, n_frames: int) -> list[SamObject]:
    """Water mask by colour on the rendered frame: teal water (G well above R) below the surface; the hull is red.
    One object per frame, mask cropped to its box (the SAM output convention)."""
    import cv2
    import numpy as np
    cap = cv2.VideoCapture(str(clip))
    objs = []
    for i in range(n_frames):
        ok, fr = cap.read()
        if not ok:
            break
        fr = cv2.GaussianBlur(fr, (5, 5), 0).astype(np.int16)
        m = fr[..., 1] > fr[..., 2] + 10  # G > R + 10 (OpenCV frames are BGR: [..,1]=G, [..,2]=R)
        ys, xs = np.nonzero(m)
        if len(ys) < 50:
            continue
        x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
        objs.append(SamObject(i, 0, (float(x0), float(y0), float(x1), float(y1)), m[y0:y1, x0:x1]))
    cap.release()
    return objs


def flow(load_id: int) -> dict:
    """Run the deployed code path on one clip (MP4 only). Returns the raw result; never reads truth."""
    clip = CLIPS / f"load{load_id:02d}.mp4"
    info = json.loads(clip.with_suffix(".json").read_text())
    run_id = f"eval-synth-{load_id:02d}"
    out = {"load_id": load_id, "stage": "measure", "usage": []}
    # Stage 1 = the app's /measure logic, with ONE change: SAM 3.1 does not segment rendered water (probed on every
    # load: 0 masks), so the water mask comes from a colour threshold on our own pixels (water_stand_in). Numerals
    # are still SAM's, live.
    url = meta.bytes_data_url(clip.read_bytes(), "video/mp4")
    cl = _client(run_id)
    sam_cache = SAM_CACHE / f"load{load_id:02d}.sam.json"  # SAM's raw output text, so a code fix re-runs without SAM
    if sam_cache.exists():
        texts = json.loads(sam_cache.read_text())
    else:
        try:
            texts = [meta.output_text(cl.sam(c, url, video=True, frames=info["frames"],
                                             feature=f"sam video '{c}' synth load {load_id}"))
                     for c in ("white number", "water")]
        except Exception as e:  # noqa: BLE001
            return {**out, "usage": [meta.as_dict(r) for r in cl.rows], "fail": f"SAM call failed: {str(e)[:160]}"}
        sam_cache.write_text(json.dumps(texts))
    out["usage"] += [meta.as_dict(r) for r in cl.rows]
    sam_water = sam.parse(texts[1])
    num = sam.parse(texts[0])
    out["sam_native"] = {"numeral_objs": len(num), "water_objs": len(sam_water)}
    water = water_stand_in(clip, info["frames"])
    g = pipeline.geometry_from_objects(num, water, info["frames"], info["fps"], marks.BARGE, None)
    g["provenance"] = {"run_id": run_id, "source": "SYNTHETIC", "clip": clip.stem, "models": [meta.SAM],
                       "water_mask": "colour-threshold stand-in (SAM finds no rendered water)"}
    g = sign.seal_geometry(g)
    out.update(geometry_row1=g["row1"], frames_with_water=g["frames_with_water"],
               frames_with_3_tokens=g["frames_with_3_tokens"], n_frames=g["n_frames"])
    if g["row1"] is not None or not g["label_frames"]:
        return {**out, "fail": f"decision row 1: {g['row1'] or 'no label frames'}"}
    out["stage"] = "labels"
    code, lab = call("/api/py/labels", {"geometry": g, "frames": jpeg_frames(clip, g["label_frames"]), "run_id": run_id})
    if code != 200:
        return {**out, "fail": f"labels HTTP {code}: {str(lab)[:160]}"}
    out["usage"] += lab["usage"]
    out["checks"] = lab["checks"]
    if not lab["checks"]["ok"]:
        return {**out, "fail": "label checks failed: " + json.dumps(
            {k: lab["checks"][k] for k in ("monotone", "pitch", "residual", "cross_frame", "anchor")})}
    out["stage"] = "draft"
    code, d = call("/api/py/draft", {"geometry": g, "drafts": lab["drafts"], "labels_token": lab["labels_token"]})
    if code != 200:
        return {**out, "fail": f"draft HTTP {code}: {str(d)[:160]}"}
    res = d["result"]
    token = res.get("token")
    out.update(result={k: res.get(k) for k in ("d_m", "u_rep_m", "n_kept", "n_frames", "n_eff", "rho1")})
    if res.get("d_m") is None:
        return {**out, "fail": f"no draft: {res.get('reason')}"}
    out["stage"] = "survey"
    code, c = call("/api/py/survey", {"mode": "barge", "run_mode": "RECORDED", "run_id": run_id,
                                      "measure": {**res, "row1": g["row1"], "n_frames": g["n_frames"], "token": token},
                                      "labels": {"checks": lab["checks"], "anchor_confirmed": bool(lab["checks"]["anchor"])},
                                      "models": sorted({u["model"] for u in out["usage"]}),
                                      "clip": {"id": run_id, "source": "SYNTHETIC (scripts/render_synthetic.py)"}})
    if code != 200:
        return {**out, "fail": f"survey HTTP {code}: {str(c)[:160]}"}
    cert = c["certificate"]
    s = cert["survey"]
    out["certificate"] = {"decision": cert["decision"], "reason": cert["reason"],
                          "warnings": [w["code"] for w in cert["warnings"]], "cargo_kg": s.get("cargo"),
                          "u_cargo_kg": s.get("u_cargo")}
    if s.get("cargo") is None:
        return {**out, "fail": f"certificate {cert['decision']} {cert['reason']}: no cargo figure"}
    return out


def _no_rate_limit():
    """In-process harness: the per-IP spend limiter guards the public deployment, not a local scored run."""
    from api._core import limits
    limits.take = lambda *a, **k: (True, None)
    limits.take_free = lambda *a, **k: (True, None)


def score(res: dict, t: dict) -> dict:
    row = {"load_id": int(t["load_id"]), "cargo_true_g": float(t["cargo_kg"]) * 1000,
           "amp_mm": float(t["amp_mm"]), "draft_true_mm": float(t["draft_true_mm"]), "fail": res.get("fail", "")}
    r, c = res.get("result") or {}, res.get("certificate") or {}
    row["decision"] = (c.get("decision") or "REFUSE") + (" " + (c.get("reason") or "") if c.get("reason") else "")
    if r.get("d_m") is not None:
        row["draft_mm"] = r["d_m"] * 1000
        row["draft_err_mm"] = row["draft_mm"] - row["draft_true_mm"]
        row["u_rep_mm"] = r["u_rep_m"] * 1000
        row["frames_kept"] = f"{r['n_kept']}/{r['n_frames']}"
    if c.get("cargo_kg") is not None:
        row["cargo_g"] = c["cargo_kg"] * 1000
        row["u_cargo_g"] = (c.get("u_cargo_kg") or 0.0) * 1000
        row["err_g"] = row["cargo_g"] - row["cargo_true_g"]
        row["err_pct"] = row["err_g"] / row["cargo_true_g"] * 100
        row["pass"] = abs(row["err_pct"]) <= PASS_PCT
        row["in_1u"] = abs(row["err_g"]) <= row["u_cargo_g"]
        row["in_2u"] = abs(row["err_g"]) <= 2 * row["u_cargo_g"]
    else:
        row["pass"] = False  # a failed or refused load counts as NOT passed and stays in the table
    return row


def pct(xs, q):
    xs = sorted(xs)
    k = (len(xs) - 1) * q
    f = int(k)
    return xs[f] + (xs[min(f + 1, len(xs) - 1)] - xs[f]) * (k - f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=int)
    ap.add_argument("--reuse", action="store_true", help="re-score cached results; no Meta call")
    a = ap.parse_args()
    meta.load_local_env()
    _no_rate_limit()
    RESULTS.mkdir(parents=True, exist_ok=True)
    SAM_CACHE.mkdir(parents=True, exist_ok=True)
    truth = {int(r["load_id"]): r for r in csv.DictReader(TRUTH.open())}
    ids = [a.only] if a.only else sorted(truth)
    rows = []
    for i in ids:
        cache = RESULTS / f"load{i:02d}.json"
        if a.reuse and cache.exists():
            res = json.loads(cache.read_text())
        else:
            if meta.ledger_total() >= meta.DEV_CAP_USD:
                raise SystemExit("dev cap reached")
            res = flow(i)
            res["ran_at"] = time.strftime("%Y-%m-%d %H:%M %z")
            ledger(res["usage"])
            cache.write_text(json.dumps(res, default=float))
        rows.append(score(res, truth[i]))
        print(i, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in rows[-1].items()})
    if a.only:
        return
    write(rows, [json.loads((RESULTS / f"load{i:02d}.json").read_text()) for i in ids])


def fmt(v, nd=1, sign=False):
    if v is None or v == "":
        return "-"
    return f"{v:+.{nd}f}" if sign else f"{v:.{nd}f}"


def write(rows, raws):
    n = len(rows)
    scored = [r for r in rows if "err_pct" in r]
    errs = [abs(r["err_pct"]) for r in scored]
    gerr = [abs(r["err_g"]) for r in scored]
    npass = sum(1 for r in rows if r["pass"])
    cols = ["load_id", "cargo_true_g", "amp_mm", "draft_true_mm", "draft_mm", "draft_err_mm", "u_rep_mm",
            "frames_kept", "cargo_g", "u_cargo_g", "err_g", "err_pct", "pass", "in_1u", "in_2u", "decision", "fail"]
    with (EVIDENCE / "eval-synthetic.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    n_num = sum(r["sam_native"]["numeral_objs"] for r in raws)
    n_wat = sum(r["sam_native"]["water_objs"] for r in raws)
    usd = sum(u["est_usd"] for rr in raws for u in rr.get("usage", []))
    ids = sorted({u["response_id"] for rr in raws for u in rr.get("usage", [])})
    L = ["# SYNTHETIC — rendered by code, not filmed", "",
         "# Synthetic barge eval (P1e)", "",
         "`scripts/render_synthetic.py` draws 12 loads of a 100 x 100 mm box (light weight 0.18 kg, rho 997) at the",
         "waterline physics gives, T = (light + cargo) / (rho x L x B), with the printed 1:10 numeral strip, a swell of",
         "2, 4 or 6 mm amplitude, blur, exposure drift, sensor noise and MP4 compression (fixed seeds; the clips are",
         "regenerated, not stored). `scripts/eval_synthetic.py` runs the whole flow on each MP4 through the deployed",
         "endpoints (SAM 3.1 video x2 concepts -> Muse Spark 1.3 label reads + 5 code checks -> code draft -> barge",
         "survey -> certificate) and compares the cargo with the truth in `data/synthetic/truth.csv`, which the flow",
         "never reads. Nothing here was weighed, filmed or touched by a physical scale. The pass rule and the loads are",
         "the ones pre-registered in `eval-protocol.md` (|cargo - truth| <= 2 %; a failed load counts as not passed).", "",
         "## What is real and what is stood in", "",
         f"- **SAM 3.1, live:** the `white number` concept finds the rendered numerals ({n_num} glyph masks over {n} "
         f"clips). The `water` concept returned **{n_wat} masks on all {n} clips**, so the native `/measure` stage would "
         "REFUSE every one of them "
         "(NO_MASKS). SAM does not segment code-drawn water; it does segment real water (the real-hull clips).",
         "- **Stand-in:** the water mask here is a colour threshold on our own pixels (`water_stand_in`), one mask per",
         "  frame. It is exact on rendered water, so this eval does not test SAM's water edge at all.",
         "- **Muse Spark 1.3, live:** reads the numerals on two frames per clip; the five code checks run on the reads.",
         "- **Simulated human step:** the certificate needs the user to confirm the whole-metre anchor; the script sets",
         "  `anchor_confirmed` = the code's anchor check, so a failed anchor stays a refusal.",
         "- **Code, not a model:** token grouping, dry-numeral scale fit, wave-averaging, the box's displacement, the",
         "  cargo figure and the certificate.", "",
         "## Headline", "",
         f"**{npass} of {n} loads within +-{PASS_PCT:g} %** of the synthetic truth"
         + (f"; median |error| {statistics.median(errs):.2f} % ({statistics.median(gerr):.1f} g), p90 "
            f"{pct(errs, 0.9):.2f} % ({pct(gerr, 0.9):.1f} g), worst {max(errs):.2f} % ({max(gerr):.1f} g) over the "
            f"{len(scored)} loads that returned a cargo figure." if scored else "; no load returned a cargo figure."), "",
         "| band (kg) | loads | within +-2 % |", "|---|---|---|"]
    for name, lo, hi in BANDS:
        b = [r for r in rows if lo <= r["cargo_true_g"] / 1000 < hi]
        L.append(f"| {name} | {len(b)} | {sum(1 for r in b if r['pass'])} |")
    in1 = sum(1 for r in scored if r["in_1u"])
    in2 = sum(1 for r in scored if r["in_2u"])
    L += ["", f"Truth inside the certificate's +-u (k=1): {in1}/{len(scored)}; inside +-2u: {in2}/{len(scored)}. "
          "A coverage percentage would need >= 8 held-out loads and the protocol's calibration split, so none is claimed.",
          "", "## Per load", "",
          "| load | truth cargo (g) | swell amp (mm) | true draft (mm) | read draft (mm) | draft err (mm) | u_rep (mm) | "
          "frames kept | cargo (g) | +-u (g) | err (g) | err (%) | within 2 % | certificate |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['load_id']} | {r['cargo_true_g']:.0f} | {r['amp_mm']:g} | {r['draft_true_mm']:.2f} | "
                 f"{fmt(r.get('draft_mm'), 2)} | {fmt(r.get('draft_err_mm'), 2, True)} | {fmt(r.get('u_rep_mm'), 2)} | "
                 f"{r.get('frames_kept', '-')} | {fmt(r.get('cargo_g'), 1)} | {fmt(r.get('u_cargo_g'), 1)} | "
                 f"{fmt(r.get('err_g'), 1, True)} | {fmt(r.get('err_pct'), 2, True)} | {'yes' if r['pass'] else 'NO'} | "
                 f"{r['decision']}{' — ' + r['fail'] if r['fail'] else ''} |")
    L += ["", "## What this does and does not show", "",
          "- It shows the measuring chain (SAM mask edges + Spark's numeral reads checked by code + wave-averaging +",
          "  the analytic box) recovers a known draft and cargo from rendered video with noise and swell.",
          "- The render and the survey share the box's constants (the same booklet file), so the box's dimensions and",
          "  light weight are not tested here; what is tested is reading the draft and carrying it to a cargo figure.",
          "- It does not show a physical scale check, real water, glare, a real meniscus, a real strip print or a real",
          "  camera: the render is ours, so any systematic our renderer omits is invisible here.",
          "- The truth is the calm (equilibrium) draft; the clips are 10 s, so a partial swell period leaves a small",
          "  residual in the mean, as it would on a real clip.",
          "- The reading has a small negative bias (see the draft-error column): the printed bottom edge is blurred and",
          "  the mask edge sits slightly above it. It is not corrected (analytic mode), and it is far inside +-2 %.", "",
          "## Development history (what the first passes found)", "",
          "The eval was developed on these same rendered loads, so the result is in-sample for the fixes below, not a",
          "held-out score. Each failure was a real weakness in the measuring code or in the framing, not a pass-rule edit:", "",
          "1. First pass, 6 px/mm framing, before any code change: load 1 `FRAMES_LOW` (every frame dropped as PERSPECTIVE:",
          "   the top numeral was cut by the frame edge and measured 20 % short); loads 3 and 4 failed the label checks (the",
          "   water cut the `1` of `1M` so its bottom edge no longer matched `M`'s, the two glyphs were not grouped, and",
          "   then no whole-metre mark stayed dry in view); loads 6-12 were not scored because the local harness hit the",
          "   per-IP spend limiter (harness bug, not a measurement). Scored then: loads 2, 5 and 7 passed, 1, 3, 4 failed.",
          "2. Fixes (commit with this file): glyph grouping accepts a shared cap line as well as a shared baseline; the",
          "   perspective test ignores a numeral cut by the frame's top edge; the label checks' geometric residual uses",
          "   the dry numerals only (the same rule the fit already used); the render shows 115 mm of strip above the",
          "   water (5 px/mm, the rig-gate floor) so a whole-metre mark is always dry, as a filmer would frame it.",
          "   Three new unit tests; pytest 127.",
          "3. Second pass (6 px/mm, fixes 1-3): 10 of 12; loads 3 and 4 still lacked a dry whole-metre mark in view,",
          "   which led to the framing change above. This table is the third full pass, all 12 loads re-rendered and re-run.", "",
          f"Meta calls for the {n} loads: {len(ids)} responses, ${usd:.3f} (price-list estimate); rows in `api-usage.md`.",
          "Reproduce: `python scripts/render_synthetic.py && python scripts/eval_synthetic.py` (live Meta calls) or",
          "`--reuse` to re-score the cached results.", ""]
    (EVIDENCE / "eval-synthetic.md").write_text("\n".join(L))
    print(json.dumps({"pass": f"{npass}/{n}", "median_pct": statistics.median(errs) if errs else None,
                      "p90_pct": pct(errs, 0.9) if errs else None}))


if __name__ == "__main__":
    main()
