# Core run: Trieste booklet, Wonder's proven program (no scale truth)

Run `rec-trieste-20261031` on 2026-10-31 16:44 +0700 by `scripts/core_run.py trieste --cond 4.1` (no Meta call: the
program was written by muse-wonder-1.0 in P1a, response `resp_6ae5a63a238297fff10f457e`, 2 regenerations; sha `4b3aa8cd9487`).

| step | result |
|---|---|
| self-test re-run in the sandbox | PASS: 22/22 printed conditions, probes raised 2/2, differential max 0.00007 % over 200 cases, 69 ms |
| survey on condition 4.1 (p.148) drafts, all six entered | disp 17825.8 t vs printed 17827.7 t (-0.0106 %), 7 cases in one sandbox launch, 35 ms |
| t per mm (fore / mid / aft, each side) | 0.092 / 1.405 / 0.376 |
| consequence (Ro-Ro test ship, illustrative, not a bulk carrier) | 1 cm at d_mm 6.500 m = 36.99 t (TPC from the extracted table) |
| certificate decision | **ISSUE_WITH_WARNING** POSITIONS_ENTERED (6 positions entered) |

No cargo figure: no lightship constant or initial survey was entered, so cargo is not computed.
Recorded run JSON: `public/runs/rec-trieste-20261031.json`.
