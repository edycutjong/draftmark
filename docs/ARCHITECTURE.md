# DraftMark — architecture (written from the code, 2026-10-31)

One Next.js app on Vercel (`app/`, `components/`, `lib/`) plus one Python FastAPI function (`api/index.py`,
`maxDuration` 300 s) that holds every model call and every number. No database, no object store: the browser
carries the intermediate JSON from one stateless endpoint to the next.

## The flow (four stations)

```
 phone clip (prepared MP4, cropped to the mark column, <= 8 s, <= 8 fps)
   |
   | POST /api/py/measure        SAM 3.1 video x2 concepts in parallel: "white number", "water"
   v
 compact geometry                 marks.group_glyphs: glyph boxes -> mark tokens per frame
 (tokens + water profile/frame)   pipeline: row-1 checks (NO_MASKS, OBJECT_CAP, WATER_MISS), two label frames >= 1 s apart
   |
   | POST /api/py/labels          Muse Spark 1.3 reads the painted strings on each annotated frame (JSON schema)
   v                              marks.check_labels: five code checks; a label is used only if all pass
 confirmed labels -> drafts       (a) strictly increasing, (b) gaps = k x pitch, (c) fit residual < 0.1 pitch,
   |                              (d) both frames agree, (e) every "NM" token is geometrically wide (+ table range)
   | POST /api/py/draft
   v
 per-frame draft -> clip draft    measure.frame_draft: least squares y = a + b z on DRY marks only (mask bottom above
   |                              the water edge by a MAD margin), d = (w - a) / b, delta-method variance;
   |                              drop reasons per frame. measure.summarize: MAD outlier rejection, mean, lag-1
   |                              N_eff, u_rep = max(scatter / sqrt(N_eff), propagated per-frame floor), u_abs
   |                              only when systematic parts are known (barge). Water edge per column = top of the
   |                              water run that reaches the crop bottom (detached spray/reflections ignored)
   | POST /api/py/survey
   v
 survey + decision + certificate  survey.ship: ONE sandbox launch of the proven Wonder-written program:
                                  survey case + 6 x (+1 mm) + (+u, -u) cases -> displacement, t/mm, u_disp;
                                  code: deductibles, net, cargo (paired / single), gates; decision.decide:
                                  fixed rows, first REFUSE wins; certificate.build prints code values only
```

### Signed station chain (`api/_core/sign.py`)

