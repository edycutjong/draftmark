# Core run: mini-barge on SYNTHETIC geometry (seed 3)

Run `synth-barge-s3` on 2026-10-31 16:38 +0700 by `scripts/core_run.py synth --seed 3`. Geometry from
`scripts/error_model_synthetic.py` (two-harmonic swell, edge jitter, occlusion bias, print stretch, dropped
frames). No SAM call: SAM does not detect synthetic water (P1a), so this exercises the code path from
geometry to certificate, not the model. Labels come from the synthetic truth and pass the same five checks.
Barge booklet: `minibarge-synthetic` (SYNTHETIC placeholder until the human's barge.md (outer L, B, light weight, zero offset) exists; analytic oracle, never counted in the Trieste X of N).

| quantity | value |
|---|---|
| frames kept | 58/60 (drops {'NO_LABELLED_MARKS': 2}) |
| label checks | all 5 pass |
| draft d (m) vs synthetic calm truth | 0.10870 vs 0.10885 (-0.155 mm) |
| u_abs (mm, k=1) · u_rep (mm) | 1.924 · 1.856 |
| cargo (kg) vs synthetic truth | 0.9037 +- 0.0192 vs 0.9053 (-0.17 %) |
| 1 mm of draft = | 9.97 g |
| certificate decision | **ISSUE_WITH_WARNING**  U_ABOVE_PASS_BAND |

This is a code-path check on geometry we control, not a physical scale check (the synthetic eval is P1e).
Recorded run JSON: `public/runs/synth-barge-s3.json`.
