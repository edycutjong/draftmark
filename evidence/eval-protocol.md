# Evaluation protocol: mini-barge vs kitchen scale (pre-registered)

Committed on 2026-10-31, **before any bucket footage or weighing existed**. The git history of this file is the
pre-registration record. Amendments are allowed only before the registered loads exist and are listed at the bottom with
their date. Code and thresholds are frozen at git tag `eval-freeze`. Any change after that tag is reported in
`eval-bucket.md` with the result before and after the change.

## What is tested
A box ("mini-barge") floats in a bucket with printed draft marks on its side: white numerals on a dark strip, 1 cm digits
every 2 cm, each numeral's bottom edge at its stated draft in cm. It is loaded with sand and filmed with waves. DraftMark
measures the time-averaged draft from the video. The survey program computes displacement, and cargo = displacement -
weighed light weight of the empty box. This is compared with `scale_g`, the dry sand mass weighed on a 1 g kitchen scale
before loading.

## Registered loads
12 loads. Sand mass in kg, load_id 1-12 in this order: 0.6, 0.7, 0.8, 0.9, 1.0, 1.0, 1.1, 1.2, 1.2, 1.3, 1.4, 1.5.
Extra loads may be filmed. They are reported in a separate table and never enter the headline.

## Pass rule and headline
- A load passes if |cargo - scale_g| <= 2 % of scale_g.
- **Headline = analytic mode on all registered loads**: "N of M loads within ±2 %", where M = registered loads not
  excluded under the rules below. Target: >= 90 % of M.
- Reported separately, never merged into one number:
  (1) the point error per load (g, %, and draft error in mm against the calm-water ruler);
  (2) coverage: is scale_g inside cargo ± 2u (u = standard uncertainty, k = 1)?;
  (3) the decision the app's certificate would print.
- Pass counts are reported per band (0.5-0.8 / 0.8-1.2 / 1.2-1.5 kg), never only pooled.
- A failed analytic result stays a failure. It is shown as one.

## Modes
- **Analytic (headline):** L, B (outer, at the waterline), light weight, strip zero offset and water density as measured.
  No fitting. The reported draft is **never bias-corrected**: the eval script asserts the correction coefficient is 0.
- **Calibrated (secondary, labelled):** two constants fitted by least squares on loads 1-4 (by load_id): an effective
  waterplane area A_eff and a draft offset b. Scored only on loads 5-12. If <= 5 registered loads are usable, calibrated mode is not computed.

## Uncertainty (rules frozen here; thresholds frozen at tag `eval-freeze`)
- Per frame: scale fit on numerals whose mask bottom is >= max(5 px, 3 x edge MAD) above the water edge (2x crop). Fewer
  than 3 such "dry" numerals -> the frame is dropped. Frames with edge MAD > 0.25 x pitch_px are dropped.
- Per-frame draft variance by the delta method including cov(a, b) of the scale fit.
- Outliers: |d_i - median| > 3.5 x 1.4826 x MAD are rejected and counted.
- Effective sample size: N_eff = N (1 - rho1) / (1 + rho1), rho1 = lag-1 autocorrelation clamped to [0, 0.99], N_eff >= 2.
- u_rep (repeatability) = sqrt(u_swell^2 + u_rand^2). u_abs adds the systematic terms (print stretch from the measured
  10-pitch span, mask-edge half pixel, strip zero offset, taper, density, scale resolution) in quadrature.
- The residual draft bias against the calm ruler, measured on loads 1-4, only widens u_abs. It is never subtracted in
  analytic mode.
- Coverage % is printed only with >= 8 held-out loads. Otherwise the residual list is published and u is labelled
  "nominal".
- The expected pass margin per band (RSS of draft u, L, B, zero offset, taper, density, scale) is computed from the
  measured `barge.md` values and published in `eval-bucket.md` before any load is scored.

## Labels in the evaluation
Numeral values are read by Muse Spark 1.3 (two frames) and confirmed by code: monotone, pitch, residual, cross-frame
agreement, and a contiguous run of the strip's printed sequence declared in `barge.md`. No human taps a label during the
evaluation. Label correctness is scored against the calm ruler afterwards. That score is never used to set a label.

## Exclusions (the only allowed ones, each listed with its load_id)
- Clip file missing or unreadable.
- `scale_g` blank.
- `MASS_CHANGED`: |scale_after_g - (light weight + scale_g)| > 2 g (water got into the box).
More than 2 registered loads excluded -> "target not met", whatever the pass count.

## Data handling
- `assets/bucket/loads.csv` is written only by the person who filmed. The evaluation never edits it.
- At first read, the script records the sha256 of every clip and of `loads.csv`. Every supplied load_id is published,
  pass or fail.
- Pilot clips (1-2 loads filmed before the registered set) are development data. They are never scored.
- The "beats the eyeball" comparison is made only if `eye_mm` is filled for >= 10 scored loads. Otherwise the claim is
  dropped.

## Amendments
(none)
