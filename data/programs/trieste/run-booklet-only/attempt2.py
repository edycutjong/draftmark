import re
import bisect
import math


def _float_or_none(text):
    try:
        return float(text)
    except Exception:
        return None


def _search_number(pattern, text, default=None):
    m = re.search(pattern, text)
    if m:
        v = _float_or_none(m.group(1))
        if v is not None:
            return v
    return default


def parse_booklet(booklet):
    pages = {}
    if isinstance(booklet, dict):
        raw_pages = booklet.get("pages", {})
        if isinstance(raw_pages, dict):
            pages = raw_pages

    def page_key(item):
        k = item[0]
        try:
            return (0, int(k), "")
        except Exception:
            return (1, 0, str(k))

    ordered = sorted(pages.items(), key=page_key)
    texts = []
    for _k, v in ordered:
        texts.append(str(v))
    text = "\n".join(texts)

    lpp = _search_number(r"Length Between Perpendiculars\s+([0-9]+(?:\.[0-9]+)?)\s*m", text, 150.0)
    loa = _search_number(r"Length Overall\s+([0-9]+(?:\.[0-9]+)?)\s*m", text)
    breadth = _search_number(r"Breadth Molded\s+([0-9]+(?:\.[0-9]+)?)\s*m", text)
    summer_draft = _search_number(r"(?:Summer Draft|Design Draft)\s+([0-9]+(?:\.[0-9]+)?)\s*m", text)
    standard_sg = _search_number(r"Water Specific Gravity\s+([0-9]+(?:\.[0-9]+)?)", text, 1.025)
    if standard_sg is None:
        standard_sg = 1.025

    # Draft-mark correction formulae from page 21:
    # dFP = df - [1.200 * ((da - df) / 140)]
    # dAP = da + [8.800 * ((da - df) / 140)]
    fore_factor = 1.2
    aft_factor = 8.8
    mark_span = 140.0
    m = re.search(r"dFP\s*=\s*df\s*-\s*\[\s*([0-9]+(?:\.[0-9]+)?)\s*\*\s*\(\(da\s*-\s*df\)\s*/\s*([0-9]+(?:\.[0-9]+)?)\)\]", text)
    if m:
        v1 = _float_or_none(m.group(1))
        v2 = _float_or_none(m.group(2))
        if v1 is not None:
            fore_factor = v1
        if v2 is not None:
            mark_span = v2
    m = re.search(r"dAP\s*=\s*da\s*\+\s*\[\s*([0-9]+(?:\.[0-9]+)?)\s*\*\s*\(\(da\s*-\s*df\)\s*/\s*([0-9]+(?:\.[0-9]+)?)\)\]", text)
    if m:
        v1 = _float_or_none(m.group(1))
        v2 = _float_or_none(m.group(2))
        if v1 is not None:
            aft_factor = v1
        if v2 is not None:
            mark_span = v2

    # Hydrostatic table: Draft, Displ, LCB, VCB, LCF, TPcm, MTcm, KML, KMT
    # KML above 1000 is printed with a space as thousands separator,
    # e.g. "1 394.363", giving 10 tokens instead of 9.
    table = []
    seen = {}
    for line in text.splitlines():
        tokens = line.strip().split()
        if len(tokens) not in (9, 10):
            continue
        if not re.match(r"^[0-9]+\.[0-9]+$", tokens[0]):
            continue
        if not re.match(r"^[0-9]+\.[0-9]+$", tokens[1]):
            continue
        try:
            draft = float(tokens[0])
            disp = float(tokens[1])
            lcb = float(tokens[2].rstrip("f"))
            vcb = float(tokens[3])
            lcf = float(tokens[4].rstrip("f"))
            tpcm = float(tokens[5])
            mtcm = float(tokens[6])
            if len(tokens) == 10:
                if not re.match(r"^[0-9]+$", tokens[7]):
                    continue
                if not re.match(r"^[0-9]+\.[0-9]+$", tokens[8]):
                    continue
                kml = float(tokens[7] + tokens[8])
                kmt = float(tokens[9])
            else:
                kml = float(tokens[7])
                kmt = float(tokens[8])
        except Exception:
            continue
        if draft < 0.1 or draft > 20.0:
            continue
        if disp <= 0.0:
            continue
        if draft in seen:
            continue
        seen[draft] = True
        table.append({
            "draft": float(draft),
            "disp": float(disp),
            "displ": float(disp),
            "lcb": float(lcb),
            "vcb": float(vcb),
            "lcf": float(lcf),
            "tpcm": float(tpcm),
            "mtcm": float(mtcm),
            "kml": float(kml),
            "kmt": float(kmt),
        })
    table.sort(key=lambda r: r["draft"])

    ship = {
        "lpp": float(lpp),
        "length_between_perpendiculars": float(lpp),
        "loa": loa,
        "breadth": breadth,
        "summer_draft": summer_draft,
        "standard_sg": float(standard_sg),
        "sg_standard": float(standard_sg),
        "fore_factor": float(fore_factor),
        "aft_factor": float(aft_factor),
        "mark_span": float(mark_span),
        "draft_mark_span": float(mark_span),
        "hydrostatic": table,
        "hydrostatics": table,
        "table": table,
    }
    return ship


