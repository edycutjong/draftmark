# Live run on the deployed URL, filmed for the demo video (P6c, 2026-11-01 06:48 WIB)

`https://draftmark.edycu.dev/survey` (Vercel production, build `2098932`). Driven in a real browser (Chrome, puppeteer) through the judge-code upload path, the run the demo video shows; the judge code is typed before the recording starts and is never in this repo. Clip: `dB7X_t45` (third-party test clip, 60 frames @ 6 fps, crop 2x; not re-hosted: its pixels are hidden in the video, the page's overlay of this run's SAM output is shown). Run id `live-mvx1wyzw`.

| step | endpoint | result (as printed on the page) | time |
|---|---|---|---|
| measure (SAM 3.1, two concepts) | `POST /api/py/measure` | frames 60 at 6 fps; numeral · water objects 506 · 60; frames with ≥ 3 tokens · with water 60 · 60; label frames 0 · 10 | round trip 50.0 s |
| labels (Spark 1.3 × 2 + five code checks) | `POST /api/py/labels` | pitch 66.76 px · fit residual 0.45 px · shared tokens 9; anchor reads 13M on token t1, 14M on token t5 | 11.7 s |
| anchor | (browser) | confirmed by the operator on camera (Confirm button) | — |
| draft (code only) | `POST /api/py/draft` | d 12.761 m, repeatability u ± 0.0863 m, frames kept 60 / 60, swell p5–p95 12.563 – 13.052 m | 1.2 s |
| program (cached, Wonder-written) | `GET /api/py/program` + `POST /api/py/selftest/rerun` | 22/22 printed conditions; live sandbox re-run: re-run just now · sandbox 59 ms · round trip 359 ms | — |
| survey + certificate | `POST /api/py/survey` | REFUSE OUT_OF_TABLE (matrix row 4), inputs signed | — |
| tamper test (signed draft edited to 6.500 m; the page's Tamper test control) | `POST /api/py/survey` | Edit this signed measurement the way a forger would: draft 12.761 m → 6.500 m on every mark, inside this booklet's table. Then send it to the same live endpoint. Edit the signed draft and resubmit REFUSE UNSIGNED matrix row 0 The measurement was not signed by this server's stations (missing or edited): run the clip again. LIVE inputs: unsigned · models credited: none · round trip 562 ms | 0.6 s |

Meta calls (ledger rows in `api-usage.md`, run `live-mvx1wyzw`): `resp_6ae67e2e6e6a44bdce3742f0` (sam-3.1, $0.0120), `resp_6ae67e2e0fd6f39b30444378` (sam-3.1, $0.0120), `resp_6ae67e6a3b240589c1234d71` (muse-spark-1.3, $0.0071), `resp_6ae67e6f9287b9086b964fc8` (muse-spark-1.3, $0.0136). Estimated cost of the run: $0.045.

Wall-clock waits in the video are sped up and labelled on screen (SAM and Spark only); everything else is real time: SAM 3.1 working: 49 s real shown at 10×; Spark 1.3 reading: 11 s real shown at 5×.

## Page text after the run (verbatim, stations 2-6)

```text
Measure
LIVE
done
13M
2
4
6
8
14M
2
13.0
13.2
13.4
13.6
13.8
14.0
14.2
12.927 m
Frame 59 / 59
Frames
60 at 6 fps
Numeral objects · water objects
506 · 60
Frames with ≥ 3 tokens · with water
60 · 60
Mark system
ship-metric · scale 1
Label frames
0 · 10
Round trip
50.0 s
3
Step 3:
Labels
LIVE
done

Read by muse-spark-1.3 on 2 frames; code checks decide.

Token	read · frame 0	read · frame 10	Confirmed	Draft (m)
t3	8	8	8	12.8
t1anchor	13M	13M	13M	13.0
t6	2	2	2	13.2
t4	4	4	4	13.4
t2	6	6	6	13.6
t0	8	8	8	13.8
t5anchor	14M	14M	14M	14.0
t7	2	2	2	14.2
✓ monotone
passed
✓ pitch
passed
✓ residual
passed
✓ cross-frame
passed
✓ anchor
passed

pitch 66.76 px · fit residual 0.45 px · shared tokens 9

Known blind spot: a consistent whole-metre misread passes all five checks, so a live run asks you to confirm the anchor crop before the reading is used.

Confirm the anchor
Spark reads 13M on token t1
Spark reads 14M on token t5

Anchor confirmed.

4
Step 4:
Draft
LIVE
done
12.4
12.6
12.8
13.0
13.2
frame 0
frame 59
12.761
± 0.0863 m
per-frame draft
running mean (band: illustrative, narrows to ± u)
swell p5–p95
DRAFT D
12.761 m
Repeatability u (k=1)
± 0.0863 m
Absolute u (k=1)
not stated — no ground truth
u parts
swell 0.0863 · random 0.0011
Frames kept
60 / 60
Dropped (reason)
none
Neff · lag-1 ρ
3.56 · 0.888
Swell p5–p95
12.563 – 13.052 m
One-pitch label shift
moves d by 0.20 m
5
Step 5:
Program
LIVE
done

The cached program that passed its booklet self-test (run run-booklet-only). Regeneration is not offered here.

Program author
muse-wonder-1.0
Response id
resp_6ae5a63a238297fff10f457e
sha256
4b3aa8cd94879978…
Regenerations
2
Self-test on the printed conditions

PASS
22/22 printed conditions
out-of-table probes refused 2/2
vs our reference program, 200 cases · max difference 7.1e-5 % · 0 failures

Re-run self-test live (sandbox, no API cost)
LIVE re-run just now · sandbox 59 ms · round trip 359 ms
Self-test: booklet printed displacement against the program output
Condition	Page	Printed t	Program t	Error %	Result	First diverging
1	101	11,244.1	11,244.7	0.0055	PASS	—
2.1	108	15,082.0	15,081.0	-0.0063	PASS	—
2.2	117	13,664.7	13,662.1	-0.0191	PASS	—
3.1	126	15,984.0	15,980.6	-0.0210	PASS	—
3.2	137	15,140.1	15,133.5	-0.0438	PASS	—
4.1	148	17,827.7	17,825.8	-0.0106	PASS	—
4.2	159	16,955.3	16,953.6	-0.0099	PASS	—
4.3	170	17,265.7	17,265.2	-0.0029	PASS	—
4.4	181	17,283.1	17,282.7	-0.0022	PASS	—
4.5	192	17,319.8	17,318.2	-0.0090	PASS	—
4.6	203	16,808.5	16,808.7	0.0011	PASS	—
5.1	214	17,035.4	17,034.3	-0.0066	PASS	—
5.2	225	15,650.9	15,649.4	-0.0097	PASS	—
6.1	236	17,057.4	17,057.1	-0.0020	PASS	—
6.2	247	15,673.0	15,670.9	-0.0136	PASS	—
7.1	258	16,516.9	16,517.7	0.0050	PASS	—
7.2	269	15,132.5	15,129.3	-0.0214	PASS	—
8.1	280	16,569.3	16,570.8	0.0089	PASS	—
8.2	291	15,184.8	15,182.5	-0.0148	PASS	—
9.1	302	16,785.0	16,782.3	-0.0158	PASS	—
9.2	313	15,400.6	15,391.4	-0.0599	PASS	—
10	324	11,959.1	11,958.0	-0.0092	PASS	—
How the program was earned
Attempt 1 · gate reject
Attempt 2 · 14/22
Attempt 3 · 22/22

PASS
22/22 printed conditions
differential max error 7.1e-5 %

0.89 min · $0.175 · 21912 tokens · resp_6ae5a63a238297fff10f457e · sha 4b3aa8cd9487…

Prompt = booklet pages + input drafts only (no standards hint). Attempt 1 rejected by the static gate, attempt 2 passed 14/22 (no second trim correction), attempt 3 passed 22/22 after feedback with failing cond ids + its own intermediates. A second run with a one-sentence UNECE hint (run-unece-hint/) passed 22/22 on attempt 1.

Proven program source (234 lines)
6
Step 6:
Survey + certificate
LIVE
Draft sheet
Fore P entered
Fore S entered
Mid P live
Mid S entered
Aft P entered
Aft S entered
Dock density 1.025 t/m³
Deductibles (t)
ballast
fw
fuel
other
Lightship + constant (t, optional)
Initial net (t, optional)
B/L figure (t)
Tolerance %
Certificate preview
REFUSE
OUT_OF_TABLE
matrix row 4

The draft is outside the vessel's hydrostatic table: the program refuses to extrapolate.

Draft sheet
Position	Draft m	Source	Weight	t per mm
Fore P	12.7610	entered	—	—
Fore S	12.7610	entered	—	—
Mid P	12.7605	live	—	—
Mid S	12.7610	entered	—	—
Aft P	12.7610	entered	—	—
Aft S	12.7610	entered	—	—

OutOfTable: mean draft outside hydrostatic table

live-mvx1wyzw · LIVE · proof: booklet

Open printable certificate
Tamper test

Edit this signed measurement the way a forger would: draft 12.761 m → 6.500 m on every mark, inside this booklet's table. Then send it to the same live endpoint.

Edit the signed draft and resubmit
MODEL CALLS THIS SESSION
sam-3.1 · 60 frames · 7.9 s · $0.012
sam-3.1 · 60 frames · 8.3 s · $0.012
muse-spark-1.3 · 2005 tok · 6.4 s · $0.0071
muse-spark-1.3 · 3533 tok · 11.2 s · $0.014
total $0.045
```

## Wonder's three attempts as station 5 shows them (tabs, from `data/programs/trieste/run-booklet-only/attempts.json`)

- Attempt 1: FAIL 0/22 printed conditions; static gate: line 230: name globals not allowed; line 255: name globals not allowed; line 260: name globals not allowed; 0.55 min, $0.161, `resp_6ae5a5f8ac84c849236c47d5`
- Attempt 2: FAIL 14/22 printed conditions; differential max error 0.6993 %; failing conditions and their first diverging intermediate: 2.2 -> corr_trim2, 3.1 -> corr_trim2, 3.2 -> corr_trim2, 6.2 -> corr_trim2, 7.2 -> corr_trim2, 8.2 -> corr_trim2, 9.1 -> corr_trim2, 9.2 -> corr_trim2; 0.55 min, $0.145, `resp_6ae5a6194a0590c4c3c04e31`
- Attempt 3: PASS 22/22 printed conditions; differential max error 7.101e-05 %; 0.89 min, $0.175, `resp_6ae5a63a238297fff10f457e`

## Printable certificate of the run (`/certificate?run=local`, verbatim)

```text
Skip to content
DRAFTMARK
Recorded runs
Evidence
Run it live →
Print / save as PDF

DRAFT SURVEY CERTIFICATE

Live run live-mvx1wyzw
LIVE
no scale truth
001
Identification
Run id
live-mvx1wyzw
Run mode
LIVE
Created
2026-10-31T23:49:13+0000
Vessel mode
ship
Proof kind
booklet · booklet — the survey program reproduced the stability booklet's printed conditions (no scale truth)
Measured on
upload · upload
Booklet
trieste
010
Decision
REFUSE
OUT_OF_TABLE
matrix row 4

The draft is outside the vessel's hydrostatic table: the program refuses to extrapolate.

020
Draft measurement
Draft d
12.761 m
Repeatability u (k=1)
± 0.0863 m
Absolute u (k=1)
not stated — no ground truth
u parts
swell 0.0863 · random 0.0011
Frames used
60 / 60
Neff · lag-1 ρ
3.56 · 0.888
Swell p5–p95
12.563 – 13.052 m
One-pitch label shift
moves d by 0.20 m
12.4
12.6
12.8
13.0
13.2
frame 0
frame 59
12.761
± 0.0863 m
per-frame draft
running mean (band: illustrative, narrows to ± u)
swell p5–p95
030
Mark labels

Read by muse-spark-1.3 · anchor confirmed by the user

✓ monotone
passed
✓ pitch
passed
✓ residual
passed
✓ cross-frame
passed
✓ anchor
passed
040
Survey
Draft sheet
Position	Draft m	Source	Weight	t per mm
Fore P	12.7610	entered	—	—
Fore S	12.7610	entered	—	—
Mid P	12.7605	live	—	—
Mid S	12.7610	entered	—	—
Aft P	12.7610	entered	—	—
Aft S	12.7610	entered	—	—

OutOfTable: mean draft outside hydrostatic table

Displacement, deductions, net and cargo are not printed: the decision is REFUSE (OUT_OF_TABLE).

050
Survey program
Program author
muse-wonder-1.0
Regenerations
2
Response id
resp_6ae5a63a238297fff10f457e
Program sha256
4b3aa8cd9487997861292e97…
Self-test verdict
PASS · 22/22 printed conditions · probes 2/2 · differential 200 cases, max 7.1e-5 %
060
Models

Called in this run: muse-spark-1.3 · sam-3.1 Measurement signed by this server's stations. Survey program author: muse-wonder-1.0.

CALLS IN THIS RUN
sam-3.1 · 60 frames · 7.9 s · $0.012
sam-3.1 · 60 frames · 8.3 s · $0.012
muse-spark-1.3 · 2005 tok · 6.4 s · $0.0071
muse-spark-1.3 · 3533 tok · 11.2 s · $0.014
total $0.045

live-mvx1wyzw · LIVE · proof: booklet

Prototype — not a surveyor's certificate.

Prototype — not a surveyor's certificate.
```
