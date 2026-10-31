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
| 2026-10-31 09:55 | live-probe-p1c | sam-3.1 | sam video 'white number' upload | 0 (0) / 0 · 60 frames | 0.0120 | 6319 | resp_6ae5bafe3dec643fa3c6482c |
| 2026-10-31 09:55 | live-probe-p1c | sam-3.1 | sam video 'water' upload | 0 (0) / 0 · 60 frames | 0.0120 | 8677 | resp_6ae5baff4742a84a974a41b9 |
| 2026-10-31 09:58 | live-probe-p1c | muse-spark-1.3 | spark labels f0 try 1 | 462 (0) / 1511 | 0.0070 | 7187 | resp_6ae5bbaf16399a729fff46fc |
| 2026-10-31 09:58 | live-probe-p1c | muse-spark-1.3 | spark labels f10 try 1 | 462 (0) / 2310 | 0.0104 | 11144 | resp_6ae5bbb4ff1d25a7c7f84de6 |
| 2026-10-31 11:28 | live-p1d-1793446130 | sam-3.1 | sam video 'water' upload | 0 (0) / 0 · 60 frames | 0.0120 | 5443 | resp_6ae5d0f8a3ddef2f3c56436e |
| 2026-10-31 11:28 | live-p1d-1793446130 | sam-3.1 | sam video 'white number' upload | 0 (0) / 0 · 60 frames | 0.0120 | 6386 | resp_6ae5d0f868684f14ecbd40a9 |
| 2026-10-31 11:29 | live-p1d-1793446130 | muse-spark-1.3 | spark labels f0 try 1 | 462 (0) / 880 | 0.0043 | 2983 | resp_6ae5d12a9ca6989f37164fcf |
| 2026-10-31 11:29 | live-p1d-1793446130 | muse-spark-1.3 | spark labels f10 try 1 | 462 (0) / 2938 | 0.0131 | 13446 | resp_6ae5d133bcf4e867510c4478 |
| 2026-10-31 18:20 | p1d-review-r1 | muse-wonder-1.0 | outside architecture review r1 (reasoning high, no tools; ~157k-char packet; token counts estimated) | ~45k / ~10-15k | 0.4500 |  |  |
| 2026-10-31 19:06 | p1d-review-r2a | muse-wonder-1.0 | outside architecture review r2 (reasoning high; EMPTY — all 16k output tokens spent reasoning; estimated) | ~50k / 16k | 0.5200 |  |  |
| 2026-10-31 19:09 | p1d-review-r2b | muse-wonder-1.0 | outside architecture review r2 re-run (reasoning medium, no tools; estimated) | ~50k / ~5-10k | 0.3500 |  |  |
| 2026-10-31 19:48 | p1d-review-r3a | muse-wonder-1.0 | outside architecture review r3 (reasoning medium; EMPTY — max_output_tokens; estimated) | ~52k / 16k | 0.5300 |  |  |
| 2026-10-31 19:57 | p1d-review-r3b | muse-wonder-1.0 | outside architecture review r3 re-run on the slim packet (reasoning low, no tools; estimated) | ~28k / ~4k | 0.2000 |  |  |
| 2026-10-31 13:01 | live-p1d-1793451671 | sam-3.1 | sam video 'water' upload | 0 (0) / 0 · 60 frames | 0.0120 | 6052 | resp_6ae5e69d37a25da88506485c |
| 2026-10-31 13:01 | live-p1d-1793451671 | sam-3.1 | sam video 'white number' upload | 0 (0) / 0 · 60 frames | 0.0120 | 17142 | resp_6ae5e69fc2eec0d2028743a3 |
| 2026-10-31 13:02 | live-p1d-1793451671 | muse-spark-1.3 | spark labels f0 try 1 | 462 (0) / 1402 | 0.0065 | 6190 | resp_6ae5e6d979e05de4a16d4ada |
| 2026-10-31 13:02 | live-p1d-1793451671 | muse-spark-1.3 | spark labels f10 try 1 | 462 (0) / 2285 | 0.0103 | 10811 | resp_6ae5e6def11021bc8f184e39 |
| 2026-11-01 01:01 | eval-synth-07 | sam-3.1 | sam video 'water' upload | 0 (0) / 0 · 60 frames | 0.0120 | 5055 | resp_6ae62cddc1ce7c41cb154f5b |
| 2026-11-01 01:01 | eval-synth-07 | sam-3.1 | sam video 'white number' upload | 0 (0) / 0 · 60 frames | 0.0120 | 8589 | resp_6ae62cddba684ac3f98e4c0c |
| 2026-11-01 01:02 | eval-synth-07 | sam-3.1 | sam video 'white number' synth load 7 | 0 (0) / 0 · 60 frames | 0.0120 | 8916 | resp_6ae62d3f027c62f3a1d34dba |
| 2026-11-01 01:02 | eval-synth-07 | sam-3.1 | sam video 'water' synth load 7 | 0 (0) / 0 · 60 frames | 0.0120 | 4113 | resp_6ae62d461c877e3c72a041c5 |
| 2026-11-01 01:02 | eval-synth-07 | muse-spark-1.3 | spark labels f2 try 1 | 396 (0) / 922 | 0.0044 | 6933 | resp_6ae62d52c75cecc44cc342b8 |
| 2026-11-01 01:03 | eval-synth-07 | muse-spark-1.3 | spark labels f9 try 1 | 396 (114) / 2815 | 0.0123 | 15515 | resp_6ae62d5b7f1190a2cc794db2 |
| 2026-11-01 01:03 | eval-synth-07 | muse-spark-1.3 | spark labels f9 try 2 | 428 (0) / 3364 | 0.0148 | 15039 | resp_6ae62d6a874b4069fab6404e |
| 2026-11-01 01:03 | eval-synth-07 | muse-spark-1.3 | spark labels f2 try 2 | 428 (0) / 7510 | 0.0325 | 33739 | resp_6ae62d7cac6bf38e811046c5 |
| 2026-11-01 01:04 | eval-synth-07 | sam-3.1 | sam video 'white number' synth load 7 | 0 (0) / 0 · 60 frames | 0.0120 | 8314 | resp_6ae62dc6e812dfa608ac48df |
| 2026-11-01 01:05 | eval-synth-07 | sam-3.1 | sam video 'water' synth load 7 | 0 (0) / 0 · 60 frames | 0.0120 | 3591 | resp_6ae62dcc256e87fdd9844e0a |
| 2026-11-01 01:05 | eval-synth-07 | muse-spark-1.3 | spark labels f2 try 1 | 396 (0) / 1691 | 0.0077 | 9477 | resp_6ae62ddae3b6999e962042c6 |
| 2026-11-01 01:05 | eval-synth-07 | muse-spark-1.3 | spark labels f9 try 1 | 396 (0) / 2965 | 0.0131 | 13511 | resp_6ae62dde28865a02904940c5 |
| 2026-11-01 01:05 | eval-synth-07 | sam-3.1 | sam video 'white number' synth load 7 | 0 (0) / 0 · 60 frames | 0.0120 | 6042 | resp_6ae62df1b0eb354a44834626 |
| 2026-11-01 01:05 | eval-synth-07 | sam-3.1 | sam video 'water' synth load 7 | 0 (0) / 0 · 60 frames | 0.0120 | 5602 | resp_6ae62df81831027918bb461c |
| 2026-11-01 01:05 | eval-synth-07 | muse-spark-1.3 | spark labels f2 try 1 | 396 (0) / 2068 | 0.0093 | 10207 | resp_6ae62e06800f4cd928974c49 |
| 2026-11-01 01:06 | eval-synth-07 | muse-spark-1.3 | spark labels f9 try 1 | 396 (370) / 4116 | 0.0176 | 18584 | resp_6ae62e0f8e91b3fad7534c8b |
| 2026-11-01 01:06 | eval-synth-07 | sam-3.1 | sam video 'white number' synth load 7 | 0 (0) / 0 · 60 frames | 0.0120 | 9166 | resp_6ae62e205b9593422c0e4324 |
| 2026-11-01 01:06 | eval-synth-07 | sam-3.1 | sam video 'water' synth load 7 | 0 (0) / 0 · 60 frames | 0.0120 | 5170 | resp_6ae62e26ef8d77e714d74500 |
| 2026-11-01 01:06 | eval-synth-07 | muse-spark-1.3 | spark labels f9 try 1 | 396 (370) / 1518 | 0.0065 | 9156 | resp_6ae62e35d3c181758c3b486c |
| 2026-11-01 01:06 | eval-synth-07 | muse-spark-1.3 | spark labels f2 try 1 | 396 (370) / 2017 | 0.0087 | 10347 | resp_6ae62e363631bfd614824ec4 |
| 2026-11-01 01:07 | eval-synth-01 | sam-3.1 | sam video 'white number' synth load 1 | 0 (0) / 0 · 60 frames | 0.0120 | 8306 | resp_6ae62e55c9e79dd876834a54 |
| 2026-11-01 01:07 | eval-synth-01 | sam-3.1 | sam video 'water' synth load 1 | 0 (0) / 0 · 60 frames | 0.0120 | 4431 | resp_6ae62e5bc1634559788c4b4d |
| 2026-11-01 01:07 | eval-synth-01 | muse-spark-1.3 | spark labels f6 try 1 | 396 (114) / 2345 | 0.0103 | 12451 | resp_6ae62e6dffd127c8b0654645 |
| 2026-11-01 01:07 | eval-synth-01 | muse-spark-1.3 | spark labels f0 try 1 | 396 (114) / 1204 | 0.0055 | 12950 | resp_6ae62e6df955390205e244e3 |
| 2026-11-01 01:07 | eval-synth-02 | sam-3.1 | sam video 'white number' synth load 2 | 0 (0) / 0 · 60 frames | 0.0120 | 7649 | resp_6ae62e734cc48b6d62034ad7 |
| 2026-11-01 01:07 | eval-synth-02 | sam-3.1 | sam video 'water' synth load 2 | 0 (0) / 0 · 60 frames | 0.0120 | 4500 | resp_6ae62e7900376c15c9184995 |
| 2026-11-01 01:08 | eval-synth-02 | muse-spark-1.3 | spark labels f13 try 1 | 396 (114) / 2018 | 0.0089 | 12111 | resp_6ae62e89c0a650f205fe49d9 |
| 2026-11-01 01:08 | eval-synth-02 | muse-spark-1.3 | spark labels f3 try 1 | 396 (114) / 2457 | 0.0108 | 13923 | resp_6ae62e8bdb7443337e674e3a |
| 2026-11-01 01:08 | eval-synth-03 | sam-3.1 | sam video 'white number' synth load 3 | 0 (0) / 0 · 60 frames | 0.0120 | 8853 | resp_6ae62e91304ab872e17644fe |
| 2026-11-01 01:08 | eval-synth-03 | sam-3.1 | sam video 'water' synth load 3 | 0 (0) / 0 · 60 frames | 0.0120 | 6898 | resp_6ae62e9a0d728ab118a64e14 |
| 2026-11-01 01:09 | eval-synth-03 | muse-spark-1.3 | spark labels f9 try 1 | 396 (0) / 9062 | 0.0390 | 44824 | resp_6ae62ecc35b7fc7941774c4c |
| 2026-11-01 01:09 | eval-synth-03 | muse-spark-1.3 | spark labels f28 try 1 | 396 (19) / 10671 | 0.0458 | 58205 | resp_6ae62edae0b88506e72c41c5 |
| 2026-11-01 01:10 | eval-synth-03 | muse-spark-1.3 | spark labels f9 try 2 | 459 (0) / 7796 | 0.0337 | 41067 | resp_6ae62f023b9ff278d6c74afc |
| 2026-11-01 01:10 | eval-synth-03 | muse-spark-1.3 | spark labels f28 try 2 | 459 (147) / 9102 | 0.0391 | 48692 | resp_6ae62f0af5996d9d2fef4d7a |
| 2026-11-01 01:10 | eval-synth-04 | sam-3.1 | sam video 'white number' synth load 4 | 0 (0) / 0 · 60 frames | 0.0120 | 9183 | resp_6ae62f1026a5c85c35c9426f |
| 2026-11-01 01:10 | eval-synth-04 | sam-3.1 | sam video 'water' synth load 4 | 0 (0) / 0 · 60 frames | 0.0120 | 3327 | resp_6ae62f17059430befbad445f |
| 2026-11-01 01:10 | eval-synth-04 | muse-spark-1.3 | spark labels f0 try 1 | 396 (114) / 3566 | 0.0155 | 20460 | resp_6ae62f2f1be9cae9f81546f0 |
| 2026-11-01 01:11 | eval-synth-04 | muse-spark-1.3 | spark labels f15 try 1 | 396 (19) / 4342 | 0.0189 | 25697 | resp_6ae62f34f9e7c2269ac644df |
| 2026-11-01 01:11 | eval-synth-04 | muse-spark-1.3 | spark labels f0 try 2 | 459 (0) / 7213 | 0.0312 | 35518 | resp_6ae62f5787469b17a48449a9 |
| 2026-11-01 01:11 | eval-synth-04 | muse-spark-1.3 | spark labels f15 try 2 | 459 (147) / 8922 | 0.0383 | 40674 | resp_6ae62f5d0ec958f1aa2d4755 |
| 2026-11-01 01:11 | eval-synth-05 | sam-3.1 | sam video 'white number' synth load 5 | 0 (0) / 0 · 60 frames | 0.0120 | 9435 | resp_6ae62f627e8e907b8130412b |
| 2026-11-01 01:11 | eval-synth-05 | sam-3.1 | sam video 'water' synth load 5 | 0 (0) / 0 · 60 frames | 0.0120 | 4666 | resp_6ae62f6b8560247a379c43a0 |
| 2026-11-01 01:12 | eval-synth-05 | muse-spark-1.3 | spark labels f6 try 1 | 396 (114) / 1317 | 0.0060 | 6912 | resp_6ae62f77b65f5ae813e84d36 |
| 2026-11-01 01:12 | eval-synth-05 | muse-spark-1.3 | spark labels f0 try 1 | 396 (114) / 2495 | 0.0110 | 10704 | resp_6ae62f7a5b6dd962f0d9408b |
| 2026-11-01 01:12 | eval-synth-06 | sam-3.1 | sam video 'white number' synth load 6 | 0 (0) / 0 · 60 frames | 0.0120 | 11279 | resp_6ae62f812c269914da2b476e |
| 2026-11-01 01:12 | eval-synth-06 | sam-3.1 | sam video 'water' synth load 6 | 0 (0) / 0 · 60 frames | 0.0120 | 4771 | resp_6ae62f8a716969b3c27b4ff1 |
| 2026-11-01 01:12 | eval-synth-07 | sam-3.1 | sam video 'white number' synth load 7 | 0 (0) / 0 · 60 frames | 0.0120 | 9332 | resp_6ae62f950226d29c854843da |
| 2026-11-01 01:12 | eval-synth-07 | sam-3.1 | sam video 'water' synth load 7 | 0 (0) / 0 · 60 frames | 0.0120 | 4688 | resp_6ae62f9d8b96312ae6a64e2c |
| 2026-11-01 01:12 | eval-synth-08 | sam-3.1 | sam video 'white number' synth load 8 | 0 (0) / 0 · 60 frames | 0.0120 | 8505 | resp_6ae62fa7f7ec580d233d4c77 |
| 2026-11-01 01:13 | eval-synth-08 | sam-3.1 | sam video 'water' synth load 8 | 0 (0) / 0 · 60 frames | 0.0120 | 4216 | resp_6ae62faecef873f374834ad3 |
| 2026-11-01 01:13 | eval-synth-09 | sam-3.1 | sam video 'white number' synth load 9 | 0 (0) / 0 · 60 frames | 0.0120 | 8501 | resp_6ae62fb82e6fc9d8c802481c |
| 2026-11-01 01:13 | eval-synth-09 | sam-3.1 | sam video 'water' synth load 9 | 0 (0) / 0 · 60 frames | 0.0120 | 3033 | resp_6ae62fbe6fc5d5b4f7ca4e94 |
| 2026-11-01 01:13 | eval-synth-10 | sam-3.1 | sam video 'white number' synth load 10 | 0 (0) / 0 · 60 frames | 0.0120 | 9123 | resp_6ae62fc9c80cdb0b8e7b4492 |
| 2026-11-01 01:13 | eval-synth-10 | sam-3.1 | sam video 'water' synth load 10 | 0 (0) / 0 · 60 frames | 0.0120 | 3973 | resp_6ae62fd0816ec8dd10f14012 |
| 2026-11-01 01:13 | eval-synth-11 | sam-3.1 | sam video 'white number' synth load 11 | 0 (0) / 0 · 60 frames | 0.0120 | 7983 | resp_6ae62fdab4f84687a6a74667 |
| 2026-11-01 01:13 | eval-synth-11 | sam-3.1 | sam video 'water' synth load 11 | 0 (0) / 0 · 60 frames | 0.0120 | 4361 | resp_6ae62fe1537b0f80e0d1424c |
| 2026-11-01 01:14 | eval-synth-12 | sam-3.1 | sam video 'white number' synth load 12 | 0 (0) / 0 · 60 frames | 0.0120 | 8248 | resp_6ae62feb58156d4aefd5452a |
| 2026-11-01 01:14 | eval-synth-12 | sam-3.1 | sam video 'water' synth load 12 | 0 (0) / 0 · 60 frames | 0.0120 | 6763 | resp_6ae62ff3777b2101439443e8 |
| 2026-11-01 01:14 | eval-synth-01 | sam-3.1 | sam video 'white number' synth load 1 | 0 (0) / 0 · 60 frames | 0.0120 | 9193 | resp_6ae630199dd6cc6dd63d4129 |
| 2026-11-01 01:14 | eval-synth-01 | sam-3.1 | sam video 'water' synth load 1 | 0 (0) / 0 · 60 frames | 0.0120 | 4599 | resp_6ae630208f5704c17eef4215 |
| 2026-11-01 01:15 | eval-synth-01 | muse-spark-1.3 | spark labels f6 try 1 | 396 (370) / 1617 | 0.0070 | 6733 | resp_6ae6302bee1e0cd3532c4416 |
| 2026-11-01 01:15 | eval-synth-01 | muse-spark-1.3 | spark labels f0 try 1 | 396 (114) / 1714 | 0.0077 | 7803 | resp_6ae6302ce8b50bffd3b84e2c |
| 2026-11-01 01:15 | eval-synth-03 | sam-3.1 | sam video 'white number' synth load 3 | 0 (0) / 0 · 60 frames | 0.0120 | 9630 | resp_6ae6303331b3f656b5034fdb |
| 2026-11-01 01:15 | eval-synth-03 | sam-3.1 | sam video 'water' synth load 3 | 0 (0) / 0 · 60 frames | 0.0120 | 4355 | resp_6ae6303bbe6ca79c57b2445a |
| 2026-11-01 01:15 | eval-synth-03 | muse-spark-1.3 | spark labels f28 try 1 | 396 (275) / 6589 | 0.0282 | 28213 | resp_6ae6305b7b88c02ba50942bf |
| 2026-11-01 01:16 | eval-synth-03 | muse-spark-1.3 | spark labels f9 try 1 | 396 (19) / 11327 | 0.0486 | 47676 | resp_6ae6306f83a9088001e6433e |
| 2026-11-01 01:16 | eval-synth-03 | muse-spark-1.3 | spark labels f9 try 2 | 459 (147) / 6160 | 0.0266 | 29077 | resp_6ae6308cf5b64df11bf34908 |
| 2026-11-01 01:17 | eval-synth-03 | muse-spark-1.3 | spark labels f28 try 2 | 459 (403) / 12877 | 0.0549 | 52969 | resp_6ae630a41e734a2f1a604522 |
| 2026-11-01 01:17 | eval-synth-04 | sam-3.1 | sam video 'white number' synth load 4 | 0 (0) / 0 · 60 frames | 0.0120 | 9330 | resp_6ae630abfb2736d60fc24b91 |
| 2026-11-01 01:17 | eval-synth-04 | sam-3.1 | sam video 'water' synth load 4 | 0 (0) / 0 · 60 frames | 0.0120 | 4385 | resp_6ae630b395d1605d93d04308 |
| 2026-11-01 01:17 | eval-synth-04 | muse-spark-1.3 | spark labels f0 try 1 | 396 (114) / 5123 | 0.0221 | 24346 | resp_6ae630cf6fbbcd67df214646 |
| 2026-11-01 01:18 | eval-synth-04 | muse-spark-1.3 | spark labels f15 try 1 | 396 (275) / 10735 | 0.0458 | 46907 | resp_6ae630e66f8149f685f14c00 |
| 2026-11-01 01:18 | eval-synth-04 | muse-spark-1.3 | spark labels f0 try 2 | 459 (370) / 6949 | 0.0297 | 30604 | resp_6ae631040e0d80ca406d4e84 |
| 2026-11-01 01:18 | eval-synth-04 | muse-spark-1.3 | spark labels f15 try 2 | 459 (403) / 6847 | 0.0292 | 30852 | resp_6ae631048c7c26e172864737 |
| 2026-11-01 01:22 | eval-synth-01 | sam-3.1 | sam video 'white number' synth load 1 | 0 (0) / 0 · 60 frames | 0.0120 | 8926 | resp_6ae631d2b78b651433fd4457 |
| 2026-11-01 01:22 | eval-synth-01 | sam-3.1 | sam video 'water' synth load 1 | 0 (0) / 0 · 60 frames | 0.0120 | 4309 | resp_6ae631da98478222c7204617 |
| 2026-11-01 01:22 | eval-synth-01 | muse-spark-1.3 | spark labels f6 try 1 | 396 (114) / 828 | 0.0039 | 5703 | resp_6ae631e48aa86bcf38bd4051 |
| 2026-11-01 01:22 | eval-synth-01 | muse-spark-1.3 | spark labels f0 try 1 | 396 (370) / 1636 | 0.0070 | 9331 | resp_6ae631e836082ec158d34183 |
| 2026-11-01 01:22 | eval-synth-02 | sam-3.1 | sam video 'white number' synth load 2 | 0 (0) / 0 · 60 frames | 0.0120 | 8129 | resp_6ae631ee02d5e4768b0a4e11 |
| 2026-11-01 01:22 | eval-synth-02 | sam-3.1 | sam video 'water' synth load 2 | 0 (0) / 0 · 60 frames | 0.0120 | 4657 | resp_6ae631f51c9517e3955b40d2 |
| 2026-11-01 01:23 | eval-synth-02 | muse-spark-1.3 | spark labels f13 try 1 | 396 (370) / 2420 | 0.0104 | 14237 | resp_6ae63207ced43dd3221b46bf |
| 2026-11-01 01:23 | eval-synth-02 | muse-spark-1.3 | spark labels f3 try 1 | 396 (370) / 2912 | 0.0125 | 17299 | resp_6ae6320a7455ad14677b4d5e |
| 2026-11-01 01:23 | eval-synth-03 | sam-3.1 | sam video 'white number' synth load 3 | 0 (0) / 0 · 60 frames | 0.0120 | 7954 | resp_6ae63210a4e6c2c645aa47da |
| 2026-11-01 01:23 | eval-synth-03 | sam-3.1 | sam video 'water' synth load 3 | 0 (0) / 0 · 60 frames | 0.0120 | 3209 | resp_6ae6321572d8fc65f8394d10 |
| 2026-11-01 01:23 | eval-synth-03 | muse-spark-1.3 | spark labels f6 try 1 | 396 (114) / 753 | 0.0036 | 4848 | resp_6ae6321f5204d17342cb4feb |
| 2026-11-01 01:23 | eval-synth-03 | muse-spark-1.3 | spark labels f0 try 1 | 396 (114) / 1012 | 0.0047 | 6051 | resp_6ae63220f96c58599c1144a5 |
| 2026-11-01 01:23 | eval-synth-03 | muse-spark-1.3 | spark labels f6 try 2 | 459 (114) / 935 | 0.0044 | 6104 | resp_6ae63226390cb1bc256b43f7 |
| 2026-11-01 01:23 | eval-synth-03 | muse-spark-1.3 | spark labels f0 try 2 | 459 (114) / 1329 | 0.0061 | 7278 | resp_6ae632278c42d6ac0a1548bb |
| 2026-11-01 01:23 | eval-synth-04 | sam-3.1 | sam video 'white number' synth load 4 | 0 (0) / 0 · 60 frames | 0.0120 | 7952 | resp_6ae6322c92fadbeec81b4d03 |
| 2026-11-01 01:23 | eval-synth-04 | sam-3.1 | sam video 'water' synth load 4 | 0 (0) / 0 · 60 frames | 0.0120 | 6526 | resp_6ae63235dc2edc7cecd24704 |
| 2026-11-01 01:24 | eval-synth-04 | muse-spark-1.3 | spark labels f49 try 1 | 396 (19) / 5812 | 0.0252 | 29585 | resp_6ae6325777df89592190438a |
| 2026-11-01 01:24 | eval-synth-04 | muse-spark-1.3 | spark labels f55 try 1 | 396 (19) / 6558 | 0.0283 | 32160 | resp_6ae6325ad72a5db3041949b1 |
| 2026-11-01 01:24 | eval-synth-04 | muse-spark-1.3 | spark labels f55 try 2 | 459 (147) / 5286 | 0.0229 | 24243 | resp_6ae63272749ba70ce6334f15 |
| 2026-11-01 01:25 | eval-synth-04 | muse-spark-1.3 | spark labels f49 try 2 | 459 (147) / 17821 | 0.0762 | 85354 | resp_6ae632af38c1b849a0ea4b18 |
| 2026-11-01 01:25 | eval-synth-05 | sam-3.1 | sam video 'white number' synth load 5 | 0 (0) / 0 · 60 frames | 0.0120 | 8075 | resp_6ae632b5621c74e369004cb4 |
| 2026-11-01 01:26 | eval-synth-05 | sam-3.1 | sam video 'water' synth load 5 | 0 (0) / 0 · 60 frames | 0.0120 | 4770 | resp_6ae632bc5e126ae2b2b34261 |
| 2026-11-01 01:26 | eval-synth-05 | muse-spark-1.3 | spark labels f6 try 1 | 396 (114) / 1015 | 0.0047 | 6943 | resp_6ae632c7e382ac817402413f |
| 2026-11-01 01:26 | eval-synth-05 | muse-spark-1.3 | spark labels f0 try 1 | 396 (370) / 2001 | 0.0086 | 11658 | resp_6ae632cc1f187a74af094c9c |
| 2026-11-01 01:26 | eval-synth-06 | sam-3.1 | sam video 'white number' synth load 6 | 0 (0) / 0 · 60 frames | 0.0120 | 7515 | resp_6ae632d107c41387d24243fb |
| 2026-11-01 01:26 | eval-synth-06 | sam-3.1 | sam video 'water' synth load 6 | 0 (0) / 0 · 60 frames | 0.0120 | 6982 | resp_6ae632da039815fa935d4a62 |
| 2026-11-01 01:26 | eval-synth-06 | muse-spark-1.3 | spark labels f0 try 1 | 396 (114) / 551 | 0.0027 | 4444 | resp_6ae632e43c4fb0b0f9d94c3e |
| 2026-11-01 01:26 | eval-synth-06 | muse-spark-1.3 | spark labels f6 try 1 | 396 (114) / 1766 | 0.0079 | 9247 | resp_6ae632e81f2fd5e550cd476f |
| 2026-11-01 01:26 | eval-synth-07 | sam-3.1 | sam video 'white number' synth load 7 | 0 (0) / 0 · 60 frames | 0.0120 | 8573 | resp_6ae632ee6a52797b8d7f48d0 |
| 2026-11-01 01:27 | eval-synth-07 | sam-3.1 | sam video 'water' synth load 7 | 0 (0) / 0 · 60 frames | 0.0120 | 4266 | resp_6ae632f5d2c755ad927f407c |
| 2026-11-01 01:27 | eval-synth-07 | muse-spark-1.3 | spark labels f2 try 1 | 396 (370) / 1842 | 0.0079 | 11005 | resp_6ae633050cfba50d1fda4928 |
| 2026-11-01 01:27 | eval-synth-07 | muse-spark-1.3 | spark labels f9 try 1 | 396 (370) / 3393 | 0.0145 | 18554 | resp_6ae6330c2f6c22e301404a77 |
| 2026-11-01 01:27 | eval-synth-08 | sam-3.1 | sam video 'white number' synth load 8 | 0 (0) / 0 · 60 frames | 0.0120 | 9065 | resp_6ae63312113acd37e5ba4c22 |
| 2026-11-01 01:27 | eval-synth-08 | sam-3.1 | sam video 'water' synth load 8 | 0 (0) / 0 · 60 frames | 0.0120 | 4869 | resp_6ae6331a42637534bddc4280 |
| 2026-11-01 01:27 | eval-synth-08 | muse-spark-1.3 | spark labels f0 try 1 | 396 (114) / 1185 | 0.0054 | 7038 | resp_6ae63326bf576a8ac1f84344 |
| 2026-11-01 01:27 | eval-synth-08 | muse-spark-1.3 | spark labels f6 try 1 | 396 (114) / 1243 | 0.0057 | 7296 | resp_6ae6332683fc8d924e084753 |
| 2026-11-01 01:27 | eval-synth-09 | sam-3.1 | sam video 'white number' synth load 9 | 0 (0) / 0 · 60 frames | 0.0120 | 8636 | resp_6ae6332ca2a1db6a3895455e |
| 2026-11-01 01:28 | eval-synth-09 | sam-3.1 | sam video 'water' synth load 9 | 0 (0) / 0 · 60 frames | 0.0120 | 5145 | resp_6ae63334f7601dbc4d364682 |
| 2026-11-01 01:28 | eval-synth-09 | muse-spark-1.3 | spark labels f0 try 1 | 396 (114) / 1056 | 0.0049 | 4798 | resp_6ae6333e8c29278e420a4f42 |
| 2026-11-01 01:28 | eval-synth-09 | muse-spark-1.3 | spark labels f6 try 1 | 396 (114) / 1623 | 0.0073 | 7211 | resp_6ae633412d6a2bc07c264efc |
| 2026-11-01 01:28 | eval-synth-10 | sam-3.1 | sam video 'white number' synth load 10 | 0 (0) / 0 · 60 frames | 0.0120 | 6611 | resp_6ae63344b88c6569f3134158 |
| 2026-11-01 01:28 | eval-synth-10 | sam-3.1 | sam video 'water' synth load 10 | 0 (0) / 0 · 60 frames | 0.0120 | 4944 | resp_6ae6334c7d07339e725e449e |
| 2026-11-01 01:28 | eval-synth-10 | muse-spark-1.3 | spark labels f3 try 1 | 396 (114) / 2111 | 0.0093 | 10123 | resp_6ae6335bf729cac00f654b47 |
| 2026-11-01 01:28 | eval-synth-10 | muse-spark-1.3 | spark labels f11 try 1 | 396 (114) / 2681 | 0.0118 | 13248 | resp_6ae6335e45ec94a7444b4f05 |
| 2026-11-01 01:28 | eval-synth-11 | sam-3.1 | sam video 'white number' synth load 11 | 0 (0) / 0 · 60 frames | 0.0120 | 7642 | resp_6ae6336392ca296426934ca2 |
| 2026-11-01 01:28 | eval-synth-11 | sam-3.1 | sam video 'water' synth load 11 | 0 (0) / 0 · 60 frames | 0.0120 | 4366 | resp_6ae6336a5cee3b55b2144bce |
| 2026-11-01 01:29 | eval-synth-11 | muse-spark-1.3 | spark labels f0 try 1 | 396 (114) / 1389 | 0.0063 | 7943 | resp_6ae6337774208578f4df4453 |
| 2026-11-01 01:29 | eval-synth-11 | muse-spark-1.3 | spark labels f6 try 1 | 396 (114) / 1799 | 0.0080 | 9968 | resp_6ae63379422b75582319471a |
| 2026-11-01 01:29 | eval-synth-12 | sam-3.1 | sam video 'white number' synth load 12 | 0 (0) / 0 · 60 frames | 0.0120 | 7660 | resp_6ae6337e03264a0050154677 |
| 2026-11-01 01:29 | eval-synth-12 | sam-3.1 | sam video 'water' synth load 12 | 0 (0) / 0 · 60 frames | 0.0120 | 4660 | resp_6ae6338540b974ca38a24a23 |
| 2026-11-01 01:29 | eval-synth-12 | muse-spark-1.3 | spark labels f5 try 1 | 396 (114) / 1196 | 0.0055 | 6852 | resp_6ae63390d44fd38e8b194f70 |
| 2026-11-01 01:29 | eval-synth-12 | muse-spark-1.3 | spark labels f14 try 1 | 396 (114) / 2893 | 0.0127 | 16079 | resp_6ae6339ac9fc108992944e27 |
| 2026-11-01 01:30 | eval-synth-01 | sam-3.1 | sam video 'white number' synth load 1 | 0 (0) / 0 · 60 frames | 0.0120 | 7677 | resp_6ae633d4a216bac14b234388 |
| 2026-11-01 01:30 | eval-synth-01 | sam-3.1 | sam video 'water' synth load 1 | 0 (0) / 0 · 60 frames | 0.0120 | 4818 | resp_6ae633db9c2b9c7d9a0e4192 |
| 2026-11-01 01:31 | eval-synth-01 | muse-spark-1.3 | spark labels f0 try 1 | 396 (19) / 698 | 0.0034 | 4618 | resp_6ae633e4d8868396061d4ce8 |
| 2026-11-01 01:31 | eval-synth-01 | muse-spark-1.3 | spark labels f6 try 1 | 396 (19) / 1193 | 0.0055 | 6618 | resp_6ae633e63c2dabcbd4854af1 |
| 2026-11-01 01:31 | eval-synth-02 | sam-3.1 | sam video 'white number' synth load 2 | 0 (0) / 0 · 60 frames | 0.0120 | 8090 | resp_6ae633eb065c7e0105a94402 |
| 2026-11-01 01:31 | eval-synth-02 | sam-3.1 | sam video 'water' synth load 2 | 0 (0) / 0 · 60 frames | 0.0120 | 5035 | resp_6ae633f3bb95bc9d9bb64de5 |
| 2026-11-01 01:31 | eval-synth-02 | muse-spark-1.3 | spark labels f3 try 1 | 396 (0) / 1633 | 0.0074 | 9465 | resp_6ae634005534a5107ed94411 |
| 2026-11-01 01:31 | eval-synth-02 | muse-spark-1.3 | spark labels f13 try 1 | 396 (52) / 2111 | 0.0094 | 11168 | resp_6ae6340297106cd72a394fd3 |
| 2026-11-01 01:31 | eval-synth-03 | sam-3.1 | sam video 'white number' synth load 3 | 0 (0) / 0 · 60 frames | 0.0120 | 7436 | resp_6ae634076a02db8470b8436d |
| 2026-11-01 01:31 | eval-synth-03 | sam-3.1 | sam video 'water' synth load 3 | 0 (0) / 0 · 60 frames | 0.0120 | 5340 | resp_6ae6340f0d563b2dc4c448f3 |
| 2026-11-01 01:31 | eval-synth-03 | muse-spark-1.3 | spark labels f6 try 1 | 396 (19) / 598 | 0.0030 | 3515 | resp_6ae63417d11588d799f54f35 |
| 2026-11-01 01:31 | eval-synth-03 | muse-spark-1.3 | spark labels f0 try 1 | 396 (19) / 833 | 0.0040 | 6156 | resp_6ae634190f4a710904c74fad |
| 2026-11-01 01:32 | eval-synth-04 | sam-3.1 | sam video 'white number' synth load 4 | 0 (0) / 0 · 60 frames | 0.0120 | 7377 | resp_6ae6341e6841f22c1eda4528 |
| 2026-11-01 01:32 | eval-synth-04 | sam-3.1 | sam video 'water' synth load 4 | 0 (0) / 0 · 60 frames | 0.0120 | 4688 | resp_6ae634251d223e553ab84433 |
| 2026-11-01 01:32 | eval-synth-04 | muse-spark-1.3 | spark labels f0 try 1 | 396 (52) / 3215 | 0.0141 | 18077 | resp_6ae6343bdae724fae573467c |
| 2026-11-01 01:32 | eval-synth-04 | muse-spark-1.3 | spark labels f7 try 1 | 396 (52) / 4081 | 0.0178 | 20837 | resp_6ae6343e0dbf746249544300 |
| 2026-11-01 01:32 | eval-synth-05 | sam-3.1 | sam video 'white number' synth load 5 | 0 (0) / 0 · 60 frames | 0.0120 | 7879 | resp_6ae634444c131d3e272b4395 |
| 2026-11-01 01:32 | eval-synth-05 | sam-3.1 | sam video 'water' synth load 5 | 0 (0) / 0 · 60 frames | 0.0120 | 4463 | resp_6ae6344ad448ad7f4c784135 |
| 2026-11-01 01:32 | eval-synth-05 | muse-spark-1.3 | spark labels f6 try 1 | 396 (19) / 1127 | 0.0053 | 7798 | resp_6ae634561e5209064711422b |
| 2026-11-01 01:32 | eval-synth-05 | muse-spark-1.3 | spark labels f0 try 1 | 396 (19) / 1640 | 0.0074 | 10279 | resp_6ae6345980b8d8385d934aa8 |
| 2026-11-01 01:33 | eval-synth-06 | sam-3.1 | sam video 'white number' synth load 6 | 0 (0) / 0 · 60 frames | 0.0120 | 7603 | resp_6ae6345e1cc586af445d4359 |
| 2026-11-01 01:33 | eval-synth-06 | sam-3.1 | sam video 'water' synth load 6 | 0 (0) / 0 · 60 frames | 0.0120 | 4640 | resp_6ae63465156187e2523049ad |
| 2026-11-01 01:33 | eval-synth-06 | muse-spark-1.3 | spark labels f0 try 1 | 396 (19) / 1630 | 0.0074 | 9679 | resp_6ae634730a6efcc594d64f13 |
| 2026-11-01 01:33 | eval-synth-06 | muse-spark-1.3 | spark labels f6 try 1 | 396 (19) / 2363 | 0.0105 | 14183 | resp_6ae634775ca425c473a544de |
| 2026-11-01 01:33 | eval-synth-07 | sam-3.1 | sam video 'white number' synth load 7 | 0 (0) / 0 · 60 frames | 0.0120 | 8044 | resp_6ae6347d68cb52179d0349a7 |
| 2026-11-01 01:33 | eval-synth-07 | sam-3.1 | sam video 'water' synth load 7 | 0 (0) / 0 · 60 frames | 0.0120 | 3446 | resp_6ae63483d0d595f635e14857 |
| 2026-11-01 01:34 | eval-synth-07 | muse-spark-1.3 | spark labels f9 try 1 | 396 (0) / 2713 | 0.0120 | 17886 | resp_6ae63498b1080332f737415a |
| 2026-11-01 01:34 | eval-synth-07 | muse-spark-1.3 | spark labels f1 try 1 | 396 (52) / 4608 | 0.0200 | 28114 | resp_6ae634a321fe95da42714884 |
| 2026-11-01 01:34 | eval-synth-08 | sam-3.1 | sam video 'white number' synth load 8 | 0 (0) / 0 · 60 frames | 0.0120 | 8533 | resp_6ae634a8611db85a2d6648eb |
| 2026-11-01 01:34 | eval-synth-08 | sam-3.1 | sam video 'water' synth load 8 | 0 (0) / 0 · 60 frames | 0.0120 | 3341 | resp_6ae634ae4f8544a27f584b2b |
| 2026-11-01 01:34 | eval-synth-08 | muse-spark-1.3 | spark labels f6 try 1 | 396 (19) / 1399 | 0.0064 | 8768 | resp_6ae634bb699c49e72d804538 |
| 2026-11-01 01:34 | eval-synth-08 | muse-spark-1.3 | spark labels f0 try 1 | 396 (19) / 1669 | 0.0076 | 10691 | resp_6ae634bdc1908ad6e55546b8 |
| 2026-11-01 01:34 | eval-synth-09 | sam-3.1 | sam video 'white number' synth load 9 | 0 (0) / 0 · 60 frames | 0.0120 | 9808 | resp_6ae634c4658726ddc18a4a6d |
| 2026-11-01 01:34 | eval-synth-09 | sam-3.1 | sam video 'water' synth load 9 | 0 (0) / 0 · 60 frames | 0.0120 | 4229 | resp_6ae634cb2393c4358a444a9c |
| 2026-11-01 01:35 | eval-synth-09 | muse-spark-1.3 | spark labels f6 try 1 | 396 (19) / 1394 | 0.0064 | 10456 | resp_6ae634d9b858a10562674692 |
| 2026-11-01 01:35 | eval-synth-09 | muse-spark-1.3 | spark labels f0 try 1 | 396 (19) / 1575 | 0.0072 | 10484 | resp_6ae634d930c7155f292e49f8 |
| 2026-11-01 01:35 | eval-synth-10 | sam-3.1 | sam video 'white number' synth load 10 | 0 (0) / 0 · 60 frames | 0.0120 | 8191 | resp_6ae634df1d03565ae244488f |
| 2026-11-01 01:35 | eval-synth-10 | sam-3.1 | sam video 'water' synth load 10 | 0 (0) / 0 · 60 frames | 0.0120 | 4423 | resp_6ae634e6542aa551995e4d45 |
| 2026-11-01 01:35 | eval-synth-10 | muse-spark-1.3 | spark labels f3 try 1 | 396 (52) / 3099 | 0.0136 | 17410 | resp_6ae634fb2b5ad929237b4114 |
| 2026-11-01 01:36 | eval-synth-10 | muse-spark-1.3 | spark labels f11 try 1 | 396 (52) / 7093 | 0.0306 | 38557 | resp_6ae63510fe59dd2c9801431d |
| 2026-11-01 01:36 | eval-synth-11 | sam-3.1 | sam video 'white number' synth load 11 | 0 (0) / 0 · 60 frames | 0.0120 | 7610 | resp_6ae63516cc680bf49c714357 |
| 2026-11-01 01:36 | eval-synth-11 | sam-3.1 | sam video 'water' synth load 11 | 0 (0) / 0 · 60 frames | 0.0120 | 5782 | resp_6ae6351e13667013a9574a2a |
| 2026-11-01 01:36 | eval-synth-11 | muse-spark-1.3 | spark labels f0 try 1 | 396 (19) / 1384 | 0.0064 | 7367 | resp_6ae635295436edd847704321 |
| 2026-11-01 01:36 | eval-synth-11 | muse-spark-1.3 | spark labels f6 try 1 | 396 (19) / 1584 | 0.0072 | 8330 | resp_6ae6352ac25851847a7e46cd |
| 2026-11-01 01:36 | eval-synth-12 | sam-3.1 | sam video 'white number' synth load 12 | 0 (0) / 0 · 60 frames | 0.0120 | 7775 | resp_6ae6353017484ba7fc8643eb |
| 2026-11-01 01:36 | eval-synth-12 | sam-3.1 | sam video 'water' synth load 12 | 0 (0) / 0 · 60 frames | 0.0120 | 3261 | resp_6ae63535e266ea66dca04bab |
| 2026-11-01 01:37 | eval-synth-12 | muse-spark-1.3 | spark labels f4 try 1 | 396 (19) / 3609 | 0.0158 | 20585 | resp_6ae6354efdb8a2ee54be4256 |
| 2026-11-01 01:37 | eval-synth-12 | muse-spark-1.3 | spark labels f14 try 1 | 396 (19) / 5013 | 0.0218 | 29873 | resp_6ae6355790ac9c5c01b14651 |
| 2026-11-01 06:04 | live-mvx0dfza | sam-3.1 | sam video 'water' upload (P6c demo take 'take1', judge upload path, live site) | 0 (0) / 0 · 60 frames | 0.0120 | 7111 | resp_6ae6740c287f0396633c4ac6 |
| 2026-11-01 06:04 | live-mvx0dfza | sam-3.1 | sam video 'white number' upload (P6c demo take 'take1', judge upload path, live site) | 0 (0) / 0 · 60 frames | 0.0120 | 10102 | resp_6ae6740ed8a60aab3fb7447e |
| 2026-11-01 06:05 | live-mvx0dfza | muse-spark-1.3 | spark labels f0 try 1 (P6c demo take 'take1', judge upload path, live site) | 462 (0) / 1169 | 0.0055 | 4665 | resp_6ae67449b6615692a70640ff |
| 2026-11-01 06:05 | live-mvx0dfza | muse-spark-1.3 | spark labels f10 try 1 (P6c demo take 'take1', judge upload path, live site) | 462 (0) / 2198 | 0.0099 | 8416 | resp_6ae6744c4e8ae94a2464491d |
| 2026-11-01 06:16 | live-mvx0ss6d | sam-3.1 | sam video 'water' upload (P6c demo take 'take2', judge upload path, live site) | 0 (0) / 0 · 60 frames | 0.0120 | 5983 | resp_6ae676d9af55366832aa4028 |
| 2026-11-01 06:16 | live-mvx0ss6d | sam-3.1 | sam video 'white number' upload (P6c demo take 'take2', judge upload path, live site) | 0 (0) / 0 · 60 frames | 0.0120 | 6410 | resp_6ae676da29b4db285e4d44a0 |
| 2026-11-01 06:17 | live-mvx0ss6d | muse-spark-1.3 | spark labels f0 try 1 (P6c demo take 'take2', judge upload path, live site) | 462 (0) / 994 | 0.0048 | 5028 | resp_6ae677126a439f10d7314093 |
| 2026-11-01 06:17 | live-mvx0ss6d | muse-spark-1.3 | spark labels f10 try 1 (P6c demo take 'take2', judge upload path, live site) | 462 (0) / 2113 | 0.0096 | 9441 | resp_6ae67717de873e7b58e148d4 |
| 2026-11-01 06:34 | live-mvx1g5z2 | sam-3.1 | sam video 'water' upload (P6c demo take 'take3', judge upload path, live site) | 0 (0) / 0 · 60 frames | 0.0120 | 5488 | resp_6ae67b1bdfdc1709ec624636 |
| 2026-11-01 06:34 | live-mvx1g5z2 | sam-3.1 | sam video 'white number' upload (P6c demo take 'take3', judge upload path, live site) | 0 (0) / 0 · 60 frames | 0.0120 | 8524 | resp_6ae67b1dbc7c0a3e66ca47c8 |
| 2026-11-01 06:35 | live-mvx1g5z2 | muse-spark-1.3 | spark labels f0 try 1 (P6c demo take 'take3', judge upload path, live site) | 462 (0) / 1931 | 0.0088 | 8341 | resp_6ae67b5ae1f0437ff6e44569 |
| 2026-11-01 06:35 | live-mvx1g5z2 | muse-spark-1.3 | spark labels f10 try 1 (P6c demo take 'take3', judge upload path, live site) | 462 (0) / 2488 | 0.0112 | 11895 | resp_6ae67b5edd0cd5d55eaa4bbb |
| 2026-11-01 06:40 | live-mvx1muta | sam-3.1 | sam video 'white number' upload (P6c demo take 'take4', judge upload path, live site) | 0 (0) / 0 · 60 frames | 0.0120 | 5873 | resp_6ae67c54e79c0cc2f33f4fc1 |
| 2026-11-01 06:40 | live-mvx1muta | sam-3.1 | sam video 'water' upload (P6c demo take 'take4', judge upload path, live site) | 0 (0) / 0 · 60 frames | 0.0120 | 6133 | resp_6ae67c54e2baa17d21414096 |
| 2026-11-01 06:41 | live-mvx1muta | muse-spark-1.3 | spark labels f0 try 1 (P6c demo take 'take4', judge upload path, live site) | 462 (0) / 1603 | 0.0074 | 7958 | resp_6ae67c90d6c272cf70c2436f |
| 2026-11-01 06:41 | live-mvx1muta | muse-spark-1.3 | spark labels f10 try 1 (P6c demo take 'take4', judge upload path, live site) | 462 (0) / 2127 | 0.0096 | 10419 | resp_6ae67c9265c51a8107d74fa4 |
| 2026-11-01 06:48 | live-mvx1wyzw | sam-3.1 | sam video 'white number' upload (P6c demo take 'take5', judge upload path, live site) | 0 (0) / 0 · 60 frames | 0.0120 | 7856 | resp_6ae67e2e6e6a44bdce3742f0 |
| 2026-11-01 06:48 | live-mvx1wyzw | sam-3.1 | sam video 'water' upload (P6c demo take 'take5', judge upload path, live site) | 0 (0) / 0 · 60 frames | 0.0120 | 8283 | resp_6ae67e2e0fd6f39b30444378 |
| 2026-11-01 06:48 | live-mvx1wyzw | muse-spark-1.3 | spark labels f0 try 1 (P6c demo take 'take5', judge upload path, live site) | 462 (0) / 1543 | 0.0071 | 6440 | resp_6ae67e6a3b240589c1234d71 |
| 2026-11-01 06:49 | live-mvx1wyzw | muse-spark-1.3 | spark labels f10 try 1 (P6c demo take 'take5', judge upload path, live site) | 462 (0) / 3071 | 0.0136 | 11200 | resp_6ae67e6f9287b9086b964fc8 |
