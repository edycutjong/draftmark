# Core run: dB7X_t45 (real hull, third-party clip, no ground truth)

Run `rec-db7x-20261031` on 2026-10-31 16:07 +0700 by `scripts/core_run.py clip dB7X_t45` through the HTTP endpoints (FastAPI TestClient, the deployed code). Source: [dB7X_t45](https://www.youtube.com/watch?v=dB7X-manr10); frames are not re-hosted.

| station | what ran | ms | Meta response ids |
|---|---|---|---|
| measure | SAM 3.1 video x2 concepts (stored) | 24322 | resp_6ae5afc5eaf19a98130b4b2d, resp_6ae5afc6a737472e198542a8 |
| labels | Spark 1.3 x2 + 5 code checks (stored) | 14611 | resp_6ae5afdecc5b13667f374d5e, resp_6ae5afe8bf4fcf96229347a0 |
| draft | pure code | 165 |  |
| survey + certificate | proven program, one sandbox launch | 44 |  |

| measure | value |
|---|---|
| frames | 60 @ 6.0 fps |
| frames with >= 3 numeral tokens | 60/60 |
| frames with water | 60/60 |
| decision row 1 (masks / cap / water) | pass |
| label checks | {"monotone": true, "pitch": true, "residual": true, "cross_frame": true, "anchor": true} |
| frames kept | 60/60 |
| draft d (m) | 12.761 |
| u_rep (m, k=1, repeatability only) | 0.086 |
| N_eff · rho1 | 3.55 · 0.888 |
| one-pitch label error would shift d by (m) | 0.20 |
| certificate decision | **REFUSE** OUT_OF_TABLE |
| why | The draft is outside the vessel's hydrostatic table: the program refuses to extrapolate. OutOfTable: mean draft outside hydrostatic table |

Anchor confirmation: a live user confirms the whole-metre anchor crop; this recorded replay has no user,
so the script sets it to the code's own anchor check (`anchor_confirmed` = checks.anchor).

The survey step runs Wonder's proven Trieste program on this draft (port midship live, the other five
positions entered at the same value). This ship is not the Trieste booklet's vessel, so a draft
outside the booklet's 0.5-9.3 m table is refused by the program (OutOfTable) and the certificate is
REFUSE: the code refuses to extrapolate. The measurement itself stands (repeatability only, no
ground truth). No cargo is computed for a real-hull test clip.

Cost of this run (price-list estimate): $0.0397; its rows are in `evidence/api-usage.md`.
Recorded run JSON: `public/runs/rec-db7x-20261031.json`.
