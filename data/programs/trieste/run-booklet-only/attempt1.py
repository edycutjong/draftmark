import math
import bisect
import re


def _to_float(x):
    try:
        return float(str(x).replace(",", "").strip())
    except Exception:
        return None


def parse_booklet(booklet):
    pages = {}
    if isinstance(booklet, dict):
        pages = booklet.get("pages", {}) or {}
    # Order pages numerically when possible
    items = []
    for k in list(pages.keys()):
        try:
            n = int(str(k))
        except Exception:
            n = 0
        items.append((n, str(k), pages[k]))
    items.sort(key=lambda t: (t[0], t[1]))
    texts = []
    page_texts = {}
    for n, k, v in items:
        s = v if isinstance(v, str) else str(v)
        texts.append(s)
        page_texts[k] = s
    full = "\n".join(texts)

    def search_float(pattern, default=None):
        m = re.search(pattern, full)
        if not m:
            return default
        v = _to_float(m.group(1))
        return default if v is None else v

    loa = search_float(r"Length\s+Overall\s+([0-9]+\.[0-9]+)\s*m")
    lpp = search_float(r"Length\s+Between\s+Perpendiculars\s+([0-9]+\.[0-9]+)\s*m", 150.0)
    breadth = search_float(r"Breadth\s+Molded\s+([0-9]+\.[0-9]+)\s*m")
    summer_draft = search_float(r"Summer\s+Draft\s+([0-9]+\.[0-9]+)\s*m")
    if summer_draft is None:
        summer_draft = search_float(r"Design\s+Draft\s+([0-9]+\.[0-9]+)\s*m")
    standard_sg = search_float(r"Water\s+Specific\s+Gravity\s+([0-9]+\.[0-9]+)", 1.025)
    if standard_sg is None:
        standard_sg = 1.025

    # Draft-mark correction formula constants from page 21:
    # dFP = df - [1.200 * ((da - df) / 140)]
    # dAP = da + [8.800 * ((da - df) / 140)]
    fore_corr = 1.2
    aft_corr = 8.8
    mark_span = 140.0
    m = re.search(r"dFP\s*=\s*df\s*-\s*\[\s*([0-9]+\.[0-9]+)\s*\*\s*\(\s*\(\s*da\s*-\s*df\s*\)\s*/\s*([0-9]+\.?[0-9]*)\s*\)\s*\]", full)
    if m:
        v1 = _to_float(m.group(1))
        v2 = _to_float(m.group(2))
        if v1 is not None:
            fore_corr = v1
        if v2 is not None and v2 != 0:
            mark_span = v2
    m2 = re.search(r"dAP\s*=\s*da\s*\+\s*\[\s*([0-9]+\.[0-9]+)\s*\*\s*\(\s*\(\s*da\s*-\s*df\s*\)\s*/\s*([0-9]+\.?[0-9]*)\s*\)\s*\]", full)
    if m2:
        v1 = _to_float(m2.group(1))
        v2 = _to_float(m2.group(2))
        if v1 is not None:
            aft_corr = v1
        if v2 is not None and v2 != 0:
            mark_span = v2

    # Draft mark positions as printed (informational)
    mark_pos = {}
    mp = re.search(r"FORE\s+Fr\.\s*([0-9]+)", full)
    if mp:
        mark_pos["fore_frame"] = mp.group(1)
    mp = re.search(r"MID\s+Fr\.\s*([0-9]+)\s*-\s*([0-9]+)\s*mm", full)
    if mp:
        mark_pos["mid_frame"] = mp.group(1)
        mark_pos["mid_offset_mm"] = _to_float(mp.group(2))
    mp = re.search(r"AFT\s+Fr\.\s*([0-9]+)", full)
    if mp:
        mark_pos["aft_frame"] = mp.group(1)
    mark_pos["fore_correction"] = float(fore_corr)
    mark_pos["aft_correction"] = float(aft_corr)
    mark_pos["mark_span"] = float(mark_span)

    # Hydrostatic table parsing.
    # Columns: Draft Displ LCBf VCB LCFf TPcm MTcm KML KMT
    # KML may be printed with a thousand-separator space, e.g. "1 394.363",
    # giving 10 whitespace tokens instead of 9.
    hydrostatic = []
    seen = {}
    for line in full.splitlines():
        parts = line.strip().split()
        if len(parts) not in (9, 10):
            continue
        if not parts[2].endswith("f") or not parts[4].endswith("f"):
            continue
        try:
            draft = float(parts[0])
            displ = float(parts[1])
            lcb = float(parts[2][:-1])
            vcb = float(parts[3])
            lcf = float(parts[4][:-1])
            tpcm = float(parts[5])
            mtcm = float(parts[6])
            if len(parts) == 10:
                kml = float(parts[7] + parts[8])
                kmt = float(parts[9])
            else:
                kml = float(parts[7])
                kmt = float(parts[8])
        except Exception:
            continue
        if draft < 0.1 or draft > 30.0:
            continue
        if draft in seen:
            continue
        row = {
            "draft": float(draft),
            "displ": float(displ),
            "lcb": float(lcb),
            "vcb": float(vcb),
            "lcf": float(lcf),
            "tpcm": float(tpcm),
            "mtcm": float(mtcm),
            "kml": float(kml),
            "kmt": float(kmt),
        }
        seen[draft] = row
        hydrostatic.append(row)
    hydrostatic.sort(key=lambda r: r["draft"])

    ship = {
        "loa": loa,
        "lpp": float(lpp) if lpp is not None else 150.0,
        "breadth": breadth,
        "summer_draft": summer_draft,
        "design_draft": summer_draft,
        "standard_sg": float(standard_sg),
        "fore_correction": float(fore_corr),
        "aft_correction": float(aft_corr),
        "mark_span": float(mark_span),
        "draft_marks": mark_pos,
        "hydrostatic": hydrostatic,
        "hydrostatic_table": hydrostatic,
        "table": hydrostatic,
    }
    return ship