def _interp(table, drafts, x, field):
    i = bisect.bisect_right(drafts, x)
    if i <= 0:
        return float(table[0][field])
    if i >= len(table):
        return float(table[-1][field])
    lo = table[i - 1]
    hi = table[i]
    d0 = float(lo["draft"])
    d1 = float(hi["draft"])
    if d1 == d0:
        return float(lo[field])
    frac = (x - d0) / (d1 - d0)
    return float(lo[field]) + frac * (float(hi[field]) - float(lo[field]))


def survey(inputs, ship):
    fore_p = float(inputs["fore_p"])
    fore_s = float(inputs["fore_s"])
    mid_p = float(inputs["mid_p"])
    mid_s = float(inputs["mid_s"])
    aft_p = float(inputs["aft_p"])
    aft_s = float(inputs["aft_s"])
    sg = float(inputs["sg"])

    df = (fore_p + fore_s) / 2.0
    dm = (mid_p + mid_s) / 2.0
    da = (aft_p + aft_s) / 2.0

    lpp = float(ship.get("lpp", ship.get("length_between_perpendiculars", 150.0)))
    fore_factor = float(ship.get("fore_factor", 1.2))
    aft_factor = float(ship.get("aft_factor", 8.8))
    mark_span = float(ship.get("mark_span", ship.get("draft_mark_span", 140.0)))
    standard_sg = float(ship.get("standard_sg", ship.get("sg_standard", 1.025)))

    table = ship.get("hydrostatic") or ship.get("hydrostatics") or ship.get("table") or []
    if not table:
        raise OutOfTable("hydrostatic table is empty")

    apparent = da - df
    d_fp = df - fore_factor * (apparent / mark_span)
    d_ms = dm
    d_ap = da + aft_factor * (apparent / mark_span)

    trim = d_ap - d_fp
    d_m = (d_ap + d_fp) / 2.0
    d_mm = (d_fp + 6.0 * d_ms + d_ap) / 8.0

    drafts = [float(r["draft"]) for r in table]
    if not math.isfinite(d_mm) or d_mm < drafts[0] or d_mm > drafts[-1]:
        raise OutOfTable("mean draft outside hydrostatic table")

    disp_table = _interp(table, drafts, d_mm, "disp")
    tpcm = _interp(table, drafts, d_mm, "tpcm")
    lcf = _interp(table, drafts, d_mm, "lcf")
    mtcm = _interp(table, drafts, d_mm, "mtcm")
    lcb = _interp(table, drafts, d_mm, "lcb")
    vcb = _interp(table, drafts, d_mm, "vcb")

    # Booklet first (and only) trim correction D2, page 22 / sheet page 26:
    # D2 = [ t * TPcm * 100 * (Lpp/2 - L.C.F.) ] / Lpp   tons
    corr_trim1 = trim * tpcm * 100.0 * (lpp / 2.0 - lcf) / lpp
    corr_trim2 = 0.0

    # Density correction D3 = (D1 + D2) * (S.G. - 1.025) / 1.025
    corr_density = (disp_table + corr_trim1) * (sg - standard_sg) / standard_sg
    disp_final = disp_table + corr_trim1 + corr_trim2 + corr_density

    return {
        "d_fp": float(d_fp),
        "d_ap": float(d_ap),
        "d_ms": float(d_ms),
        "trim": float(trim),
        "d_mm": float(d_mm),
        "d_m": float(d_m),
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
        "mtcm": float(mtcm),
        "lcb": float(lcb),
        "vcb": float(vcb),
        "sg": float(sg),
        "lpp": float(lpp),
    }
