# Evaluation protocol: mini-barge vs kitchen scale (pre-registered)

First committed on 2026-10-31, **before any bucket footage or weighing existed**. The git history of this file is the
pre-registration record. Amendments are allowed only before the registered loads exist. Each one is listed at the bottom
with its date. Code and thresholds are frozen at git tag `eval-freeze`. Any change after that tag is reported in
`eval-bucket.md` with the result before and after the change.

## What is tested
A box ("mini-barge") floats in a bucket with draft marks printed on its side. The marks are white numerals on a dark
strip, laid out like a ship's metric draft marks at 1:10 scale: "1M" = 10 cm, then "2", "4", "6", "8" at 12, 14, 16 and
18 cm, then "2M" = 20 cm, and so on. Each numeral is 1 cm tall and its bottom edge sits at its stated draft. The strip's
zero line sits at the box's outer bottom edge, and that alignment is photographed. The box is loaded with sand and filmed
with waves. DraftMark measures the time-averaged draft from the video. Cargo = displacement - weighed light weight of the
empty box. It is compared with `scale_g`, the dry sand mass weighed on a 1 g kitchen scale before loading.

The survey program for the box is analytic code (displacement = rho x L x B x T): this evaluation tests the
**measurement**. The program-writing proof (Muse Wonder vs a real stability booklet's printed conditions) is a separate
test with its own evidence file. The two are never merged into one claim.

## Registered loads
12 loads. Sand mass in kg, load_id 1-12 in this order: 0.6, 0.7, 0.8, 0.9, 1.0, 1.0, 1.1, 1.2, 1.2, 1.3, 1.4, 1.5.
Extra loads may be filmed. They are reported in a separate table and never enter the headline.
Load 7 (1.1 kg, waved clip) is the public live-demo clip, pass or fail.

## Pass rule and headline
- A load passes if |cargo - scale_g| <= 2 % of scale_g.
- **Headline = analytic mode: "N of 12 registered loads within ±2 %".** An excluded load counts as NOT passed and is
  listed with its reason in the same table. Target: >= 11 of 12.
- Reported in separate columns, never merged into one number:
  (1) the point error per load (g, %, and draft error in mm against the calm-water ruler);
  (2) "scale inside cargo ± u" and "scale inside cargo ± 2u (≈95 %)", where u is the standard uncertainty (k = 1).
      Any coverage percentage uses ± 2u and says so;
  (3) the decision the app's certificate would print.
- Pass counts are reported per band [0.5, 0.8), [0.8, 1.2), [1.2, 1.5] kg, never only pooled.
- A failed analytic result stays a failure. It is shown as one.

## Modes
- **Analytic (headline):** L, B (outer, at the waterline), light weight, strip zero offset and water density as measured.
  No fitting. The reported draft is **never bias-corrected**: the eval script asserts the correction coefficient is 0.
- **Calibrated (secondary, labelled, never in a headline):** two constants fitted by least squares on loads 2, 5, 8 and
  11 (spread across the range): an effective waterplane area A_eff and a draft offset b. Scored only on loads 1, 3, 4,
  6, 7, 9, 10 and 12.

## Uncertainty (rules frozen here; thresholds frozen at tag `eval-freeze`)
- Per frame: scale fit on numerals whose mask bottom is >= max(5 px, 3 x edge MAD) above the water edge (2x crop). Fewer
  than 3 such "dry" numerals -> the frame is dropped. Frames with edge MAD > 0.25 x pitch_px are dropped.
- Per-frame draft variance by the delta method including cov(a, b) of the scale fit.
- Outliers: |d_i - median| > 3.5 x 1.4826 x MAD are rejected and counted.
- Effective sample size: N_eff = N (1 - rho1) / (1 + rho1), rho1 = lag-1 autocorrelation clamped to [0, 0.99], N_eff >= 2.
- u_rep (repeatability) = sqrt(u_swell^2 + u_rand^2). u_abs adds in quadrature, each converted to grams of cargo: print
  stretch (from the measured 10-pitch span), strip zero offset, taper (L, B at 2-3 heights), water density (from the
  temperature via the Kell 1975 density formula; without a reading, its span over 18-32 °C), the calm-ruler reading
  spread (3 readings), and the scale resolution on light weight and sand.
- The residual draft bias against the calm ruler, measured on loads 2, 5, 8 and 11, replaces the mask-edge and parallax
  terms (it is not added on top of them). It only widens u_abs and is never subtracted in analytic mode.
- Coverage % is printed only with >= 8 held-out loads. Otherwise the residual list is published and u is labelled
  "nominal".
- **Before tag `eval-freeze`** the expected RSS u (k = 1) per registered load is computed from the pilot's measured
  `barge.md` values and appended below as an amendment. Pre-declared rule: a registered load whose expected u exceeds
  1 % of its cargo is replaced by the next heavier mass in 0.1 kg steps (at most 1.5 kg; duplicates allowed). The
  replacement is listed in that amendment.

## Labels in the evaluation
Numeral values are read by Muse Spark 1.3 (two frames) and confirmed by code: monotone, pitch, residual, cross-frame
agreement, the wide "NM" token as the absolute anchor, and a contiguous run of the strip's printed sequence declared in
`barge.md`. No human taps a label during the evaluation. A label failure is a scored FAIL for that load, not an
exclusion. Label correctness is scored against the calm ruler afterwards. That score is never used to set a label.

## Exclusions (the only allowed ones; each still counts as not passed)
- Clip file missing or unreadable.
- `scale_g` blank, or no phone photo of the scale display for it.
- `MASS_CHANGED`: |scale_after_g - (light weight + scale_g)| > 3 g, where `scale_after_g` = box + sand lifted out of
  the water, exterior wiped dry, weighed (photo required). This means water got into the box.

## Data handling
- `assets/bucket/loads.csv` and `barge.md` are written only by the person who filmed. The evaluation never edits them.
- At first read, before any Muse Spark call, the script records the sha256 of every clip, photo, `loads.csv` and
  `barge.md`. Every registered load_id is published, pass or fail.
- Per load, in this order: weigh the dry sand (photo) -> load and float -> waved clip, writing `eye_mm` (the filmer's own
  eyeball reading) during the take -> calm clip -> calm ruler read 3 times (photo) -> lift out, wipe, weigh
  `scale_after_g` (photo).
- Pilot clips (1-2 loads filmed before the registered set) are development data. They are never scored. Pilot rig
  gate before the registered loads: >= 5 px/mm on the 2x crop, median >= 4 dry numerals, >= 90 % of frames kept, calm
  |SAM waterline - ruler| <= 1 mm. If it fails, the filming setup changes before the registered loads (closer camera,
  more strip above the water, smaller waves). The gate result is appended below.
- The "beats the eyeball" comparison is made only if `eye_mm` is filled for >= 10 scored loads. Otherwise the claim is
  dropped.

## Amendments
- 2026-10-31 (still before any footage or weighing): one interval notation (u is k = 1; "± u" and "± 2u" columns);
  the denominator is all 12 registered loads, and exclusions count as not passed; the calibration loads are spread across
  the range (2, 5, 8, 11); the strip is laid out like a ship's marks at 1:10 scale with a wide "NM" anchor; the Sunday
  RSS rule and the pilot rig gate; `MASS_CHANGED` defined at 3 g with photos; ruler read 3 times; the order of
  `eye_mm`; load 7 named as the live-demo clip; a label failure is a scored FAIL.
- 2026-10-31 18:25 WIB (architecture review, before any held-out scoring; no physical loads will exist, human decision
  16:20): u_rep = max(u_swell, u_rand), not their RSS. The frame-to-frame scatter behind u_swell already contains each
  frame's own fit and edge noise, so adding the propagated per-frame term again double counted it; u_rand stays as a
  floor for few or identical frames. On the recorded runs the change is below 0.001 m (dB7X 0.0864 -> 0.0864 m,
  UKTRQ 0.0550 -> 0.0547 m, synthetic barge 1.856 -> 1.856 mm). Label check (d) now needs >= 3 shared tokens.
