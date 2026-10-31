# Live run on the deployed URL after the architecture review (P1d, 2026-10-31 ~18:28 WIB)

`https://draftmark.edycu.dev` (Vercel production, build `efe60ef`). Script-driven through the public endpoints with
the judge code (kept in `~/.config/draftmark/`, never in this repo). Clip: `dB7X_t45` (third-party test clip,
60 frames @ 6 fps, crop 2x, 1.1 MB; not re-hosted). Run id `live-p1d-1793446130`.

| step | endpoint | result | wall time |
|---|---|---|---|
| measure (SAM 3.1 x2 concepts) | `POST /api/py/measure` | 200, row 1 clear, 60 frames, geometry sealed; SAM 6.4 s + mask decode 42.5 s | 51.1 s |
| labels (Spark 1.3 x2 + 5 code checks) | `POST /api/py/labels` | 200, checks ok on attempt 1, labels token issued | 14.6 s |
| labels on a geometry edited by 3 px | `POST /api/py/labels` | 400 `UNSIGNED`, no Spark call | 1.0 s |
| draft (pure code) | `POST /api/py/draft` | d = 12.761 m, u_rep = 0.086 m, 60/60 kept (same as `core-run-dB7X.md`), measure token issued | 1.2 s |
| survey, signed | `POST /api/py/survey` | REFUSE `OUT_OF_TABLE` (not the Trieste vessel), inputs signed, models sam-3.1 + muse-spark-1.3 from the token | 0.4 s |
| survey, token dropped, drafts forged to 6.5 m | `POST /api/py/survey` | REFUSE `UNSIGNED`, models [] | 0.6 s |
| survey, body edited to 6.5 m, token kept | `POST /api/py/survey` | the token's d = 12.761 m is used: REFUSE `OUT_OF_TABLE`, inputs signed | 0.4 s |
| re-run Wonder's Trieste self-test | `POST /api/py/selftest/rerun` | PASS 22/22, sandbox on Vercel, no API cost | 0.6 s |
| probes without the judge code | `GET /api/py/probe/sleep` | 403 | <1 s |

Meta response ids (ledger rows in `api-usage.md`, run `live-p1d-1793446130`): `resp_6ae5d0f8a3ddef2f3c56436e`,
`resp_6ae5d0f868684f14ecbd40a9` (SAM), `resp_6ae5d12a9ca6989f37164fcf`, `resp_6ae5d133bcf4e867510c4478` (Spark).
Estimated cost of the run: $0.041.

Latency: the measure step is dominated by decoding SAM's masks (pure-Python decoder in `meta_sam_parser`; locally
16.5 s of 18.8 s for this clip, identical output from our own parser). 51 s is under the function's 300 s limit;
the UI shows the stations as they finish.

## Final run after review rounds 2 and 3 (2026-10-31 ~20:02 WIB, build `dfbc23f`, run `live-p1d-1793451671`)

| step | result | wall time |
|---|---|---|
| measure | 200, row 1 clear, 60 frames, sealed; SAM 17.1 s + mask decode 39.1 s | 58.5 s |
| labels | 200, checks ok on attempt 1, labels token | 12.0 s |
| labels on an edited geometry | 400 `UNSIGNED` | 1.0 s |
| draft | d = 12.761 m, u_rep = 0.086 m, 60/60, measure token | 1.6 s |
| survey, signed (mid_p = the clip, other positions entered) | REFUSE `OUT_OF_TABLE`, inputs signed, models from the token | 0.6 s |
| survey, token dropped, forged 6.5 m | REFUSE `UNSIGNED`, models [] | 0.6 s |
| survey, body edited to 6.5 m, token kept | token's d = 12.761 m used: REFUSE `OUT_OF_TABLE` | 0.4 s |
| self-test re-run | PASS 22/22 (both probes raise OutOfTable) | 0.4 s |

Response ids: `resp_6ae5e69d37a25da88506485c`, `resp_6ae5e69fc2eec0d2028743a3` (SAM),
`resp_6ae5e6d979e05de4a16d4ada`, `resp_6ae5e6def11021bc8f184e39` (Spark). Estimated cost $0.041. The draft moved by
0.1 mm against the first run (12.76087 -> 12.76077 m) from the water edge now bridging <= 3 px mask holes.
