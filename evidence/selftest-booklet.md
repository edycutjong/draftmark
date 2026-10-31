# Wonder's Trieste survey program: self-test against the booklet's printed conditions

Booklet: public Trieste trim & stability booklet (Ro-Ro/passenger ship, Lpp 150 m; NOT a bulk carrier).
There is no scale truth here: the check is that a program reproduces the displacements the booklet itself
PRINTS for its 22 worked loading conditions (`data/booklets/trieste/conditions.csv`, verified row by row,
see `data/booklets/trieste/CITATION.md`).

**Pass rule (pre-set in the spec):** a row passes if |program - printed| / printed <= 0.1 %. Verdict PASS only if
>= ceil(0.9 N) = 20 of N = 22 rows pass, both out-of-range probes raise, and 200 randomized cases agree
with our reference program within 0.05 %. Every program runs in the sandbox (`api/_core/sandbox.py`: AST gate,
`python -I -S` subprocess, rlimits, audit hook).

## Result

- **Default proven program:** `data/programs/trieste/run-booklet-only/program.py` by muse-wonder-1.0, sha256 `4b3aa8cd94879978…`, response `resp_6ae5a63a238297fff10f457e`, regenerations 2: **22 of 22 printed conditions**, probes raised [True, True], differential 200 cases max 0.00007 %, verdict **PASS**.
- Our reference program (`api/_core/reference_survey.py`, written before Wonder was called): 22 of 22.
- The booklet's §3.1 procedure applied verbatim (no second trim correction): 14 of 22.
- A generic textbook template that does not read this booklet's conventions (`scripts/baseline_generic.py`): 0 of 22; first diverging intermediate `d_fp` on every row.

## What the booklet hides (and Wonder found)
- Lpp = 150 m, but the mark formulas divide by 140 (the distance between the draft marks).
- LCF is measured from the AP; the table's MTcm column is per DEGREE (heading) though the legend says per cm.
- §3.1 omits the second (Nemoto) trim correction; without it the high-trim rows miss by up to 0.38 %.

## Wonder runs (both real, both kept)

### Run A: booklet pages only (the default proven program)

Prompt manifest: bundle sha256 `bb96e5d1ae1e658e…`, system prompt sha256 `c9f658a8ff0cb0c9…`, pages [4, 21, 22, 26, 36, 37, 38, 39]; no printed displacement string found in the bundle.

| attempt | response id | minutes | tokens in / out | est $ | outcome | rows | probes raised | differential max % |
|---|---|---|---|---|---|---|---|---|
| 1 | `resp_6ae5a5f8ac84c849236c47d5` | 0.55 | 12428 / 5554 | 0.161 | static gate REJECTED | - | - | - |
|  | | | | | `static gate: line 230: name globals not allowed; line 255: name globals not allowed; line 260: name globals not allowed` | | | |
| 2 | `resp_6ae5a6194a0590c4c3c04e31` | 0.55 | 12535 / 4738 | 0.145 | FAIL | 14/22 | [True, True] | 0.69930 |
|  | | | | | failing (cond, first diverging intermediate): 2.2 corr_trim2, 3.1 corr_trim2, 3.2 corr_trim2, 6.2 corr_trim2, 7.2 corr_trim2, 8.2 corr_trim2, 9.1 corr_trim2, 9.2 corr_trim2 | | | |
| 3 | `resp_6ae5a63a238297fff10f457e` | 0.89 | 13483 / 8429 | 0.175 | PASS | 22/22 | [True, True] | 0.00007 |

Run total: 3 Wonder calls, est $0.481.

Regeneration feedback gave Wonder only the failing condition ids and its OWN intermediates; the printed displacements were never in its context (asserted on the prompt bundle before every run), nor was our reference program.

### Run B: same prompt plus one sentence: "where the booklet's procedure is incomplete compared with standard draught-survey practice (UNECE code), apply the standard practice"

Prompt manifest: bundle sha256 `bb96e5d1ae1e658e…`, system prompt sha256 `7469ed1fb7527abd…`, pages [4, 21, 22, 26, 36, 37, 38, 39]; no printed displacement string found in the bundle.

| attempt | response id | minutes | tokens in / out | est $ | outcome | rows | probes raised | differential max % |
|---|---|---|---|---|---|---|---|---|
| 1 | `resp_6ae5a597b8e919c19664401e` | 0.89 | 12469 / 7477 | 0.199 | PASS | 22/22 | [True, True] | 0.00000 |

Run total: 1 Wonder calls, est $0.199.

## Rows of the default proven program

