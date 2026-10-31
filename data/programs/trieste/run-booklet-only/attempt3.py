import math
import bisect
import re


def _num(text):
    return float(str(text).replace(",", "").rstrip("fF"))


def _interp(rows, drafts, x, key):
    if x <= drafts[0]:
        if x == drafts[0]:
            return float(rows[0][key])
        x0 = drafts[0]
        x1 = drafts[1]
        y0 = float(rows[0][key])
        y1 = float(rows[1][key])
        return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    if x >= drafts[-1]:
        if x == drafts[-1]:
            return float(rows[-1][key])
        x0 = drafts[-2]
        x1 = drafts[-1]
        y0 = float(rows[-2][key])
        y1 = float(rows[-1][key])
        return y1 + (y1 - y0) * (x - x1) / (x1 - x0)
    i = bisect.bisect_left(drafts, x)
    if drafts[i] == x:
        return float(rows[i][key])
    x0 = drafts[i - 1]
    x1 = drafts[i]
    y0 = float(rows[i - 1][key])
    y1 = float(rows[i][key])
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def parse_booklet(booklet):
    pages = booklet.get("pages", {}) if isinstance(booklet, dict) else {}
    ordered = []
    for key in sorted(pages.keys(), key=lambda z: int(z) if str(z).isdigit() else 9999):
        ordered.append(str(pages[key]))
    text = "\n".join(ordered)

    lpp = 150.0
    m = re.search(r"Length Between Perpendiculars\s+([0-9]+(?:\.[0-9]+)?)\s*m", text)
    if m:
        lpp = float(m.group(1))

    loa = None
    m = re.search(r"Length Overall\s+([0-9]+(?:\.[0-9]+)?)\s*m", text)
    if m:
        loa = float(m.group(1))

    breadth = None
    m = re.search(r"Breadth Molded\s+([0-9]+(?:\.[0-9]+)?)\s*m", text)
    if m:
        breadth = float(m.group(1))

    standard_sg = 1.025
    m = re.search(r"Water Specific Gravity\s+([0-9]+(?:\.[0-9]+)?)", text)
    if m:
        standard_sg = float(m.group(1))

    fore_corr = 1.2
    aft_corr = 8.8
    corr_divisor = 140.0
    pairs = re.findall(
        r"([0-9]+(?:\.[0-9]+)?)\s*\*\s*\(\s*\(\s*da\s*-\s*df\s*\)\s*/\s*([0-9]+(?:\.[0-9]+)?)\s*\)",
        text,
    )
    if len(pairs) >= 2:
        fore_corr = float(pairs[0][0])
        corr_divisor = float(pairs[0][1])
        aft_corr = float(pairs[1][0])
    elif len(pairs) == 1:
        fore_corr = float(pairs[0][0])
        corr_divisor = float(pairs[0][1])

    rows = []
    seen = {}
    for page_text in ordered:
        for line in page_text.splitlines():
            s = line.strip()
            mm = re.match(r"^([0-9]+\.[0-9]{3})\s+(.+)$", s)
            if not mm:
                continue
            draft = float(mm.group(1))
            toks = mm.group(2).split()
            # Columns: Displ LCB VCB LCF TPcm MTcm(/deg) KML KMT
            # KML may be printed with a thousands space, e.g. "1 394.363".
            if len(toks) < 8:
                continue
            try:
                displ = _num(toks[0])
                lcb = _num(toks[1])
                vcb = _num(toks[2])
                lcf = _num(toks[3])
                tpcm = _num(toks[4])
                mt_deg = _num(toks[5])
                rest = toks[6:]
                if len(rest) == 3:
                    kml = _num(rest[0] + rest[1])
                    kmt = _num(rest[2])
                elif len(rest) == 2:
                    kml = _num(rest[0])
                    kmt = _num(rest[1])
                else:
                    continue
            except ValueError:
                continue
            # Hydrostatic drafts in this booklet are 0.500 to 9.300 m.
            if draft < 0.4 or draft > 9.4:
                continue
            row = {
                "draft": float(draft),
                "displ": float(displ),
                "disp": float(displ),
                "lcb": float(lcb),
                "vcb": float(vcb),
                "lcf": float(lcf),
                "tpcm": float(tpcm),
                "mtcm_deg": float(mt_deg),
                "mtcm": float(mt_deg),
                "kml": float(kml),
                "kmt": float(kmt),
            }
            seen[float(draft)] = row
    for d in sorted(seen.keys()):
        rows.append(seen[d])

    ship = {
        "lpp": float(lpp),
        "lbp": float(lpp),
        "loa": float(loa) if loa is not None else float(lpp),
        "breadth": float(breadth) if breadth is not None else 0.0,
        "standard_sg": float(standard_sg),
        "sg_standard": float(standard_sg),
        "fore_corr": float(fore_corr),
        "aft_corr": float(aft_corr),
        "corr_divisor": float(corr_divisor),
        "draft_mark_divisor": float(corr_divisor),
        "hydrostatic": rows,
        "hydro": rows,
    }
    return ship