The endpoints are stateless (no database on Vercel Hobby), so the browser carries each station's output to the
next. Every station signs what it produced: `/measure` seals the geometry (HMAC-SHA256, key derived from the
deployment's secret, never sent), `/labels` refuses an edited geometry before any Spark call and issues a labels
token, `/draft` issues a measure token only for a fully signed chain, and `/survey` takes the draft, u, label checks,
mark system and called models from that token, never from the request body. A measurement without a valid token is
certified `REFUSE UNSIGNED` (decision row 0). Drafts typed by hand stay possible and are printed as entered.

## Where each Meta model is load-bearing

| Model | Call | Without it |
|---|---|---|
| `sam-3.1` | video segmentation, two text concepts, on the cropped clip (`api/_core/sam.py` parses the box/mask grammar) | no numeral or water geometry; nothing to measure |
| `muse-spark-1.3` | reads which token is "12M", "8", ... on two annotated frames (`api/_core/labels.py`); code confirms, and the user confirms the anchor crop on a live run | geometry has no absolute scale; a human must type labels (LABELS_TYPED warning) |
| `muse-wonder-1.0` | writes the per-vessel survey program from the booklet pages (`scripts/spike_wonder_program.py`); the program is proven offline and cached in `data/programs/trieste/` | the hand-written reference program is used (REFERENCE_FALLBACK warning) |
| `muse-spark-1.3` (native `computer` tool) | OFFLINE SPIKE, not in the live flow: a computer-use sub-agent read back a filing on our demo portal (`api/_core/cu.py`, `scripts/spike_cu.py`, `evidence/cu-runs.md`) | the live app has no filing step |

## Proof of the model-written program (`api/_core/selftest.py`, `api/_core/sandbox.py`)

- Static AST gate (imports limited to math, bisect, json, statistics, re, and per module only the listed public
  functions: `re.enum.sys` is rejected; banned names and attributes; no `__` anywhere; 64 KB cap), then
  `python -I -S runner.py` in a fresh temp dir, empty environment, rlimits (CPU, address space, files, processes,
  file size), proxy modules holding only those functions, an audit hook refusing sockets, subprocesses, signals,
  directory listing and files outside the dir (paths normalised first), allowlisted builtins, JSON in/out.
  Defense in depth, not a hard boundary; the server never `eval`s generated code.
- `survey.proven` loads the cached program only if its sha256, the recorded self-test (same sha, PASS) and the
  parsed ship table (`ship_sha256`) all match `data/programs/<booklet>/proven.json`.
- The program's second trim correction reads MTC at d +- 0.5 m; survey refuses OUT_OF_TABLE unless both points lie
  inside the printed table (1.0-8.8 m mean draft for Trieste), so nothing is extrapolated.
- One launch runs the booklet's 22 PRINTED worked conditions, two out-of-range probes that must raise, and 200
  randomized cases against our reference program. PASS = >= 20/22 within 0.1 %, both probes raise, 0 differential
  failures, max differential <= 0.05 %. `POST /api/py/selftest/rerun` repeats it live at no API cost.

## Decision (`api/_core/decision.py`)

Rows in fixed order: 0 unsigned measurement, 1 masks / object cap / water, 2 frames kept, 3 labels + anchor, 4 out
of table / entered drafts inconsistent, 5 self-test, 6 uncertainty, 7 deductibles contradiction, 8 B/L difference,
9 warnings (partial frames, typed labels, reference fallback, entered positions, failed self-test row near today's
draft, 2u above the pass band, what-if). Every reason is an enum with a hint and a named test. Row 7 has no input in
the live app yet (it needs the cross-check agent, not built); it fires only in its unit test.

## Endpoints (`api/index.py`)

| Endpoint | Cost class | Notes |
|---|---|---|
| `GET /api/py/health` | free | key present, live mode, budget state |
| `POST /api/py/measure` | SAM | committed fixture id (rate-limited) or MP4 upload (needs `JUDGE_CODE`); <= 3 MB, <= 64 frames |
| `POST /api/py/labels` | Spark | two frames as JPEG data URLs, <= 2 MB / 4 MP each; one re-read on failure; typed labels skip Spark (degraded) |
| `POST /api/py/draft` | free | geometry + confirmed labels -> clip draft |
| `POST /api/py/survey` | free (per-IP cap) | sandboxed program run, decision, certificate; numbers from the measure token |
| `GET /api/py/program`, `POST /api/py/selftest/rerun` | free (re-run per-IP cap) | the cached program and its live re-proof |
| `GET /api/py/probe/*` | free | deployed-runtime probes; judge code required on production |

## Spend protection (`api/_core/limits.py`)

Per-IP and per-instance hourly counters (in memory; Hobby has no shared store), `JUDGE_CODE` for uploads (constant-
time compare), a fail-closed BUDGET flag on a Meta 402 / billing 429, and a `LIVE_MODE=off` kill switch. Every call
is logged with an estimated cost in `evidence/api-usage.md`.

## Known limits (stated, not hidden)

- Entered drafts (typed by hand) can be certified; the certificate prints each draft's source and a
  POSITIONS_ENTERED warning. It is a prototype, not a surveyor's document.
- The absolute metre value rests on Spark's read, a second read >= 1 s later agreeing on >= 3 tokens, the wide-glyph
  anchor check and the user's confirmation of the anchor crop: a consistent whole-metre misread passes the geometry
  checks by construction, so the anchor confirmation is required on every live run.
- The synthetic barge run exercises the code path from geometry to certificate (SAM does not detect rendered
  water); its labels come from the renderer's truth. It validates the arithmetic and error model, not the models.
- Real-ship clips are third-party footage without ground truth: they show repeatability and refusal only. Weight
  accuracy is shown on a rendered synthetic barge; the test booklet is a Ro-Ro/passenger ship, not a bulk carrier.
- Rate counters are per instance, so a cold start resets them; the budget flag and kill switch are the hard stops.
