"""Check the landing page, the pitch deck and the judge path against the evidence they quote.

  python scripts/check_landing.py            # exit 1 on any mismatch

1. The waterline replayed by both pages (the DS array) equals draft.frames[].d_m of the recorded run, rounded to
   4 decimals, and D / U equal draft.result.d_m / u_rep_m exactly.
2. Every number in the visible text of all three pages (landing, deck, /judge) appears somewhere in the evidence corpus (evidence/*.md,
   README.md, docs/*.md, public/runs/*.json). A number that greps nowhere is printed as UNSOURCED.
Re-run after any change to the recorded runs (P1e regenerates them) or to the page copy.
"""
import html as htmllib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / "public/index.html", ROOT / "public/deck/index.html"]  # replay the waterline (check 1)
TEXT_PAGES = PAGES + [ROOT / "public/judge/index.html"]  # numbers must grep in the corpus (check 2)
RUN = ROOT / "public/runs/rec-db7x-20261031.json"
# numbers that are page furniture, not claims (slide/line numbers, frame indices, viewport sizes)
FURNITURE = {"0", "1", "2", "3", "4", "5", "6", "8", "10", "12", "001", "002", "003", "004", "005", "006", "007", "008",
             "009", "010", "011", "012", "004.1", "004.2", "004.3", "002.1", "002.2", "002.3", "59", "1920", "1080", "2026", "31", "3.1", "1.3",
             "1.0", "7", "9", "11", "13", "14", "20"}


def visible_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|svg|title)\b.*?</\1>", " ", raw)
    raw = re.sub(r"(?is)<head\b.*?</head>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return htmllib.unescape(raw).replace("−", "-").replace(" ", " ")


def corpus() -> str:
    parts = [p.read_text(errors="ignore") for p in sorted((ROOT / "evidence").glob("*.md"))]
    parts += [(ROOT / "README.md").read_text()] + [p.read_text() for p in sorted((ROOT / "docs").glob("*.md"))]
    for p in sorted((ROOT / "public/runs").glob("*.json")):
        parts.append(p.read_text())
    return "\n".join(parts).replace("−", "-")


def main() -> int:
    bad = 0
    run = json.loads(RUN.read_text())
    want = [round(f["d_m"], 4) for f in run["draft"]["frames"]]
    res = run["draft"]["result"]
    for page in PAGES:
        src = page.read_text()
        m = re.search(r"var DS = (\[[^\]]+\])", src)
        if not m or json.loads(m.group(1)) != want:
            print(f"FAIL {page.relative_to(ROOT)}: DS differs from {RUN.name} draft.frames[].d_m")
            bad += 1
        for name, key in (("D", "d_m"), ("U", "u_rep_m")):
            mm = re.search(rf"\b{name} = ([0-9.]+)", src)
            if not mm or float(mm.group(1)) != res[key]:
                print(f"FAIL {page.relative_to(ROOT)}: {name} != draft.result.{key} ({res[key]})")
                bad += 1
    text_corpus = corpus()
    for page in TEXT_PAGES:
        nums = sorted(set(re.findall(r"(?<![\w.])\d[\d,]*(?:\.\d+)?", visible_text(page.read_text()))))
        unsourced = []
        for n in nums:
            bare = n.replace(",", "")
            if bare in FURNITURE:
                continue
            variants = {bare, bare.rstrip("0").rstrip(".") if "." in bare else bare}
            if not any(re.search(rf"(?<![\d.]){re.escape(v)}(?![\d])", text_corpus) for v in variants):
                unsourced.append(n)
        status = "PASS" if not unsourced else "FAIL"
        print(f"{status} {page.relative_to(ROOT)}: {len(nums)} numbers, unsourced: {unsourced or 'none'}")
        bad += bool(unsourced)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
