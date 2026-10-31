# Error model on synthetic barge geometry (no API calls)

`scripts/error_model_synthetic.py`: noise families differ from the estimator's model (two-harmonic swell,
per-column edge jitter + per-frame edge offset, systematic crest-occlusion bias 0-0.4 mm, print stretch
+-0.4 %, ~6 % dropped frames, submerged numerals with clipped masks). Truth = the calm draft. 60 frames at
6 fps, 6 px/mm. Nominal systematic terms (k=1, frozen here): scale 0.40 mm, edge 0.083 mm, parallax/occlusion 0.30 mm.

| seeds | measured | refused | bias (mm) | RMSE (mm) | max abs err (mm) | mean u_abs (mm) | truth inside +-u | truth inside +-2u (target >= 90 %) |
|---|---|---|---|---|---|---|---|---|
| 100 | 100 | 0 | +0.111 | 0.519 | 2.416 | 1.653 | 93 % | 96 % |

This checks the estimator and its stated uncertainty on geometry we control. It is not the bucket result:
real masks, glare and a real meniscus are measured on the human's clips (P1e, pre-registered protocol).