| cond | page | printed (t) | Wonder program (t) | err % | pass |
|---|---|---|---|---|---|
| 1 | 101 | 11244.1 | 11244.7 | +0.0055 | yes |
| 2.1 | 108 | 15082.0 | 15081.0 | -0.0063 | yes |
| 2.2 | 117 | 13664.7 | 13662.1 | -0.0191 | yes |
| 3.1 | 126 | 15984.0 | 15980.6 | -0.0210 | yes |
| 3.2 | 137 | 15140.1 | 15133.5 | -0.0438 | yes |
| 4.1 | 148 | 17827.7 | 17825.8 | -0.0106 | yes |
| 4.2 | 159 | 16955.3 | 16953.6 | -0.0099 | yes |
| 4.3 | 170 | 17265.7 | 17265.2 | -0.0029 | yes |
| 4.4 | 181 | 17283.1 | 17282.7 | -0.0022 | yes |
| 4.5 | 192 | 17319.8 | 17318.2 | -0.0090 | yes |
| 4.6 | 203 | 16808.5 | 16808.7 | +0.0011 | yes |
| 5.1 | 214 | 17035.4 | 17034.3 | -0.0066 | yes |
| 5.2 | 225 | 15650.9 | 15649.4 | -0.0097 | yes |
| 6.1 | 236 | 17057.4 | 17057.1 | -0.0020 | yes |
| 6.2 | 247 | 15673.0 | 15670.9 | -0.0136 | yes |
| 7.1 | 258 | 16516.9 | 16517.7 | +0.0050 | yes |
| 7.2 | 269 | 15132.5 | 15129.3 | -0.0214 | yes |
| 8.1 | 280 | 16569.3 | 16570.8 | +0.0089 | yes |
| 8.2 | 291 | 15184.8 | 15182.5 | -0.0148 | yes |
| 9.1 | 302 | 16785.0 | 16782.3 | -0.0158 | yes |
| 9.2 | 313 | 15400.6 | 15391.4 | -0.0599 | yes |
| 10 | 324 | 11959.1 | 11958.0 | -0.0092 | yes |

## Reference and booklet-verbatim, row by row

| cond | page | printed disp (t) | reference (t) | err % | booklet-verbatim (t) | err % |
|---|---|---|---|---|---|---|
| 1 | 101 | 11244.1 | 11244.7 | +0.006 | 11244.0 | -0.001 |
| 2.1 | 108 | 15082.0 | 15081.0 | -0.006 | 15071.8 | -0.068 |
| 2.2 | 117 | 13664.7 | 13662.1 | -0.019 | 13638.3 | -0.193 |
| 3.1 | 126 | 15984.0 | 15980.6 | -0.021 | 15951.6 | -0.203 |
| 3.2 | 137 | 15140.1 | 15133.5 | -0.044 | 15093.2 | -0.310 |
| 4.1 | 148 | 17827.7 | 17825.8 | -0.011 | 17816.0 | -0.066 |
| 4.2 | 159 | 16955.3 | 16953.6 | -0.010 | 16942.0 | -0.078 |
| 4.3 | 170 | 17265.7 | 17265.2 | -0.003 | 17256.7 | -0.052 |
| 4.4 | 181 | 17283.1 | 17282.7 | -0.002 | 17274.6 | -0.049 |
| 4.5 | 192 | 17319.8 | 17318.2 | -0.009 | 17312.1 | -0.045 |
| 4.6 | 203 | 16808.5 | 16808.7 | +0.001 | 16792.0 | -0.098 |
| 5.1 | 214 | 17035.4 | 17034.3 | -0.007 | 17033.6 | -0.011 |
| 5.2 | 225 | 15650.9 | 15649.4 | -0.010 | 15642.3 | -0.055 |
| 6.1 | 236 | 17057.4 | 17057.1 | -0.002 | 17053.4 | -0.024 |
| 6.2 | 247 | 15673.0 | 15670.9 | -0.014 | 15657.0 | -0.102 |
| 7.1 | 258 | 16516.9 | 16517.7 | +0.005 | 16508.0 | -0.054 |
| 7.2 | 269 | 15132.5 | 15129.3 | -0.021 | 15105.2 | -0.181 |
| 8.1 | 280 | 16569.3 | 16570.8 | +0.009 | 16565.7 | -0.022 |
| 8.2 | 291 | 15184.8 | 15182.5 | -0.015 | 15166.1 | -0.123 |
| 9.1 | 302 | 16785.0 | 16782.3 | -0.016 | 16755.4 | -0.176 |
| 9.2 | 313 | 15400.6 | 15391.4 | -0.060 | 15342.3 | -0.378 |
| 10 | 324 | 11959.1 | 11958.0 | -0.009 | 11957.9 | -0.010 |

Spend for the Wonder program-writing spike: est $0.680 (price-list estimate; rows in `evidence/api-usage.md`). Raw booklet page text is not committed (licence unstated); only its hashes.