def _interp(table, drafts, x, key):
    if x <= drafts[0]:
        return float(table[0][key])
    if x >= drafts[-1]:
        return float(table[-1][key])
    i = bisect.bisect_left(drafts, x)
    if i < len(drafts) and drafts[i] == x:
        return float(table[i][key])
    x0 = drafts[i - 1]
    x1 = drafts[i]
    y0 = float(table[i - 1][key])
    y1 = float(table[i][key])
    if x1 == x0:
        return float(y0)
    f = (x - x0) / (x1 - x0)
    return float(y0 + f * (y1 - y0))


def survey(inputs, ship):
    # inputs is a dict with the draft readings and sg
    if isinstance(inputs, dict):
        get = inputs.get
    else:
        # Fallback: treat mapping-like via keys not available; expect dict per spec
        get = lambda k, d=None: d

    fore_p = float(get("fore_p"))
    fore_s = float(get("fore_s"))
    mid_p = float(get("mid_p"))
    mid_s = float(get("mid_s"))
    aft_p = float(get("aft_p"))
    aft_s = float(get("aft_s"))
    sg = float(get("sg", 1.025))

    if isinstance(ship, dict):
        lpp = float(ship.get("lpp", 150.0))
        fore_corr = float(ship.get("fore_correction", 1.2))
        aft_corr = float(ship.get("aft_correction", 8.8))
        mark_span = float(ship.get("mark_span", 140.0))
        standard_sg = float(ship.get("standard_sg", 1.025))
        table = ship.get("hydrostatic") or ship.get("hydrostatic_table") or ship.get("table") or []
        # draft_marks may carry the constants
        dm = ship.get("draft_marks")
        if isinstance(dm, dict):
            if "fore_correction" in dm:
                fore_corr = float(dm["fore_correction"])
            if "aft_correction" in dm:
                aft_corr = float(dm["aft_correction"])
            if "mark_span" in dm:
                mark_span = float(dm["mark_span"])
    else:
        lpp = 150.0
        fore_corr = 1.2
        aft_corr = 8.8
        mark_span = 140.0
        standard_sg = 1.025
        table = []

    df = (fore_p + fore_s) / 2.0
    dm_read = (mid_p + mid_s) / 2.0
    da = (aft_p + aft_s) / 2.0

    # Booklet page 21 corrections to perpendiculars
    diff = (da - df) / mark_span if mark_span != 0 else 0.0
    d_fp = df - fore_corr * diff
    d_ms = dm_read
    d_ap = da + aft_corr * diff

    trim = d_ap - d_fp
    d_m = (d_ap + d_fp) / 2.0
    # Mean draft with correction for deflection (quarter / mean-of-means draft)
    d_mm = (d_fp + 6.0 * d_ms + d_ap) / 8.0
    deflection = d_m - d_ms

    if not table:
        exc = globals().get("OutOfTable", ValueError)
        raise exc("hydrostatic table is empty")

    # Normalise table rows (allow alternative key spellings)
    norm = []
    for r in table:
        if not isinstance(r, dict):
            continue
        try:
            row = {
                "draft": float(r.get("draft")),
                "displ": float(r.get("displ", r.get("disp", r.get("displacement")))),
                "lcb": float(r.get("lcb", 0.0)),
                "vcb": float(r.get("vcb", 0.0)),
                "lcf": float(r.get("lcf", 0.0)),
                "tpcm": float(r.get("tpcm", r.get("tpc", 0.0))),
                "mtcm": float(r.get("mtcm", r.get("mtc", 0.0))),
                "kml": float(r.get("kml", 0.0)),
                "kmt": float(r.get("kmt", 0.0)),
            }
        except Exception:
            continue
        norm.append(row)
    norm.sort(key=lambda r: r["draft"])
    if not norm:
        exc = globals().get("OutOfTable", ValueError)
        raise exc("hydrostatic table is empty")

    drafts = [r["draft"] for r in norm]
    if d_mm < drafts[0] or d_mm > drafts[-1]:
        exc = globals().get("OutOfTable", ValueError)
        raise exc("mean draft outside hydrostatic table")

    disp_table = _interp(norm, drafts, d_mm, "displ")
    tpcm = _interp(norm, drafts, d_mm, "tpcm")
    lcf = _interp(norm, drafts, d_mm, "lcf")
    mtcm = _interp(norm, drafts, d_mm, "mtcm")
    lcb = _interp(norm, drafts, d_mm, "lcb")

    # Booklet page 22: first (only) trim correction
    # D2 = [ t * TPcm * 100 * (Lpp/2 - L.C.F.) ] / Lpp   (LCF from A.P.)
    corr_trim1 = (trim * tpcm * 100.0 * (lpp / 2.0 - lcf)) / lpp if lpp != 0 else 0.0
    corr_trim2 = 0.0

    # Density correction: D3 = (D1 + D2) * (S.G. - 1.025) / 1.025
    corr_density = (disp_table + corr_trim1) * (sg - standard_sg) / standard_sg if standard_sg != 0 else 0.0

    disp_final = disp_table + corr_trim1 + corr_trim2 + corr_density

    result = {
        "df": float(df),
        "dm": float(dm_read),
        "da": float(da),
        "d_fp": float(d_fp),
        "d_ap": float(d_ap),
        "d_ms": float(d_ms),
        "trim": float(trim),
        "d_m": float(d_m),
        "d_mm": float(d_mm),
        "deflection": float(deflection),
        "disp_table": float(disp_table),
        "corr_trim1": float(corr_trim1),
        "corr_trim2": float(corr_trim2),
        "corr_density": float(corr_density),
        "disp_final": float(disp_final),
        "tpcm": float(tpcm),
        "mtcm": float(mtcm),
        "lcf": float(lcf),
        "lcb": float(lcb),
        "sg": float(sg),
        "lpp": float(lpp),
    }
    return result