def survey(inputs, ship):
    fore_p = float(inputs["fore_p"])
    fore_s = float(inputs["fore_s"])
    mid_p = float(inputs["mid_p"])
    mid_s = float(inputs["mid_s"])
    aft_p = float(inputs["aft_p"])
    aft_s = float(inputs["aft_s"])
    sg = float(inputs["sg"])

    rows = ship["hydrostatic"] if "hydrostatic" in ship else ship["hydro"]
    drafts = [float(r["draft"]) for r in rows]
    lpp = float(ship["lpp"]) if "lpp" in ship else float(ship["lbp"])
    standard_sg = float(ship["standard_sg"]) if "standard_sg" in ship else 1.025
    fore_corr = float(ship["fore_corr"]) if "fore_corr" in ship else 1.2
    aft_corr = float(ship["aft_corr"]) if "aft_corr" in ship else 8.8
    divisor = float(ship["corr_divisor"]) if "corr_divisor" in ship else 140.0

    df = (fore_p + fore_s) / 2.0
    dm = (mid_p + mid_s) / 2.0
    da = (aft_p + aft_s) / 2.0

    # Booklet page 21: corrections from draft marks to FP / AP.
    # The divisor 140 m is the distance used in that printed formula,
    # not Lpp (150 m).
    apparent_trim = da - df
    d_fp = df - fore_corr * (apparent_trim / divisor)
    d_ap = da + aft_corr * (apparent_trim / divisor)
    d_ms = dm

    trim = d_ap - d_fp
    d_mm = (d_fp + 6.0 * d_ms + d_ap) / 8.0
    d_mean_ends = (d_fp + d_ap) / 2.0

    if d_mm < drafts[0] or d_mm > drafts[-1]:
        raise OutOfTable("mean draft outside hydrostatic table")

    disp_table = _interp(rows, drafts, d_mm, "displ")
    tpcm = _interp(rows, drafts, d_mm, "tpcm")
    lcf = _interp(rows, drafts, d_mm, "lcf")
    lcb = _interp(rows, drafts, d_mm, "lcb")
    mt_deg_mean = _interp(rows, drafts, d_mm, "mtcm_deg")

    # First trim correction, booklet page 22, item 3:
    # D2 = t * TPcm * 100 * (Lpp/2 - LCF) / Lpp   (LCF from AP)
    corr_trim1 = trim * tpcm * 100.0 * (lpp / 2.0 - lcf) / lpp

    # Second (Nemoto) trim correction. This is required to reproduce
    # the printed trimmed loading conditions, especially at large trim.
    # The table column headed MTcm is in MT-m/deg (see Sheet No.1:
    # "MTcm : (MT-m/deg)"). Convert moment per degree to moment per cm:
    # a trim of 1 degree is Lpp*100*tan(1 deg) cm of trim.
    # Corr2 = 50 * trim^2 / Lpp * (MCT at d+0.50 m - MCT at d-0.50 m)
    # with MCT in MT-m/cm. Values at d +/- 0.50 m are interpolated;
    # linear extrapolation from the end interval is used only for the
    # +/-0.50 m points if the mean draft itself is inside the table.
    cm_per_degree = lpp * 100.0 * math.tan(math.radians(1.0))
    mt_plus_deg = _interp(rows, drafts, d_mm + 0.5, "mtcm_deg")
    mt_minus_deg = _interp(rows, drafts, d_mm - 0.5, "mtcm_deg")
    mt_plus = mt_plus_deg / cm_per_degree
    mt_minus = mt_minus_deg / cm_per_degree
    corr_trim2 = 50.0 * trim * trim * (mt_plus - mt_minus) / lpp

    corr_density = (disp_table + corr_trim1 + corr_trim2) * (sg - standard_sg) / standard_sg
    disp_final = disp_table + corr_trim1 + corr_trim2 + corr_density

    return {
        "d_fp": float(d_fp),
        "d_ap": float(d_ap),
        "d_ms": float(d_ms),
        "trim": float(trim),
        "d_mm": float(d_mm),
        "d_m": float(d_mean_ends),
        "disp_table": float(disp_table),
        "corr_trim1": float(corr_trim1),
        "corr_trim2": float(corr_trim2),
        "corr_density": float(corr_density),
        "disp_final": float(disp_final),
        "df": float(df),
        "dm": float(dm),
        "da": float(da),
        "tpcm": float(tpcm),
        "lcf": float(lcf),
        "lcb": float(lcb),
        "mtcm": float(mt_deg_mean),
        "mtcm_deg": float(mt_deg_mean),
        "sg": float(sg),
    }
