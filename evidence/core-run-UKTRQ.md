# Core run: UKTRQ_t20 (real hull, third-party clip, no ground truth)

Run `rec-uktrq-20261031` on 2026-10-31 16:08 +0700 by `scripts/core_run.py clip UKTRQ_t20` through the HTTP endpoints (FastAPI TestClient, the deployed code). Source: [UKTRQ_t20](https://www.youtube.com/watch?v=UKTRQ1KJ4G4); frames are not re-hosted.

| station | what ran | ms | Meta response ids |
|---|---|---|---|
| measure | SAM 3.1 video x2 concepts (stored) | 14697 | resp_6ae5aff3a1dd4facbd3f4669, resp_6ae5aff313ac34f042304dee |
| labels | Spark 1.3 x2 + 5 code checks (stored) | 46011 | resp_6ae5b00343caa8de0c3548cb, resp_6ae5b02b599a1c9ed28d4118 |
| draft | pure code | 108 |  |
| survey + certificate | proven program, one sandbox launch | 45 |  |

| measure | value |
|---|---|
| frames | 48 @ 6.0 fps |
| frames with >= 3 numeral tokens | 48/48 |
| frames with water | 46/48 |
| decision row 1 (masks / cap / water) | pass |
| label checks | {"monotone": true, "pitch": true, "residual": true, "cross_frame": true, "anchor": true} |
| frames kept | 46/48 |
| draft d (m) | 20.830 |
| u_rep (m, k=1, repeatability only) | 0.055 |
| N_eff · rho1 | 2.91 · 0.881 |
| one-pitch label error would shift d by (m) | 0.20 |
| certificate decision | **REFUSE** OUT_OF_TABLE |
| why | The draft is outside the vessel's hydrostatic table: the program refuses to extrapolate. OutOfTable: mean draft outside hydrostatic table |

The survey step runs Wonder's proven Trieste program on this draft (midships live, the other four
positions entered at the same value). This ship is not the Trieste booklet's vessel, so a draft outside
the booklet's 0.5-9.3 m table is refused by the program (OutOfTable) and the certificate is REFUSE: the
code refuses to extrapolate. The measurement itself stands (repeatability only, no ground truth).

Cost of this run (price-list estimate): $0.0760; rows appended to `evidence/api-usage.md`.
Recorded run JSON: `public/runs/rec-uktrq-20261031.json`.
