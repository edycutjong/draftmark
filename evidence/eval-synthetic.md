# SYNTHETIC — rendered by code, not filmed

# Synthetic barge eval (P1e)

`scripts/render_synthetic.py` draws 12 loads of a 100 x 100 mm box (light weight 0.18 kg, rho 997) at the
waterline physics gives, T = (light + cargo) / (rho x L x B), with the printed 1:10 numeral strip, a swell of
2, 4 or 6 mm amplitude, blur, exposure drift, sensor noise and MP4 compression (fixed seeds; the clips are
regenerated, not stored). `scripts/eval_synthetic.py` runs the whole flow on each MP4 through the deployed
endpoints (SAM 3.1 video x2 concepts -> Muse Spark 1.3 label reads + 5 code checks -> code draft -> barge
survey -> certificate) and compares the cargo with the truth in `data/synthetic/truth.csv`, which the flow
never reads. Nothing here was weighed, filmed or touched by a physical scale. The pass rule and the loads are
the ones pre-registered in `eval-protocol.md` (|cargo - truth| <= 2 %; a failed load counts as not passed).

## What is real and what is stood in

- **SAM 3.1, live:** the `white number` concept finds the rendered numerals (5254 glyph masks over 12 clips). The `water` concept returned **0 masks on all 12 clips**, so the native `/measure` stage would REFUSE every one of them (NO_MASKS). SAM does not segment code-drawn water; it does segment real water (the real-hull clips).
- **Stand-in:** the water mask here is a colour threshold on our own pixels (`water_stand_in`), one mask per
  frame. It is exact on rendered water, so this eval does not test SAM's water edge at all.
- **Muse Spark 1.3, live:** reads the numerals on two frames per clip; the five code checks run on the reads.
- **Simulated human step:** the certificate needs the user to confirm the whole-metre anchor; the script sets
  `anchor_confirmed` = the code's anchor check, so a failed anchor stays a refusal.
- **Code, not a model:** token grouping, dry-numeral scale fit, wave-averaging, the box's displacement, the
  cargo figure and the certificate.

## Headline

**12 of 12 loads within +-2 %** of the synthetic truth; median |error| 0.12 % (1.4 g), p90 0.42 % (3.2 g), worst 0.75 % (4.5 g) over the 12 loads that returned a cargo figure.

| band (kg) | loads | within +-2 % |
|---|---|---|
| 0.5-0.8 | 2 | 2 |
| 0.8-1.2 | 5 | 5 |
| 1.2-1.5 | 5 | 5 |

Truth inside the certificate's +-u (k=1): 12/12; inside +-2u: 12/12. A coverage percentage would need >= 8 held-out loads and the protocol's calibration split, so none is claimed.

## Per load

