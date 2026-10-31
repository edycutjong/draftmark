# Computer use (P1a spike, rung A)

Rung A of the CU ladder: **Muse Wonder 1.0 plans** (strict-JSON filing plan, no tools; Wonder's own native `computer`
tool is rejected on our key) and **Muse Spark 1.3 acts** with its native `computer` tool in a real headless Chromium
(Playwright, 1280x800). Every Spark action carries `computer_action_requires_confirmation`; the harness
(`api/_core/cu.py`) acknowledges only on allowlisted hosts (our demo portal, read-only public pages) and stops
anywhere else. The portal is our own page `public/portal/index.html`, labelled "DEMO PORTAL — not a real
authority"; it shows back exactly what it received, and code compares that echo with the certificate.
Script: `scripts/spike_cu.py`, run 2026-10-31 locally (portal served from `public/`). Per-call rows: `evidence/api-usage.md` (run_id `p1a-cu`).

| Run | Host | Spark steps | Seconds | est $ | Outcome |
|---|---|---|---|---|---|
| File the certificate into the demo portal (Wonder plan response `resp_6ae5aa45c365f10a6d90450b`) | 127.0.0.1 (demo portal) | 11 | 148.6 | 0.070 | read-back 6/6 fields match |
| Fault injection: harness types cargo + 1 t | 127.0.0.1 (demo portal) | 0 (harness) | - | 0 | read-back REJECTS (cargo mismatch) as required |
| Read-only lookup: gross tonnage + length in a Wikipedia infobox | en.wikipedia.org | 1 | 15.8 | 0.009 | "220,940 GT, 399.94 m (1,312 ft 2 in)" (matches the article) |
| Off-allowlist guard: asked to click a link on example.com | example.com | 1 | - | 0.006 | stopped: confirmation requested on non-allowlisted host example.com |

## Read-back of the filing

| field | certificate (code) | portal received | match |
|---|---|---|---|
| vessel | TRIESTE BOOKLET TEST SHIP (cond 4.1) | TRIESTE BOOKLET TEST SHIP (cond 4.1) | yes |
| survey_date | 2026-10-31 | 2026-10-31 | yes |
| displacement | 17825.8 | 17825.8 | yes |
| cargo | 6581.8 | 6581.8 | yes |
| uncertainty | 37.4 | 37.4 | yes |
| decision | ISSUE | ISSUE | yes |

The certificate here is a spike fixture computed by code (Trieste condition 4.1 inputs through the reference
program; cargo = displacement - the booklet's lightship weight 11 244.06 t; ± from ±10 mm on every mark). It is not a
survey of a real ship.

## Decision (CU ladder, rule 16)
**Rung A** (Spark 1.3 native CU sub-agent, Wonder plans and checks) is proven locally. CU is Tier 3: it is wired into
the app only after Tiers 1-2 are green; the default filing path stays a direct POST to the portal, and CU never
blocks the certificate. The deployed path (Node function + `@sparticuz/chromium`) is not yet probed; if it does not
fit Vercel Hobby, the site shows this recorded run (labelled) and DEMO.md documents the local live path.
