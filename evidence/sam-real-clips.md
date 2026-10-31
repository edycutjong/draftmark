# SAM 3.1 on real hull clips (P1a spike)

Third-party public YouTube clips, used as TEST footage only: no ground truth exists for them, no frame is
re-hosted here, and they never appear in the demo video. The scale-checked proof is the mini-barge (P1e).
Pipeline: `scripts/prep_clip.py` (cut, crop the mark column, 2x; handheld clips use a column-tracking crop
by normalised cross-correlation) -> `scripts/spike_sam.py` (SAM 3.1 video, concepts "white number" and
"water", run concurrently; glyph -> token grouping) -> `scripts/spike_labels.py` (Spark 1.3 strict-JSON
label reads on two frames >= 1 s apart, 5 code checks, then `api/core/measure.py`).

| clip (source) | segment | frames | numerals found | water found | tokens/frame (median) | raw glyphs max | labels (code checks) | frames kept | draft d (m) | u_rep (m, k=1) | sd (m) | median / Huber (m) | p5-p95 swell (m) | rho1 · N_eff | drops |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [dB7X-manr10](https://www.youtube.com/watch?v=dB7X-manr10) | t=45-55 s @ 6 fps, crop 160x440 px x2, tracked | 60 | 60/60 | 60/60 | 9 | 9 | confirmed 5/5 | 60/60 | 12.761 | 0.086 | 0.163 | 12.729 / 12.747 | 12.56-13.05 | 0.89 · 3.6 | none |
| [UKTRQ1KJ4G4](https://www.youtube.com/watch?v=UKTRQ1KJ4G4) | t=20-28 s @ 6 fps, crop 110x360 px x2, tracked | 48 | 48/48 | 46/48 | 8 | 13 | confirmed 5/5 | 46/48 | 20.830 | 0.055 | 0.093 | 20.828 / 20.832 | 20.67-20.97 | 0.88 · 2.9 | NO_WATER_EDGE 2 |
| [eeLL1kt2KiU](https://www.youtube.com/watch?v=eeLL1kt2KiU) | t=8-16 s @ 6 fps, crop 110x420 px x2, tracked | 48 | 48/48 | 45/48 | 10 | 13 | REFUSED by code (see note) | - | - | - | - | - | - | - | - |

## Label reads

- **dB7X_t45**: Spark reads (box number -> mark, top to bottom) {"0": {"1": "2", "2": "14M", "3": "8", "4": "6", "5": "4", "6": "2", "7": "13M", "8": "8", "9": "6"}, "10": {"1": "2", "2": "14M", "3": "8", "4": "6", "5": "4", "6": "2", "7": "13M", "8": "8", "9": "6"}}; response ids resp_6ae5a35a5b65e7c27d6f4266, resp_6ae5a368c6f0d68b80e04733.
- **UKTRQ_t20**: Spark reads (box number -> mark, top to bottom) {"17": {"1": "2", "2": "22M", "3": "8", "4": "6", "5": "4", "6": "2", "7": "21M", "8": "8", "9": "6"}, "29": {"1": "2", "2": "22M", "3": "8", "4": "6", "5": "4", "6": "2", "7": "?", "8": "?", "9": "2"}}; response ids resp_6ae5a3e21d109189159046ce, resp_6ae5a40fc6a2ce1e5eeb4145.
- **eeLL_t8**: Spark reads (box number -> mark, top to bottom) {"2": {"1": "4", "10": "6", "11": "4", "12": "2", "2": "2", "3": "10M", "4": "8", "5": "6", "6": "4", "7": "2", "8": "9M", "9": "8"}, "45": {"1": "4", "10": "8", "11": "6", "12": "4", "2": "2", "3": "?", "4": "8", "5": "6", "6": "4", "7": "2", "8": "?", "9": "?"}}; response ids resp_6ae5a453d1c511066b5a4323, resp_6ae5a4863a9e61b887f7410c.

Every token Spark named matches the painted mark visible in the annotated frame (checked by eye on the
annotated crops in P1a). On the second read Spark answered "?" for the half-submerged tokens instead of
guessing (UKTRQ: 2 tokens, eeLL: 3); the schema allows "?" and code treats it as no label.

## Why eeLL is refused
eeLL is a bow section with breaking waves and a strongly slanted mark column on a curved hull. Spark's two
reads agree and are monotone, but code refuses the labels: the scale-fit residual is 8.8 px against a
limit of 0.1 x pitch = 6.5 px (the marks are not on one straight scale), and the anchor check fails
because SAM boxed only part of the "10M" mark (a 12 px wide glyph), so the token labelled "10M" is not
geometrically wide. In the app this is the typed-labels fallback (run marked degraded). This is the
intended behaviour: code, not the model, decides whether a label is trusted.

## Reading the numbers
- d is the mean of kept frames; u_rep is repeatability only (swell + per-frame noise, k=1), NOT absolute
  accuracy: these clips have no ground truth. u_abs exists only for the calibrated mini-barge.
- The swell is strongly correlated frame to frame (rho1 ~0.9), so 46-60 frames carry ~3 independent
  samples (N_eff); a longer clip shrinks u_rep. A one-pitch label error would shift d by 0.20 m (ship).
- Day-0 test on a different 10 s segment of the dB7X ship gave 12.756 m; this run gives 12.761 m.

Cost: SAM video frames at $0.20 / 1k (price list); per-call rows in `evidence/api-usage.md`.
