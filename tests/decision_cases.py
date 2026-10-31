"""One fixture per decision-matrix reason (complexity.md §1). DEMO.md lists these by name."""
OK_SHIP = {"mode": "ship", "row1": None, "n_frames": 60, "n_kept": 60, "labels_ok": True, "anchor_ok": True,
           "out_of_table": False, "entered_inconsistent": False, "selftest_verdict": "PASS", "fallback": None,
           "failed_rows": [], "d_mm": 6.5, "trim": 0.56, "cargo": 5000.0, "u_cargo": 28.0, "perturb_oot": False,
           "n_entered": 0}
OK_BARGE = {"mode": "barge", "row1": None, "n_frames": 32, "n_kept": 32, "labels_ok": True, "anchor_ok": True,
            "cargo": 1.000, "u_cargo": 0.006, "expected_u": 0.006, "what_if": False}

CASES = {
    # reason: (facts, expected decision, expected reason)
    "UNSIGNED": ({**OK_SHIP, "unsigned": True, "row1": "OBJECT_CAP"}, "REFUSE", "UNSIGNED"),
    "NO_MASKS": ({**OK_BARGE, "row1": "NO_MASKS"}, "REFUSE", "NO_MASKS"),
    "OBJECT_CAP": ({**OK_SHIP, "row1": "OBJECT_CAP"}, "REFUSE", "OBJECT_CAP"),
    "WATER_MISS": ({**OK_BARGE, "row1": "WATER_MISS"}, "REFUSE", "WATER_MISS"),
    "FRAMES_LOW": ({**OK_BARGE, "n_kept": 19}, "REFUSE", "FRAMES_LOW"),
    "LABEL_FAIL": ({**OK_SHIP, "labels_ok": False}, "REFUSE", "LABEL_FAIL"),
    "NO_ANCHOR": ({**OK_SHIP, "anchor_ok": False}, "REFUSE", "NO_ANCHOR"),
    "OUT_OF_TABLE": ({**OK_SHIP, "out_of_table": True}, "REFUSE", "OUT_OF_TABLE"),
    "ENTERED_INCONSISTENT": ({**OK_SHIP, "entered_inconsistent": True}, "REFUSE", "ENTERED_INCONSISTENT"),
    "SELFTEST_FAIL": ({**OK_SHIP, "selftest_verdict": "FAIL"}, "REFUSE", "SELFTEST_FAIL"),
    "U_TOO_WIDE_SHIP": ({**OK_SHIP, "u_cargo": 51.0}, "REFUSE", "U_TOO_WIDE"),
    "U_TOO_WIDE_BARGE": ({**OK_BARGE, "u_cargo": 0.0121}, "REFUSE", "U_TOO_WIDE"),
    "U_TOO_WIDE_PERTURB": ({**OK_SHIP, "perturb_oot": True}, "REFUSE", "U_TOO_WIDE"),
    "DEDUCTIBLES_CONTRADICTION": ({**OK_SHIP, "contradiction": True}, "REFUSE", "DEDUCTIBLES_CONTRADICTION"),
    "PROTEST": ({**OK_SHIP, "bl": 5200.0, "tol_pct": 0.5}, "PROTEST", "BL_DIFFERENCE"),
    "FRAMES_PARTIAL": ({**OK_BARGE, "n_kept": 25}, "ISSUE_WITH_WARNING", None),
    "LABELS_TYPED": ({**OK_SHIP, "labels_ok": False, "labels_typed": True}, "ISSUE_WITH_WARNING", None),
    "REFERENCE_FALLBACK": ({**OK_SHIP, "selftest_verdict": "FAIL", "fallback": "reference"}, "ISSUE_WITH_WARNING",
                           None),
    "POSITIONS_ENTERED": ({**OK_SHIP, "n_entered": 4}, "ISSUE_WITH_WARNING", None),
    "SELFTEST_ROW_NEAR": ({**OK_SHIP, "failed_rows": [{"cond_id": "4.2", "d_mm": 6.7, "trim": 1.5}]},
                          "ISSUE_WITH_WARNING", None),
    "U_ABOVE_PASS_BAND": ({**OK_BARGE, "u_cargo": 0.0110, "expected_u": 0.0100}, "ISSUE_WITH_WARNING", None),
    "WHAT_IF": ({**OK_BARGE, "what_if": True}, "NOT_SCORED", "WHAT_IF"),
    "ISSUE_SHIP": (OK_SHIP, "ISSUE", None),
    "ISSUE_BARGE": (OK_BARGE, "ISSUE", None),
}
