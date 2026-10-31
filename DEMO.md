# DEMO: reproduce what the judges see

Everything below runs without a Meta key unless marked.

| Step | Do | Expect | Evidence |
|---|---|---|---|
| 1 | Open https://draftmark.edycu.dev | the landing replays the real dB7X waterline: 60 of 60 frames, draft 12.761 m, u_rep 0.086 m | [core-run-dB7X.md](evidence/core-run-dB7X.md) |
| 2 | Open [/runs](https://draftmark.edycu.dev/runs) | recorded runs (labelled "recorded"): dB7X and UKTRQ certify as `REFUSE OUT_OF_TABLE`; Trieste 4.1 gives 17825.8 t vs printed 17827.7 t; the synthetic barge is labelled synthetic | [core-run-trieste.md](evidence/core-run-trieste.md), [core-run-UKTRQ.md](evidence/core-run-UKTRQ.md) |
| 3 | Open [/survey](https://draftmark.edycu.dev/survey) and re-run the self-test | the survey program reproduces the booklet's printed conditions, 22/22 | [selftest-booklet.md](evidence/selftest-booklet.md) |
| 4 | Local tests: `python3 -m pytest -q` | 127 passed | `tests/` |
| 5 | Uploading your own clip (needs the judge code given in the submission notes, and `MODEL_API_KEY` locally) | measure, labels with five code checks, draft | [live-run-p1d.md](evidence/live-run-p1d.md) |

Limits: see the README's "Honest limits". Regenerating the Wonder program calls the Meta API and is logged with a
price-list cost estimate in [api-usage.md](evidence/api-usage.md).
