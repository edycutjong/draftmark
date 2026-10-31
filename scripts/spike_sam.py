"""P1a spike: SAM 3.1 video on a prepared 2x crop -> raw glyphs -> mark tokens per frame.

  python scripts/spike_sam.py .cache/clips/dB7X_t45.mp4 [--concepts "white number|water"]
Raw SAM text is cached under .cache/sam/ (gitignored: derived from third-party clips);
a second run reuses the cache and makes no API call.
"""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from _common import CACHE, meta

from api.core import marks, sam


def run(clip: Path, concepts: list[str], run_id: str, frames: int) -> dict[str, str]:
    out = {}
    todo = []
    for c in concepts:
        p = CACHE / "sam" / f"{clip.stem}__{c.replace(' ', '_')}.txt"
        if p.exists():
            out[c] = p.read_text()
        else:
            todo.append((c, p))
    if todo:
        cl = meta.Client(run_id=run_id)
        url = meta.data_url(clip, "video/mp4")

        def one(cp):
            c, p = cp
            resp = cl.sam(c, url, video=True, frames=frames, feature=f"sam video '{c}' {clip.stem}")
            txt = meta.output_text(resp)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(txt)
            return c, txt, resp.get("id")

        with ThreadPoolExecutor(2) as ex:
            for c, txt, rid in ex.map(one, todo):
                out[c] = txt
                print(f"  {c!r}: {len(txt)} chars, response {rid}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("--concepts", default="white number|water")
    ap.add_argument("--scale", type=float, default=1.0, help="mark system scale: 1.0 ship, 0.1 barge")
    a = ap.parse_args()
    clip = Path(a.clip)
    info = json.loads(clip.with_suffix(".json").read_text())
    texts = run(clip, a.concepts.split("|"), f"p1a-sam-{clip.stem}", info["frames"])
    num = sam.parse(texts["white number"])
    wat = sam.parse(texts["water"])
    nf, wf = sam.by_frame(num), sam.by_frame(wat)
    system = marks.MarkSystem(scale=a.scale)
    rows = []
    for i in range(info["frames"]):
        g = nf.get(i, [])
        try:
            toks = marks.group_glyphs(g, system)
            cap = False
        except marks.ObjectCapError:
            toks, cap = [], True
        rows.append({"frame": i, "glyphs": len(g), "tokens": len(toks), "multi": sum(t.n_glyphs > 1 for t in toks),
                     "water": len(wf.get(i, [])), "cap": cap})
    n = info["frames"]
    summ = {
        "clip": clip.stem, "frames": n,
        "frames_with_numerals": sum(r["tokens"] >= 3 for r in rows),
        "frames_with_water": sum(r["water"] > 0 for r in rows),
        "median_glyphs": sorted(r["glyphs"] for r in rows)[n // 2],
        "median_tokens": sorted(r["tokens"] for r in rows)[n // 2],
        "max_glyphs": max(r["glyphs"] for r in rows),
        "object_cap_frames": sum(r["cap"] for r in rows),
        "parsers_agree": [(o.frame, o.obj_id, o.box) for o in sam.parse_own(texts["white number"])]
        == [(o.frame, o.obj_id, o.box) for o in num],
    }
    out = CACHE / "sam" / f"{clip.stem}__summary.json"
    out.write_text(json.dumps({"summary": summ, "rows": rows}, indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
