"""Certificate assembly: every printed number comes from code (measure, survey, decision).

Two proofs, never merged: ship mode certifies with the model-written program proven on the booklet's
printed conditions (proof: booklet, no scale truth); barge mode certifies with the analytic box
(proof: measurement; its truth is known only for the code-rendered SYNTHETIC barge, never a physical scale check).
"""
from __future__ import annotations

import time
import uuid

from . import decision as D
from . import meta

FOOTER = "Prototype — not a surveyor's certificate."


def facts(mode: str, meas: dict | None, labels: dict | None, srv: dict, selftest: dict | None,
          extra: dict | None = None) -> dict:
    """Collect the decision-matrix inputs from the station outputs."""
    meas = meas or {}
    chk = (labels or {}).get("checks") or {}
    typed = bool((labels or {}).get("typed"))
    f = {"mode": mode, "row1": meas.get("row1"), "n_frames": meas.get("n_frames"), "n_kept": meas.get("n_kept"),
         "labels_ok": (all(chk.get(k) for k in ("monotone", "pitch", "residual", "cross_frame")) if chk else True),
         "anchor_ok": chk.get("anchor", True) if chk else True, "labels_typed": typed,
         "out_of_table": srv.get("out_of_table"), "entered_inconsistent": srv.get("entered_inconsistent"),
         "perturb_oot": srv.get("perturb_oot"), "cargo": srv.get("cargo"), "u_cargo": srv.get("u_cargo"),
         "expected_u": srv.get("expected_u"), "n_entered": srv.get("n_entered"), "what_if": srv.get("what_if"),
         "d_mm": srv.get("d_mm"), "trim": srv.get("trim")}
    if selftest:
        f["selftest_verdict"] = selftest.get("verdict")
        f["failed_rows"] = selftest.get("failed_rows", [])
        f["fallback"] = selftest.get("fallback")
    f.update(extra or {})
    return f


def build(mode: str, run_mode: str, meas: dict | None, labels: dict | None, srv: dict, selftest: dict | None,
          extra: dict | None = None, clip: dict | None = None, booklet: dict | None = None,
          models: list[str] | None = None, run_id: str | None = None, created_at: str | None = None) -> dict:
    f = facts(mode, meas, labels, srv, selftest, extra)
    dec = D.decide(f)
    meas = meas or {}
    cert = {
        "run_id": run_id or f"dm-{uuid.uuid4().hex[:10]}",
        "mode": run_mode,  # LIVE | RECORDED
        "vessel_mode": mode,  # ship | barge
        "proof": "booklet" if mode == "ship" else "measurement",
        "decision": dec.decision, "reason": dec.reason, "hint": dec.hint, "warnings": dec.warnings,
        "decision_row": dec.row,
        "draft": {k: meas.get(k) for k in ("d_m", "u_rep_m", "u_abs_m", "n_frames", "n_kept", "n_eff", "rho1",
                                             "swell_p5_p95", "label_shift_sensitivity_m", "drops")},
        "labels": {"read_by": "typed" if (labels or {}).get("typed") else meta.SPARK,
                   "degraded": bool((labels or {}).get("typed")),
                   "checks": (labels or {}).get("checks")} if labels is not None else None,
        "survey": srv,
        "selftest": selftest,
        "program_author": srv.get("program_author"),
        "response_id": srv.get("response_id"),
        "regen_count": srv.get("regen_count"),
        "models": models or [meta.SAM, meta.SPARK] + ([meta.WONDER] if mode == "ship" else []),
        "clip": clip, "booklet": booklet,
        "facts": f,
        "footer": FOOTER,
        "created_at": created_at or time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    if dec.decision == D.REFUSE:
        # a refusal prints no cargo figure, only the evidence for the refusal
        cert["survey"] = {k: v for k, v in srv.items() if k not in ("cargo", "net", "disp", "u_cargo", "u_disp")}
    return cert
