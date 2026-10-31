# Deployed-runtime probes (P1a, 2026-10-31)

Production deployment of the scaffold on Vercel Hobby (`https://draftmark.edycu.dev`, Python 3.12.15 on
Linux x86_64 / Amazon Linux 2, glibc 2.34). Endpoints: `GET /api/py/probe/sandbox`, `GET /api/py/probe/sleep?s=N`,
`GET /api/probe/cache` (Node). No Meta API cost.

| Probe | Result | Decision |
|---|---|---|
| Subprocess sandbox launch (`python -I -S runner.py`, empty env, temp dir) | OK, 48 ms | live self-test re-run and survey run Wonder's program in the sandbox on Vercel (no in-process fallback needed) |
| RLIMIT_CPU (1 s) on an infinite loop | killed (`exit -9`) after ~1.4 s wall | kept (5 s in production) |
| RLIMIT_AS 256 MB on a 3.2 GB allocation | blocked (`MemoryError`) | kept; note: macOS ignores RLIMIT_AS, so this limit is only proven on Linux |
| Audit hook refuses `open()` outside the temp dir | blocked (`RuntimeError: blocked open: /etc/hostname`) | kept |
| RLIMIT_NPROC = 0 in the child | child still launches and runs | kept (README states defense in depth, not a hard boundary) |
| `maxDuration` (vercel.json 300 s) | a 290 s request and a concurrent 70 s request both returned 200 | long steps fit; Wonder generation still uses background + polling (no blocking call) |
| Vercel Runtime Cache from a Node function | works on Hobby: counter 0 -> 1 -> 2 across requests | per-IP / LIVE_WONDER_MAX counters can use Runtime Cache (still not a global hard cap: per region, evictable) |

## Meta API format/latency probes (local, recorded in `evidence/api-usage.md`)
| Probe | Result | Decision |
|---|---|---|
| SAM 3.1 video with `video/webm` | HTTP 400 "unsupported media type ... Supported: MP4" | uploads accept MP4 only (MediaRecorder MP4 where the browser supports it; otherwise uploads are disabled) |
| SAM 3.1 video, 60 frames MP4 (2x crop) | 9.4-13.0 s per concept (4 calls) | two concepts run concurrently; a 60-frame measure fits well inside maxDuration |
| `background: true` on muse-wonder-1.0 | accepted; submit returns `queued`, poll completes in 33-53 s | live "Regenerate" can use background + polling |
| Prompt caching on Wonder regenerations | automatic: 12 404 of 13 483 input tokens cached on attempt 3 | the booklet excerpt is billed at the cached rate on regenerations |

Not yet probed (needs P1b code and our own fixture clip): p95 of the deployed `/api/py/measure` on a 60-frame fixture
from a clean browser.
