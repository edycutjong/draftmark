# Real-ship draft reading on an openly licensed photo set: NOT RUN (licence not verifiable)

Planned (P1e step 2): read the draft on real-ship photos from an openly licensed draft-mark dataset and compare it with
the labelled mark. **Not run, and no number is claimed.** Why, as attempted on 2026-11-01:

| attempt | result |
|---|---|
| Roboflow Universe search ("ship draft marks", "ship draft marks detection") | several public projects whose search snippets say CC BY 4.0 (e.g. `draftmarksdetection/ship-draft-marks`, 320 images; `weed-pbhru/ship-draft-marks-ffebm`; `aquadepth-workspace/ship-draft-marks-detection`, 2576 images) |
| open the dataset pages to verify the licence on the page itself | HTTP 403 to a script (bot protection), so the licence text and attribution requirements were NOT verified here |
| download the images | Roboflow exports need a logged-in account / API key; none exists in this environment, and a signup is a human step |
| arXiv 2310.07212 (MTL-VDR) benchmark | no open licence statement or download link found, so it is not used |

The rule for this phase is "never use a set whose licence is unclear", so the real-photo reading check was skipped
rather than run on an unverified set. The licence in a search snippet is not the licence on the dataset page.

What is also true of those sets: from their descriptions they are object-detection sets (boxes around marks), so even
with a verified licence the check would be mark-detection recall plus a small hand-checked reading subset, not a weight.

Consequences stated on every judged page: draft reading is shown on third-party real-hull test clips without ground
truth (dB7X, UKTRQ; eeLL refused by the label checks); there is no real-ship accuracy figure; there is no physical scale
check. Steps for the human, if wanted before submission, are in `submission/HUMAN-TODO.md`.
