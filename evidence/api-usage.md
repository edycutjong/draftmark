# Meta API usage ledger

Price-list estimates from `api/_core/meta.py` PRICES (not an invoice). Appended by the scripts; rule-5 budget: whole chain <= $40, dev cap $30 enforced by `ledger_total()`.

| ts (WIB) | run_id | model | feature | tokens in (cached) / out · frames | est_usd | latency_ms | response_id |
|---|---|---|---|---|---|---|---|
| 2026-10-31 13:52 | p0b-review-r1 | muse-wonder-1.0 | outside spec review r1 (reasoning high, no tools; folded from the kitchen ledger, token counts estimated) | ~15k / ~5-10k | 0.2500 |  |  |
| 2026-10-31 14:31 | p0b-review-r2 | muse-wonder-1.0 | outside spec review r2 (same) | ~20k / ~5-10k | 0.3000 |  |  |
| 2026-10-31 14:58 | p0b-review-r3 | muse-wonder-1.0 | outside spec review r3 (same) | ~25k / ~5-10k | 0.3000 |  |  |
| 2026-10-31 15:12 | p1a-sam-dB7X_t45 | sam-3.1 | sam video 'water' dB7X_t45 | 0 (0) / 0 · 60 frames | 0.0120 | 9400 | resp_6ae5a2df14326830e40e4f09 |
| 2026-10-31 15:12 | p1a-sam-dB7X_t45 | sam-3.1 | sam video 'white number' dB7X_t45 | 0 (0) / 0 · 60 frames | 0.0120 | 10680 | resp_6ae5a2e129ecc46a137b48cf |
| 2026-10-31 15:14 | p1a-labels-dB7X_t45 | muse-spark-1.3 | spark labels dB7X_t45 f0 | 462 (0) / 1609 | 0.0074 | 6209 | resp_6ae5a35a5b65e7c27d6f4266 |
| 2026-10-31 15:14 | p1a-labels-dB7X_t45 | muse-spark-1.3 | spark labels dB7X_t45 f10 | 462 (0) / 3607 | 0.0159 | 13480 | resp_6ae5a368c6f0d68b80e04733 |
| 2026-10-31 15:15 | p1a-sam-UKTRQ_t20 | sam-3.1 | sam video 'water' UKTRQ_t20 | 0 (0) / 0 · 48 frames | 0.0096 | 4770 | resp_6ae5a3b8be4bd9e1214d4847 |
| 2026-10-31 15:15 | p1a-sam-UKTRQ_t20 | sam-3.1 | sam video 'white number' UKTRQ_t20 | 0 (0) / 0 · 48 frames | 0.0096 | 8474 | resp_6ae5a3bb6774fd9c39f64963 |
| 2026-10-31 15:16 | p1a-labels-UKTRQ_t20 | muse-spark-1.3 | spark labels UKTRQ_t20 f17 | 329 (0) / 1562 | 0.0070 | 7274 | resp_6ae5a3e21d109189159046ce |
| 2026-10-31 15:17 | p1a-labels-UKTRQ_t20 | muse-spark-1.3 | spark labels UKTRQ_t20 f29 | 329 (0) / 12830 | 0.0549 | 44480 | resp_6ae5a40fc6a2ce1e5eeb4145 |
| 2026-10-31 15:17 | p1a-sam-eeLL_t8 | sam-3.1 | sam video 'white number' eeLL_t8 | 0 (0) / 0 · 48 frames | 0.0096 | 6925 | resp_6ae5a414da5d51cf99b648f9 |
| 2026-10-31 15:17 | p1a-sam-eeLL_t8 | sam-3.1 | sam video 'water' eeLL_t8 | 0 (0) / 0 · 48 frames | 0.0096 | 9411 | resp_6ae5a414e7f5487223cb4837 |
| 2026-10-31 15:18 | p1a-labels-eeLL_t8 | muse-spark-1.3 | spark labels eeLL_t8 f2 | 361 (0) / 4330 | 0.0189 | 18519 | resp_6ae5a453d1c511066b5a4323 |
| 2026-10-31 15:19 | p1a-labels-eeLL_t8 | muse-spark-1.3 | spark labels eeLL_t8 f45 | 361 (89) / 13817 | 0.0591 | 51584 | resp_6ae5a4863a9e61b887f7410c |
| 2026-10-31 15:23 | p1a-wonder-trieste | muse-wonder-1.0 | wonder program trieste attempt 1 (submit) |  | 0.0000 | 1903 | resp_6ae5a597b8e919c19664401e |
| 2026-10-31 15:24 | p1a-wonder-trieste | muse-wonder-1.0 | wonder program trieste attempt 1 | 12469 (0) / 7477 | 0.1994 | 51285 | resp_6ae5a597b8e919c19664401e |
| 2026-10-31 15:25 | p1a-wonder-trieste | muse-wonder-1.0 | wonder program trieste attempt 1 (submit) |  | 0.0000 | 1560 | resp_6ae5a5f8ac84c849236c47d5 |
| 2026-10-31 15:26 | p1a-wonder-trieste | muse-wonder-1.0 | wonder program trieste attempt 1 | 12428 (0) / 5554 | 0.1608 | 31254 | resp_6ae5a5f8ac84c849236c47d5 |
| 2026-10-31 15:26 | p1a-wonder-trieste | muse-wonder-1.0 | wonder program trieste attempt 2 (submit) |  | 0.0000 | 1401 | resp_6ae5a6194a0590c4c3c04e31 |
| 2026-10-31 15:26 | p1a-wonder-trieste | muse-wonder-1.0 | wonder program trieste attempt 2 | 12535 (0) / 4738 | 0.1449 | 31384 | resp_6ae5a6194a0590c4c3c04e31 |
| 2026-10-31 15:26 | p1a-wonder-trieste | muse-wonder-1.0 | wonder program trieste attempt 3 (submit) |  | 0.0000 | 1454 | resp_6ae5a63a238297fff10f457e |
| 2026-10-31 15:27 | p1a-wonder-trieste | muse-wonder-1.0 | wonder program trieste attempt 3 | 13483 (12404) / 8429 | 0.1754 | 51918 | resp_6ae5a63a238297fff10f457e |
| 2026-10-31 15:38 | p1a-sam-synth_s1 | sam-3.1 | sam video 'water' synth_s1 | 0 (0) / 0 · 60 frames | 0.0120 | 6011 | resp_6ae5a91f75673c5617e8424b |
| 2026-10-31 15:38 | p1a-sam-synth_s1 | sam-3.1 | sam video 'white number' synth_s1 | 0 (0) / 0 · 60 frames | 0.0120 | 7235 | resp_6ae5a91e2b8696127929439a |
| 2026-10-31 15:39 | p1a-synth-concepts | sam-3.1 | sam image 'water' synthetic probe | 0 (0) / 0 · 1 frames | 0.0025 | 1563 | resp_6ae5a9328fe6722087a54213 |
| 2026-10-31 15:39 | p1a-synth-concepts | sam-3.1 | sam image 'sea water' synthetic probe | 0 (0) / 0 · 1 frames | 0.0025 | 1800 | resp_6ae5a934541527be040c4bdf |
| 2026-10-31 15:39 | p1a-synth-concepts | sam-3.1 | sam image 'water surface' synthetic probe | 0 (0) / 0 · 1 frames | 0.0025 | 1721 | resp_6ae5a93552b1d863e3174523 |
| 2026-10-31 15:39 | p1a-synth-concepts | sam-3.1 | sam image 'green water' synthetic probe | 0 (0) / 0 · 1 frames | 0.0025 | 1086 | resp_6ae5a937a00d0bd80eeb411d |
| 2026-10-31 15:39 | p1a-synth-concepts | sam-3.1 | sam image 'water' synthetic murky | 0 (0) / 0 · 1 frames | 0.0025 | 1662 | resp_6ae5a948d70d21fc720c4da9 |
| 2026-10-31 15:39 | p1a-synth-concepts | sam-3.1 | sam image 'water' synthetic blue | 0 (0) / 0 · 1 frames | 0.0025 | 1232 | resp_6ae5a949bf32691df401459e |
| 2026-10-31 15:39 | p1a-probe-webm | sam-3.1 | sam video 'white number' synthetic mp4 probe | 0 (0) / 0 · 60 frames | 0.0120 | 7200 | resp_6ae5a95819b4830a46f746da |
| 2026-10-31 15:43 | p1a-cu | muse-wonder-1.0 | wonder filing plan | 175 (0) / 511 | 0.0109 | 4003 | resp_6ae5aa45c365f10a6d90450b |
| 2026-10-31 15:43 | p1a-cu | muse-spark-1.3 | spark computer-use step 0 | 3576 (0) / 596 | 0.0070 | 6081 | resp_6ae5aa4878c1fa889eb1434b |
| 2026-10-31 15:44 | p1a-cu | muse-spark-1.3 | spark computer-use step 1 | 3292 (0) / 137 | 0.0047 | 8191 | resp_6ae5aa5128f21f96a31546db |
| 2026-10-31 15:44 | p1a-cu | muse-spark-1.3 | spark computer-use step 2 | 4719 (3265) / 97 | 0.0027 | 9985 | resp_6ae5aa5c126a9811063c4162 |
| 2026-10-31 15:44 | p1a-cu | muse-spark-1.3 | spark computer-use step 3 | 6106 (4673) / 176 | 0.0032 | 10037 | resp_6ae5aa66ce84280faaee4d89 |
| 2026-10-31 15:44 | p1a-cu | muse-spark-1.3 | spark computer-use step 4 | 7572 (6081) / 98 | 0.0032 | 10729 | resp_6ae5aa7235bf40930bee4085 |
| 2026-10-31 15:44 | p1a-cu | muse-spark-1.3 | spark computer-use step 5 | 8960 (0) / 193 | 0.0120 | 11846 | resp_6ae5aa7fd600897d2e0a4cb0 |
| 2026-10-31 15:45 | p1a-cu | muse-spark-1.3 | spark computer-use step 6 | 10443 (7489) / 214 | 0.0057 | 14047 | resp_6ae5aa8eec5c29b67414482b |
| 2026-10-31 15:45 | p1a-cu | muse-spark-1.3 | spark computer-use step 7 | 11947 (10433) / 211 | 0.0044 | 12037 | resp_6ae5aaa0287238449ffa4455 |
| 2026-10-31 15:45 | p1a-cu | muse-spark-1.3 | spark computer-use step 8 | 13448 (11841) / 310 | 0.0051 | 14415 | resp_6ae5aaaeaaaf18b27b0b482f |
| 2026-10-31 15:45 | p1a-cu | muse-spark-1.3 | spark computer-use step 9 | 15048 (8897) / 259 | 0.0101 | 11655 | resp_6ae5aabc099b2f9f53cb4a6d |
| 2026-10-31 15:46 | p1a-cu | muse-spark-1.3 | spark computer-use step 10 | 16597 (13377) / 132 | 0.0066 | 10611 | resp_6ae5aac83e71bfedf8e645d9 |
| 2026-10-31 15:46 | p1a-cu | muse-spark-1.3 | spark computer-use step 11 | 18019 (16577) / 110 | 0.0048 | 12330 | resp_6ae5aad6fd5c5a249a3547af |
| 2026-10-31 15:46 | p1a-cu | muse-spark-1.3 | spark computer-use step 0 | 3468 (0) / 209 | 0.0052 | 5270 | resp_6ae5aaddf681c335234c43a7 |
| 2026-10-31 15:46 | p1a-cu | muse-spark-1.3 | spark computer-use step 1 | 2797 (0) / 102 | 0.0039 | 9430 | resp_6ae5aae61c5451215a11465c |
| 2026-10-31 15:46 | p1a-cu | muse-spark-1.3 | spark computer-use step 0 | 3451 (0) / 304 | 0.0056 | 4758 | resp_6ae5aaee48a10393c2aa4696 |
| 2026-10-31 16:07 | rec-db7x-20261031 | sam-3.1 | sam video 'white number' upload | 0 (0) / 0 · 60 frames | 0.0120 | 6858 | resp_6ae5afc5eaf19a98130b4b2d |
| 2026-10-31 16:07 | rec-db7x-20261031 | sam-3.1 | sam video 'water' upload | 0 (0) / 0 · 60 frames | 0.0120 | 8196 | resp_6ae5afc6a737472e198542a8 |
| 2026-10-31 16:07 | rec-db7x-20261031 | muse-spark-1.3 | spark labels f0 try 1 | 462 (0) / 947 | 0.0046 | 4772 | resp_6ae5afdecc5b13667f374d5e |
| 2026-10-31 16:07 | rec-db7x-20261031 | muse-spark-1.3 | spark labels f10 try 1 | 462 (0) / 2468 | 0.0111 | 9766 | resp_6ae5afe8bf4fcf96229347a0 |
| 2026-10-31 16:08 | rec-uktrq-20261031 | sam-3.1 | sam video 'white number' upload | 0 (0) / 0 · 48 frames | 0.0096 | 7436 | resp_6ae5aff3a1dd4facbd3f4669 |
| 2026-10-31 16:08 | rec-uktrq-20261031 | sam-3.1 | sam video 'water' upload | 0 (0) / 0 · 48 frames | 0.0096 | 7815 | resp_6ae5aff313ac34f042304dee |
| 2026-10-31 16:08 | rec-uktrq-20261031 | muse-spark-1.3 | spark labels f17 try 1 | 329 (0) / 1558 | 0.0070 | 6568 | resp_6ae5b00343caa8de0c3548cb |
| 2026-10-31 16:08 | rec-uktrq-20261031 | muse-spark-1.3 | spark labels f29 try 1 | 329 (0) / 11603 | 0.0497 | 39396 | resp_6ae5b02b599a1c9ed28d4118 |
