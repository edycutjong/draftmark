# Meta Model API: developer-experience log

Friction and surprises met while building DraftMark, with what we did about each. Dated, factual.

| Date | API / model | What happened | Workaround |
|---|---|---|---|
| 2026-10-31 | SAM 3.1 | ~18 px numerals on a full 1280-1920 px frame: 0 objects for "number" / "white number" | crop the mark column and scale 2x: every numeral found |
| 2026-10-31 | SAM 3.1 | concept wording matters: "numeral", "letter", "text", "white marking" -> 0; "white number" works | fixed concept strings, tested per clip |
| 2026-10-31 | SAM 3.1 | video output caps at 16 objects per frame | crop to the lower marks; code raises OBJECT_CAP at 16 raw glyphs |
| 2026-10-31 | SAM 3.1 | multi-character marks ("13M") may come back as one box or as separate glyph boxes | code groups glyphs into tokens (baseline + gap rule) before labelling |
| 2026-10-31 | SAM 3.1 | mask grammar: masks are cropped to their box (origin = box origin); boxes are inclusive pixel indices (`meta_sam_parser` returns half-open) | our parser matches `meta_sam_parser` exactly; tested on real output |
| 2026-10-31 | SAM 3.1 | `video/webm` rejected: "Supported: MP4" | MP4-only uploads |
| 2026-10-31 | SAM 3.1 | "water" (and "sea water", "water surface", "green water") finds nothing on rendered synthetic water (3 textures) but works on real water | synthetic tests check geometry in code; SAM is tested on real footage |
| 2026-10-31 | Muse Wonder 1.0 | native `{"type": "computer"}` tool -> HTTP 400 "Unsupported tool type" on our key; Muse Spark 1.3 accepts it | computer use runs as a Spark sub-agent (or Wonder via function tools) |
| 2026-10-31 | Muse Spark 1.3 | every computer action carries `computer_action_requires_confirmation` | harness acknowledges only on an allowlist of hosts |
| 2026-10-31 | Muse Wonder 1.0 | regenerations: input tokens grew only 12.4k -> 12.5k -> 13.5k although we sent the previous program back as an assistant `output_text` turn (~3-4k tokens) | unresolved; feedback text is self-contained (failing ids + the program's own intermediates), which worked |
| 2026-10-31 | Responses API | strict `text.format` `json_schema` with per-key enums works on Spark 1.3; a "?" enum value lets the model abstain | labels schema allows "?" |
