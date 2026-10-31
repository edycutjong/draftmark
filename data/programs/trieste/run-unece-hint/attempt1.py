import math
import bisect
import re


def parse_booklet(booklet):
    pages = booklet.get("pages", {}) if isinstance(booklet, dict) else {}

    def page_key(item):
        try:
            return int(item[0])
        except Exception:
            return 0

    ordered = sorted(pages.items(), key=page_key)
    text = "\n".join([str(v) for k, v in ordered])

    def find_float(pattern, default=None):
        m = re.search(pattern, text, re.I)
        if m:
            try:
                return float(m.group(1).replace(",", "").replace(" ", ""))
            except Exception:
                return default
        return default

    lpp = find_float(r"Length\s+Between\s+Perpendiculars\s+([\d.]+)\s*m", 150.0)
    loa = find_float(r"Length\s+Overall\s+([\d.]+)\s*m")
    breadth = find_float(r"Breadth\s+Molded\s+([\d.]+)\s*m")
    summer_draft = find_float(r"Summer\s+Draft\s+([\d.]+)\s*m")
    standard_sg = find_float(r"Water\s+Specific\s+Gravity\s*=?\s*([\d.]+)", 1.025)
    if standard_sg is None:
        standard_sg = 1.025

    # Draft-mark to perpendicular corrections exactly as printed on page 21:
    # dFP = df - [1.200 * ((da - df) / 140)]
    # dAP = da + [8.800 * ((da - df) / 140)]
    fore_corr = find_float(
        r"dFP\s*=\s*df\s*-\s*\[\s*([\d.]+)\s*\*", 1.2
    )
    aft_corr = find_float(
        r"dAP\s*=\s*da\s*\+\s*\[\s*([\d.]+)\s*\*", 8.8
    )
    span = find_float(
        r"dFP\s*=\s*df\s*-\s*\[\s*[\d.]+\s*\*\s*\(\(da\s*-\s*df\)\s*/\s*([\d.]+)\)\]",
        140.0,
    )
    if span is None or span == 0:
        span = 140.0

    # Hydrostatic table. Columns as printed, left to right:
    # Draft(m), Displ(MT), LCB(m from AP, suffixed f), VCB(m), LCF(m from AP, f),
    # TPcm(MT/cm), MTcm(MT-m/deg, see note in survey), KML(m), KMT(m).
    # KML values above 1000 are printed with a space as thousands separator,
    # e.g. "1 394.363", hence the optional leading group in the KML pattern.
    row_pat = re.compile(
        r"(?m)^\s*(\d+\.\d{3})\s+(\d+\.\d+)\s+(\d+\.\d+)f\s+(\d+\.\d+)\s+"
        r"(\d+\.\d+)f\s+(\d+\.\d+)\s+(\d+\.\d+)\s+((?:\d+\s+)?\d+\.\d+)\s+(\d+\.\d+)\s*$"
    )
    hydrostatic = []
    seen = {}
    for m in row_pat.finditer(text):
        draft = float(m.group(1))
        row = {
            "draft": draft,
            "disp": float(m.group(2)),
            "displ": float(m.group(2)),
            "lcb": float(m.group(3)),
            "vcb": float(m.group(4)),
            "lcf": float(m.group(5)),
            "tpcm": float(m.group(6)),
            "tp_cm": float(m.group(6)),
            "mtcm": float(m.group(7)),
            "mtcm_deg": float(m.group(7)),
            "kml": float(m.group(8).replace(" ", "")),
            "kmt": float(m.group(9)),
        }
        if draft not in seen:
            seen[draft] = row
            hydrostatic.append(row)
    hydrostatic.sort(key=lambda r: r["draft"])

    ship = {
        "lpp": float(lpp),
        "length_between_perpendiculars": float(lpp),
        "loa": float(loa) if loa is not None else None,
        "length_overall": float(loa) if loa is not None else None,
        "breadth_molded": float(breadth) if breadth is not None else None,
        "summer_draft": float(summer_draft) if summer_draft is not None else None,
        "standard_sg": float(standard_sg),
        "sg_standard": float(standard_sg),
        "fore_mark_correction": float(fore_corr),
        "aft_mark_correction": float(aft_corr),
        "draft_mark_span": float(span),
        "draft_marks": {
            "fore": "Fr.189",
            "mid": "Fr.94 - 200 mm",
            "aft": "Fr. 11",
        },
        "hydrostatic": hydrostatic,
        "hydrostatic_columns": {
            "draft": "m from baseline",
            "disp": "MT",
            "lcb": "m from AP",
            "vcb": "m above baseline",
            "lcf": "m from AP",
            "tpcm": "MT/cm",
            "mtcm": "MT-m/deg as printed in table heading and Sheet No.1",
            "kml": "m above baseline",
            "kmt": "m above baseline",
        },
    }
    return ship


