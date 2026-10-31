# Live run on the deployed URL (P1c, 2026-10-31 ~16:58 WIB)

`https://draftmark.edycu.dev` (Vercel production, Python 3.12, region sin1). Script-driven through the public endpoints
with the judge code (the code lives in `~/.config/draftmark/`, never in this repo). Clip: `dB7X_t45` (third-party test
clip, 60 frames @ 6 fps, crop 2x, 1.1 MB; not re-hosted).

| step | endpoint | result | wall time |
|---|---|---|---|
| upload without the judge code | `POST /api/py/measure` | 403 `JUDGE_CODE` | <1 s |
| re-run Wonder's Trieste self-test | `POST /api/py/selftest/rerun` | PASS 22/22, sandbox on Vercel, no API cost | <2 s |
| measure (SAM 3.1 x2 concepts) | `POST /api/py/measure` | 200, row 1 clear, 60 frames; SAM 8.7 s + mask decode 32.9 s | 43.7 s |
| labels (Spark 1.3 x2 + 5 code checks) | `POST /api/py/labels` | 200, checks ok, 9 tokens; two runs | 12.5 s and 19.9 s |
| draft (pure code) | `POST /api/py/draft` | d = 12.761 m, u_rep = 0.086 m, 60/60 kept (same as the recorded run, `core-run-dB7X.md`) | 0.9 s |

Finding: mask decoding is the slow part on Vercel (32.9 s here vs 15-24 s locally); the UI shows the stations as they
finish. Meta response ids: `resp_6ae5bbaf16399a729fff46fc`, `resp_6ae5bbb4ff1d25a7c7f84de6` (labels, ledger rows);
the measure ids are in `api-usage.md` under run `live-probe-p1c`. One extra labels call (19.9 s run, about $0.01) is
not in the ledger. Cost of the ledgered rows: $0.041.

Bug found and fixed in this pass: `vercel.json` `excludeFiles` pattern `data/programs/**/attempt*` also excluded
`attempts.json`, so `/api/py/program`, `/selftest/rerun` and `/survey` returned 500 on the deployment until the pattern
became `attempt[0-9]*`.
