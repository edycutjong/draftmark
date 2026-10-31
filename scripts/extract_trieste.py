"""Extract our own numbers from the public Trieste trim & stability booklet.

The PDF itself never enters this repo (licence unstated); we commit only the numbers we
extracted, with page references and the source URL (data/booklets/trieste/CITATION.md).
Two independent extractions (pdftotext -layout and pypdf) are reconciled row by row;
any disagreement fails the script.

  python scripts/extract_trieste.py /path/to/booklet.pdf
"""
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "booklets" / "trieste"
URL = ("https://moodle2.units.it/pluginfile.php/582393/mod_resource/content/0/"
       "Esercitazione%201.pdf")

HYD = re.compile(
    r"^\s*(\d+\.\d{3})\s+([\d ]*\d\.\d{3})\s+(\d+\.\d{3})([fa])\s+(\d+\.\d{3})\s+(\d+\.\d{3})([fa])\s+"
    r"(\d+\.\d{2})\s+([\d ]*\d\.\d{2})\s+([\d ]*\d\.\d{3})\s+(\d+\.\d{3})\s*$")
CASE = re.compile(r"^\s*CASE\s+(\d+(?:\.\d+)?)\s+-\s+(.+?)\s*$")
FLOAT = {
    "draft_fp": re.compile(r"Draft FP\s+(\d+\.\d+)\s*m"),
    "draft_ms": re.compile(r"Draft MS\s+(\d+\.\d+)\s*m"),
    "draft_ap": re.compile(r"Draft AP\s+(\d+\.\d+)\s*m"),
    "disp_printed": re.compile(r"Displacement\s+([\d ]*\d\.\d+)\s*MT"),
    "sg": re.compile(r"WaterSpgr\s+(\d\.\d+)"),
}
MARK = re.compile(r"(FORE|MID|AFT)\.([ps])\s+(\d+\.\d{3})\s*\(m\)")


def num(s: str) -> float:
    return float(s.replace(" ", ""))


def pages_layout(pdf: Path) -> list[str]:
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    return txt.split("\f")


def parse_hydro(pages: list[str]) -> list[dict]:
    rows = []
    for pno, page in enumerate(pages, start=1):
        hits = [(ln, HYD.match(line)) for ln, line in enumerate(page.splitlines(), start=1)]
        hits = [(ln, m) for ln, m in hits if m]
        if len(hits) < 5:  # the hydrostatic table pages only
            continue
        for ln, m in hits:
            if True:
                g = m.groups()
                rows.append({"draft": float(g[0]), "disp": num(g[1]), "lcb": float(g[2]), "lcb_side": g[3],
                             "vcb": float(g[4]), "lcf": float(g[5]), "lcf_side": g[6], "tpcm": float(g[7]),
                             "mtcm": num(g[8]), "kml": num(g[9]), "kmt": float(g[10]), "page": pno, "line": ln})
    return rows


def parse_conditions(pages: list[str]) -> list[dict]:
    conds = []
    for pno, page in enumerate(pages, start=1):
        if "Draft At Draft Marks" not in page:
            continue
        lines = page.splitlines()
        head = next((CASE.match(x) for x in lines if CASE.match(x)), None)
        text = "\n".join(lines)
        row = {"cond_id": head.group(1) if head else f"p{pno}", "title": head.group(2) if head else "", "page": pno}
        for k, rx in FLOAT.items():
            m = rx.search(text)
            row[k] = num(m.group(1)) if m else None
            row[k + "_line"] = next((i for i, x in enumerate(lines, 1) if m and m.group(0) in x), None)
        for pos, side, v in MARK.findall(text):
            row[f"{pos.lower()}_{side}"] = float(v)
        row["marks_line"] = next((i for i, x in enumerate(lines, 1) if "Draft At Draft Marks" in x), None)
        conds.append(row)
    return conds


def pypdf_pages(pdf: Path, pages: list[int]) -> dict[int, str]:
    r = PdfReader(str(pdf))
    return {p: r.pages[p - 1].extract_text() or "" for p in pages}


def reconcile(conds: list[dict], hydro: list[dict], pdf: Path) -> list[str]:
    """Second extraction with pypdf: every printed number must appear on the same page."""
    issues = []
    need = sorted({c["page"] for c in conds} | {h["page"] for h in hydro})
    alt = pypdf_pages(pdf, need)
    for c in conds:
        t = re.sub(r"(?<=\d) (?=\d{3}\.)", "", alt[c["page"]])
        for k in ("disp_printed", "sg", "draft_fp", "draft_ms", "draft_ap", "fore_p", "fore_s", "mid_p", "mid_s",
                  "aft_p", "aft_s"):
            v = c.get(k)
            if v is None:
                issues.append(f"cond {c['cond_id']}: {k} missing in pdftotext")
                continue
            dec = {"disp_printed": 1, "sg": 3}.get(k, 3)
            if f"{v:.{dec}f}" not in t:
                issues.append(f"cond {c['cond_id']}: {k}={v:.{dec}f} not found by pypdf on p{c['page']}")
    for h in hydro:
        t = re.sub(r"(?<=\d) (?=\d{3}\.)", "", alt[h["page"]])
        for k, dec in (("draft", 3), ("disp", 3), ("lcf", 3), ("tpcm", 2)):
            if f"{h[k]:.{dec}f}" not in t:
                issues.append(f"hydro {h['draft']}: {k}={h[k]} not found by pypdf on p{h['page']}")
    return issues


def main(pdf_path: str):
    pdf = Path(pdf_path)
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    pages = pages_layout(pdf)
    hydro = parse_hydro(pages)
    conds = parse_conditions(pages)
    issues = reconcile(conds, hydro, pdf)
    drafts = [h["draft"] for h in hydro]
    assert drafts == sorted(drafts) and len(set(drafts)) == len(drafts), "table not monotone"
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "hydrostatics.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(hydro[0]))
        w.writeheader()
        w.writerows(hydro)
    fields = ["cond_id", "title", "page", "fore_p", "fore_s", "mid_p", "mid_s", "aft_p", "aft_s", "sg",
              "draft_fp", "draft_ms", "draft_ap", "disp_printed", "marks_line", "disp_printed_line", "sg_line"]
    with (OUT / "conditions.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(conds)
    print(json.dumps({"pdf_sha256": sha, "pages": len(pages), "hydro_rows": len(hydro),
                      "hydro_range": [drafts[0], drafts[-1]], "hydro_pages": sorted({h["page"] for h in hydro}),
                      "conditions": len(conds), "condition_pages": [c["page"] for c in conds],
                      "reconcile_issues": issues}, indent=1))
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
