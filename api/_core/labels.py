"""Spark 1.3 reads which mark token is which ("13M", "8", ...) on an annotated crop.

The model only names the painted strings; code converts them to drafts and confirms
them (marks.check_labels). Labels never come from SAM.
"""
from __future__ import annotations

import json

import io

from PIL import Image, ImageDraw, ImageFont

from . import meta
from .marks import MarkSystem, Token

PROMPT = (
    "This image is an enlarged crop of a ship's hull draft marks (metric). Each numbered cyan box surrounds one "
    "painted mark. Read the mark inside every box exactly as painted. Whole-metre marks are a number followed by "
    "'M' (for example '7M' or '15M'); the marks between them are single even digits 2, 4, 6 or 8. A mark may be "
    "partly under water: read what is painted. If a box is unreadable answer '?'. Return JSON mapping each box "
    "number to its mark."
)


def _font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def annotate(frame: Image.Image, tokens: list[Token]) -> tuple[Image.Image, dict[str, str]]:
    """Draw numbered token union boxes (top -> bottom); returns the image and {box_number: track}."""
    img = frame.convert("RGB").copy()
    d = ImageDraw.Draw(img)
    f = _font(22)
    numbering = {}
    for k, t in enumerate(sorted(tokens, key=lambda t: t.box[3]), start=1):
        x0, y0, x1, y1 = (int(round(v)) for v in t.box)
        d.rectangle((x0 - 3, y0 - 3, x1 + 2, y1 + 2), outline=(0, 255, 255), width=2)
        d.text((max(0, x0 - 30), y0 - 2), str(k), fill=(0, 255, 255), font=f)
        numbering[str(k)] = t.track
    return img, numbering


def schema(numbers: list[str], system: MarkSystem) -> dict:
    enum = system.labels_enum() + ["?"]
    return {
        "type": "object",
        "properties": {n: {"type": "string", "enum": enum} for n in numbers},
        "required": numbers,
        "additionalProperties": False,
    }


def read(client: meta.Client, img: Image.Image, numbering: dict[str, str], system: MarkSystem,
         feature: str = "spark label read") -> tuple[dict[str, str], dict]:
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    url = meta.bytes_data_url(buf.getvalue(), "image/jpeg")
    body = {
        "model": meta.SPARK,
        "input": [{"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": PROMPT},
            {"type": "input_image", "image_url": url}]}],
        "text": {"format": {"type": "json_schema", "name": "draft_mark_labels", "strict": True,
                            "schema": schema(list(numbering), system)}},
    }
    resp = client.responses(body, feature)
    raw = json.loads(meta.output_text(resp))
    by_track = {numbering[k]: v for k, v in raw.items() if k in numbering and v != "?"}
    return by_track, {"response_id": resp.get("id"), "raw": raw}