def survey(inputs, ship):
    def get(name, default=None):
        if isinstance(inputs, dict):
            return inputs.get(name, default)
        return default

    fore_p = float(get("fore_p"))
    fore_s = float(get("fore_s"))
    mid_p = float(get("mid_p"))
    mid_s = float(get("mid_s"))
    aft_p = float(get("aft_p"))
    aft_s = float(get("aft_s"))
    sg = float(get("sg", 1.025))

    lpp = float(ship.get("lpp", ship.get("length_between_perpendiculars", 150.0)))
    standard_sg = float(ship.get("standard_sg", ship.get("sg_standard", 1.025)))
    fore_corr = float(ship.get("fore_mark_correction", 1.2))
    aft_corr = float(ship.get("aft_mark_correction", 8.8))
    span = float(ship.get("draft_mark_span", 140.0))

    table = ship.get("hydrostatic", [])
    if not table:
        raise OutOfTable("hydrostatic table is empty")
    table = sorted(table, key=lambda r: float(r["draft"]))
    drafts = [float(r["draft"]) for r in table]
    d_min = drafts[0]
    d_max = drafts[-1]

    def interp(draft_value, key):
        if draft_value < d_min or draft_value > d_max:
            raise OutOfTable("draft outside hydrostatic table")
        i = bisect.bisect_left(drafts, draft_value)
        if i < len(drafts) and drafts[i] == draft_value:
            return float(table[i][key])
        if i == 0:
            return float(table[0][key])
        if i >= len(drafts):
            return float(table[-1][key])
        x0 = drafts[i - 1]
        x1 = drafts[i]
        y0 = float(table[i - 1][key])
        y1 = float(table[i][key])
        if x1 == x0:
            return y0
        frac = (draft_value - x0) / (x1 - x0)
        return y0 + frac * (y1 - y0)

    # Mean drafts at the marks (port/starboard mean), per booklet Sheet No.1 [1].
    df = (fore_p + fore_s) / 2.0
    dm = (mid_p + mid_s) / 2.0
    da = (aft_p + aft_s) / 2.0

    # Booklet page 21 corrections from draft marks to FP / AP; midship as read.
    apparent_trim = da - df
    d_fp = df - fore_corr * (apparent_trim / span)
    d_ap = da + aft_corr * (apparent_trim / span)
    d_ms = dm

    # Booklet page 22: trim, and quarter-mean draft (deflection corrected).
    trim = d_ap - d_fp
    d_m_no_defl = (d_ap + d_fp) / 2.0
    d_mm = (d_fp + 6.0 * d_ms + d_ap) / 8.0
    deflection = d_m_no_defl - d_ms

    if d_mm < d_min or d_mm > d_max:
        raise OutOfTable("mean draft outside hydrostatic table")

    disp_table = interp(d_mm, "disp")
    tpcm = interp(d_mm, "tpcm")
    lcf = interp(d_mm, "lcf")
    mtcm_deg = interp(d_mm, "mtcm")
    lcb = interp(d_mm, "lcb")

    # First trim correction, booklet formula D2 (LCF measured from AP):
    # D2 = t * TPcm * 100 * (Lpp/2 - LCF) / Lpp
    corr_trim1 = trim * tpcm * 100.0 * (lpp / 2.0 - lcf) / lpp

    # Standard practice added where the booklet is incomplete (UNECE draught
    # survey code): the second (Nemoto) trim correction, which the booklet
    # omits. The table's MTcm column is in MT-m/deg (as its heading and Sheet
    # No.1 state, despite the "/cm" wording in the definitions list; the
    # magnitudes confirm per-degree), so it is first converted to moment to
    # change trim by 1 cm: MCTcm = MTcm_deg * (180/pi) * (0.01 / Lpp).
    # Nemoto: corr2 = trim^2 * 50 / Lpp * (MCTcm at d+0.5m - MCTcm at d-0.5m),
    # normalised by the actual draft interval used near the table ends.
    def mct_cm(draft_value):
        mt_deg = interp(draft_value, "mtcm")
        return mt_deg * (180.0 / math.pi) * (0.01 / lpp)

    lo_d = max(d_min, d_mm - 0.5)
    hi_d = min(d_max, d_mm + 0.5)
    if hi_d > lo_d:
        dmct_per_m = (mct_cm(hi_d) - mct_cm(lo_d)) / (hi_d - lo_d)
        corr_trim2 = trim * trim * 50.0 / lpp * dmct_per_m
    else:
        corr_trim2 = 0.0

    # Density correction, booklet formula D3, applied (standard practice) to
    # the displacement after both trim corrections:
    # D3 = (D1 + D2 + corr2) * (SG - 1.025) / 1.025
    disp_after_trim = disp_table + corr_trim1 + corr_trim2
    corr_density = disp_after_trim * (sg - standard_sg) / standard_sg
    disp_final = disp_after_trim + corr_density

    return {
        "d_fp": float(d_fp),
        "d_ap": float(d_ap),
        "d_ms": float(d_ms),
        "df": float(df),
        "dm": float(dm),
        "da": float(da),
        "trim": float(trim),
        "d_mm": float(d_mm),
        "d_mean_no_deflection": float(d_m_no_defl),
        "deflection": float(deflection),
        "disp_table": float(disp_table),
        "tpcm": float(tpcm),
        "lcf": float(lcf),
        "lcb": float(lcb),
        "mtcm": float(mtcm_deg),
        "mtcm_deg": float(mtcm_deg),
        "corr_trim1": float(corr_trim1),
        "corr_trim2": float(corr_trim2),
        "corr_density": float(corr_density),
        "disp_final": float(disp_final),
        "sg": float(sg),
    }
