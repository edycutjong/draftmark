"""The certificate decision: code only, rows evaluated in a fixed order (first REFUSE wins).

No model output reaches this function except through code checks that already ran (labels
confirmed by the five checks, a program that passed its self-test in the sandbox). Every reason
is an enum with a one-line hint; each has a fixture and a named test (tests/test_decision.py).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

REFUSE, ISSUE, WARN, PROTEST, NOT_SCORED = "REFUSE", "ISSUE", "ISSUE_WITH_WARNING", "PROTEST", "NOT_SCORED"

HINTS = {
    # row 0
    "UNSIGNED": "The measurement was not signed by this server's stations (missing or edited): run the clip again.",
    # row 1
    "NO_MASKS": "SAM found no numerals or no water in the clip: reshoot closer, marks in frame.",
    "OBJECT_CAP": "SAM's 16-object cap was reached in a frame: crop to the lower marks.",
    "WATER_MISS": "The water mask never reaches the mark column: move the crop down to the waterline.",
    # row 2
    "FRAMES_LOW": "Fewer than 60 % of frames were usable: reshoot, hold still, closer, less glare.",
    # row 3
    "LABEL_FAIL": "The mark labels failed the code checks after a re-read: type the values by hand.",
    "NO_ANCHOR": "No whole-metre mark was confirmed as the absolute anchor.",
    # row 4
    "OUT_OF_TABLE": "The draft is outside the vessel's hydrostatic table: the program refuses to extrapolate.",
    "ENTERED_INCONSISTENT": "An entered draft is implausible against the others (hog/sag, port/starboard or trim gate).",
    # row 5
    "SELFTEST_FAIL": "The survey program did not pass the booklet self-test and no proven fallback exists.",
    # row 6
    "U_TOO_WIDE": "The uncertainty is too wide to certify (or a +-u case walks off the table).",
    # row 7
    "DEDUCTIBLES_CONTRADICTION": "The chief officer's statement contradicts the sounded deductibles.",
    # row 8
    "BL_DIFFERENCE": "The cargo differs from the bill-of-lading figure by more than the stated tolerance.",
    # row 9 warnings
    "FRAMES_PARTIAL": "60-90 % of frames were usable.",
    "LABELS_TYPED": "Labels were typed by hand (degraded run).",
    "REFERENCE_FALLBACK": "The hand-written reference program was used, not the model-written one.",
    "POSITIONS_ENTERED": "Some draft positions were entered, not measured from a clip.",
    "SELFTEST_ROW_NEAR": "A failed self-test row lies near today's draft or trim.",
    "U_ABOVE_PASS_BAND": "2u exceeds 2 % of the cargo: the result cannot show a +-2 % pass.",
    "WHAT_IF": "A what-if control moved density or geometry off the recorded values.",
}

SHIP_U_MAX_FRAC = 0.01  # row 6, ship: u_cargo (k=1) > 1 % of cargo
BARGE_U_FACTOR = 2.0  # row 6, barge: u_cargo > 2 x the protocol's expected RSS u for that load
KEPT_REFUSE, KEPT_WARN = 0.60, 0.90
NEAR_D_M, NEAR_TRIM_M = 0.5, 0.5  # SELFTEST_ROW_NEAR window around today's d_mm / trim


@dataclass
class Decision:
    decision: str
    reason: str | None = None
    hint: str | None = None
    warnings: list[dict] = field(default_factory=list)
    row: int | None = None

    def as_dict(self) -> dict:
        return asdict(self)


def _refuse(code: str, row: int, warnings: list[dict] | None = None) -> Decision:
    return Decision(REFUSE, code, HINTS[code], warnings or [], row)


def _w(code: str, detail: str | None = None) -> dict:
    return {"code": code, "hint": HINTS[code], **({"detail": detail} if detail else {})}


def decide(f: dict) -> Decision:
    """f: facts gathered by the pipeline (all optional except mode). Keys:
    mode ship|barge; row1 (reason or None); n_frames, n_kept, measure_refused; labels_ok, labels_typed, anchor_ok;
    out_of_table, entered_inconsistent; selftest_verdict PASS|FAIL, fallback (reference|None);
    failed_rows [{cond_id, d_mm, trim}], d_mm, trim; cargo, u_cargo, expected_u (barge), perturb_oot;
    contradiction (Tier 3); bl, tol_pct; n_entered (ship); what_if (barge); unsigned (row 0)."""
    mode = f["mode"]
    if f.get("unsigned"):
        return _refuse("UNSIGNED", 0)
    if f.get("row1"):
        return _refuse(f["row1"], 1)
    n, k = f.get("n_frames") or 0, f.get("n_kept") or 0
    frac = k / n if n else 0.0
    if (n and frac < KEPT_REFUSE) or f.get("measure_refused") == "FRAMES_LOW":
        return _refuse("FRAMES_LOW", 2)
    if not f.get("labels_ok", True) and not f.get("labels_typed"):
        return _refuse("LABEL_FAIL", 3)
    if not f.get("anchor_ok", True) and not f.get("labels_typed"):
        return _refuse("NO_ANCHOR", 3)
    if f.get("out_of_table"):
        return _refuse("OUT_OF_TABLE", 4)
    if f.get("entered_inconsistent"):
        return _refuse("ENTERED_INCONSISTENT", 4)
    fallback = f.get("fallback")
    if f.get("selftest_verdict") == "FAIL" and not fallback:
        return _refuse("SELFTEST_FAIL", 5)
    cargo, u = f.get("cargo"), f.get("u_cargo")
    if f.get("perturb_oot"):
        return _refuse("U_TOO_WIDE", 6)
    if cargo is not None and u is not None:
        if mode == "ship" and cargo != 0 and u > SHIP_U_MAX_FRAC * abs(cargo):  # discharge (paired) is negative
            return _refuse("U_TOO_WIDE", 6)
        if mode == "barge" and f.get("expected_u") and u > BARGE_U_FACTOR * f["expected_u"]:
            return _refuse("U_TOO_WIDE", 6)
    if f.get("contradiction"):
        return _refuse("DEDUCTIBLES_CONTRADICTION", 7)

    warnings: list[dict] = []
    if n and frac < KEPT_WARN:
        warnings.append(_w("FRAMES_PARTIAL", f"{k}/{n} frames kept"))
    if f.get("labels_typed"):
        warnings.append(_w("LABELS_TYPED"))
    if fallback == "reference":
        warnings.append(_w("REFERENCE_FALLBACK"))
    if mode == "ship" and f.get("n_entered"):
        warnings.append(_w("POSITIONS_ENTERED", f"{f['n_entered']} positions entered"))
    near = [r["cond_id"] for r in f.get("failed_rows") or []
            if f.get("d_mm") is not None and (abs(r["d_mm"] - f["d_mm"]) <= NEAR_D_M
                                              or abs(r["trim"] - (f.get("trim") or 0.0)) <= NEAR_TRIM_M)]
    if near:
        warnings.append(_w("SELFTEST_ROW_NEAR", ", ".join(near)))
    if mode == "barge" and cargo and u is not None and 2 * u > 0.02 * cargo:
        warnings.append(_w("U_ABOVE_PASS_BAND", f"2u = {2 * u / cargo * 100:.2f} % of cargo"))

    if mode == "barge" and f.get("what_if"):
        return Decision(NOT_SCORED, "WHAT_IF", HINTS["WHAT_IF"], warnings, None)
    bl, tol = f.get("bl"), f.get("tol_pct")
    if mode == "ship" and cargo is not None and bl and tol is not None and abs(cargo - bl) > tol / 100 * bl:
        return Decision(PROTEST, "BL_DIFFERENCE", HINTS["BL_DIFFERENCE"], warnings, 8)
    if warnings:
        return Decision(WARN, None, None, warnings, 9)
    return Decision(ISSUE, None, None, [], 10)