| load | truth cargo (g) | swell amp (mm) | true draft (mm) | read draft (mm) | draft err (mm) | u_rep (mm) | frames kept | cargo (g) | +-u (g) | err (g) | err (%) | within 2 % | certificate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 600 | 2 | 78.23 | 77.79 | -0.45 | 0.64 | 60/60 | 595.5 | 6.4 | -4.5 | -0.75 | yes | ISSUE_WITH_WARNING |
| 2 | 700 | 4 | 88.26 | 87.96 | -0.31 | 1.18 | 60/60 | 697.0 | 11.8 | -3.0 | -0.43 | yes | ISSUE_WITH_WARNING |
| 3 | 800 | 6 | 98.29 | 98.27 | -0.03 | 1.60 | 60/60 | 799.7 | 16.0 | -0.3 | -0.04 | yes | ISSUE_WITH_WARNING |
| 4 | 900 | 2 | 108.32 | 108.34 | +0.02 | 0.45 | 60/60 | 900.2 | 4.6 | +0.2 | +0.02 | yes | ISSUE |
| 5 | 1000 | 4 | 118.36 | 118.32 | -0.03 | 0.94 | 60/60 | 999.7 | 9.4 | -0.3 | -0.03 | yes | ISSUE |
| 6 | 1000 | 6 | 118.36 | 118.11 | -0.24 | 1.65 | 60/60 | 997.6 | 16.5 | -2.4 | -0.24 | yes | ISSUE_WITH_WARNING |
| 7 | 1100 | 2 | 128.39 | 128.26 | -0.13 | 0.47 | 60/60 | 1098.7 | 4.8 | -1.3 | -0.11 | yes | ISSUE |
| 8 | 1200 | 4 | 138.42 | 138.26 | -0.15 | 0.98 | 60/60 | 1198.5 | 9.8 | -1.5 | -0.13 | yes | ISSUE |
| 9 | 1200 | 6 | 138.42 | 138.33 | -0.08 | 1.39 | 60/60 | 1199.2 | 13.9 | -0.8 | -0.07 | yes | ISSUE_WITH_WARNING |
| 10 | 1300 | 2 | 148.45 | 148.29 | -0.16 | 0.51 | 60/60 | 1298.4 | 5.2 | -1.6 | -0.12 | yes | ISSUE |
| 11 | 1400 | 4 | 158.48 | 158.15 | -0.33 | 1.10 | 60/60 | 1396.7 | 11.0 | -3.3 | -0.23 | yes | ISSUE |
| 12 | 1500 | 6 | 168.51 | 168.63 | +0.12 | 1.76 | 60/60 | 1501.2 | 17.6 | +1.2 | +0.08 | yes | ISSUE_WITH_WARNING |

## What this does and does not show

- It shows the measuring chain (SAM mask edges + Spark's numeral reads checked by code + wave-averaging +
  the analytic box) recovers a known draft and cargo from rendered video with noise and swell.
- The render and the survey share the box's constants (the same booklet file), so the box's dimensions and
  light weight are not tested here; what is tested is reading the draft and carrying it to a cargo figure.
- It does not show a physical scale check, real water, glare, a real meniscus, a real strip print or a real
  camera: the render is ours, so any systematic our renderer omits is invisible here.
- The truth is the calm (equilibrium) draft; the clips are 10 s, so a partial swell period leaves a small
  residual in the mean, as it would on a real clip.
- The reading has a small negative bias (see the draft-error column): the printed bottom edge is blurred and
  the mask edge sits slightly above it. It is not corrected (analytic mode), and it is far inside +-2 %.

## Development history (what the first passes found)

The eval was developed on these same rendered loads, so the result is in-sample for the fixes below, not a
held-out score. Each failure was a real weakness in the measuring code or in the framing, not a pass-rule edit:

1. First pass, 6 px/mm framing, before any code change: load 1 `FRAMES_LOW` (every frame dropped as PERSPECTIVE:
   the top numeral was cut by the frame edge and measured 20 % short); loads 3 and 4 failed the label checks (the
   water cut the `1` of `1M` so its bottom edge no longer matched `M`'s, the two glyphs were not grouped, and
   then no whole-metre mark stayed dry in view); loads 6-12 were not scored because the local harness hit the
   per-IP spend limiter (harness bug, not a measurement). Scored then: loads 2, 5 and 7 passed, 1, 3, 4 failed.
2. Fixes (commit with this file): glyph grouping accepts a shared cap line as well as a shared baseline; the
   perspective test ignores a numeral cut by the frame's top edge; the label checks' geometric residual uses
   the dry numerals only (the same rule the fit already used); the render shows 115 mm of strip above the
   water (5 px/mm, the rig-gate floor) so a whole-metre mark is always dry, as a filmer would frame it.
   Three new unit tests; pytest 127.
3. Second pass (6 px/mm, fixes 1-3): 10 of 12; loads 3 and 4 still lacked a dry whole-metre mark in view,
   which led to the framing change above. This table is the third full pass, all 12 loads re-rendered and re-run.

Meta calls for the 12 loads: 48 responses, $0.538 (price-list estimate); rows in `api-usage.md`.
Reproduce: `python scripts/render_synthetic.py && python scripts/eval_synthetic.py` (live Meta calls) or
`--reuse` to re-score the cached results.
