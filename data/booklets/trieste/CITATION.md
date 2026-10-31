# Trieste trim & stability booklet: what we extracted, and from where

**Source:** "Trim and Stability Booklet (including Loading Information)", Studio Tecnico Moroso-Starita (PDF
title "Piano di sicurezza"), 337 pages; a Ro-Ro/passenger ship, Lpp 150.00 m. Public course material at the
University of Trieste Moodle, no login required:
<https://moodle2.units.it/pluginfile.php/582393/mod_resource/content/0/Esercitazione%201.pdf>
(retrieved 2026-10-31; sha256 of the file we read `299253f73621e8c20b264369f65467c91dd80817fc3ae2dc5d599d33e6cfce88`).

**Licence: unstated.** This repository therefore does NOT contain the PDF, page images, or page text. It contains
only numbers we extracted (`hydrostatics.csv`, `conditions.csv`) with page references, so every value can be checked
against the public original. The app reads the page text live from the public URL; the committed numbers are the
fallback if that URL disappears.

## Files
| File | Rows | Booklet pages | Fields |
|---|---|---|---|
| `hydrostatics.csv` | 177 (draft 0.500-9.300 m, step 0.050) | 36-39 ("Hydrostatic Properties") | draft, Displ (MT), LCB, VCB, LCF (from AP), TPcm, MTcm (per degree, see below), KML, KMT; `page`, `line` |
| `conditions.csv` | 22 worked loading conditions | 101-324 (one page each; `page` column) | drafts at the marks FORE/MID/AFT x port/starboard, WaterSpgr, the printed Draft FP/MS/AP, and the PRINTED Displacement; `page` + line numbers |

## How the numbers were verified (every row)
1. `scripts/extract_trieste.py`: `pdftotext -layout` extraction, parsed by regex.
2. The same script re-reads every page with `pypdf` (an independent text extractor) and requires every extracted
   value to appear on the same page; 0 disagreements on all 177 table rows and all 22 x 11 condition fields.
3. All 22 condition blocks were rendered to images and read by eye against `conditions.csv` (P1a, 2026-10-31):
   all fields match.

## Booklet quirks a program must get right (found in P1a)
- **Lpp is 150 m**, but the mark formulas on p.21 divide by **140**: that is the distance between the fore mark
  (1.200 m aft of FP) and the aft mark (8.800 m forward of AP), not Lpp. D2 uses Lpp = 150.
- **LCF is measured from the AP** (p.36 legend), so the trim correction is `t * TPcm * 100 * (Lpp/2 - LCF) / Lpp`.
- **The MTcm column is per degree of trim**: the table heading says "MT-m/deg" while the p.36 legend says "MT-m/cm";
  the magnitudes (e.g. 67 047 at 4.60 m) only fit per degree.
- **The §3.1 procedure (p.21-22) is first order.** Applied verbatim it reproduces 14 of the 22 printed displacements
  within 0.1 % (worst 0.378 %, error growing with trim squared). Adding the standard second trim correction (Nemoto,
  UNECE draught-survey code) reproduces 22 of 22 (worst 0.060 %). `scripts/check_reference.py [--verbatim]`.
- The booklet's own summary table (p.100) prints condition 8.1 as 16 596.3 t; the condition page (p.280) prints
  16 569.3 t. We use the condition pages; our reference gives 16 570.8 t.
