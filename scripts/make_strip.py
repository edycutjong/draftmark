"""Printable mini-barge draft-mark strip: ship-style metric marks at 1:10.

Ship marks: numerals 10 cm tall, bottom edge = stated draft, every 20 cm, the metre
mark carries an "M". At 1:10 that is 1 cm digits every 2 cm, "1M" at 10 cm, "2M" at
20 cm. White on dark red (SAM's tested concept is "white number").

    python scripts/make_strip.py OUT.pdf
Print at 100 % ("actual size"), A4 portrait, then check the 10 cm bar with a ruler.
"""
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

FONT = "Helvetica-Bold"
DIGIT_H_EM = 0.709  # Helvetica-Bold digit height (no descender), em units
DIGIT_H = 10 * mm  # 1:10 of a 10 cm ship numeral
FONT_SIZE = DIGIT_H / DIGIT_H_EM
ZERO_Y = 12 * mm  # page y of the strip's zero (bottom) edge
STRIP_W = 34 * mm
TOP_CM = 26  # last mark: "6" at 26 cm (digit top at 27 cm)
RED = (0.42, 0.06, 0.06)


def marks(top_cm=TOP_CM):
    """(draft_cm, label) for every mark, bottom edge = draft."""
    out = []
    for cm in range(2, top_cm + 1, 2):
        out.append((cm, f"{cm // 10}M" if cm % 10 == 0 else str(cm % 10)))
    return out


def strip(c, x0):
    top = ZERO_Y + (TOP_CM + 1.6) * 10 * mm
    c.setFillColorRGB(*RED)
    c.rect(x0, ZERO_Y, STRIP_W, top - ZERO_Y, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont(FONT, FONT_SIZE)
    for cm, label in marks():
        y = ZERO_Y + cm * 10 * mm
        c.drawString(x0 + 6 * mm, y, label)
    # zero edge marker: white tick inside the strip at the very bottom
    c.setStrokeColorRGB(1, 1, 1)
    c.setLineWidth(0.3)
    c.line(x0, ZERO_Y + 0.15, x0 + STRIP_W, ZERO_Y + 0.15)
    # cut marks outside the strip (black), on the zero line
    c.setStrokeColorRGB(0, 0, 0)
    for xs, xe in ((x0 - 8 * mm, x0 - 1 * mm), (x0 + STRIP_W + 1 * mm, x0 + STRIP_W + 8 * mm)):
        c.line(xs, ZERO_Y, xe, ZERO_Y)


def check_bar(c, x0):
    c.setFillColorRGB(0, 0, 0)
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.4)
    c.rect(x0, ZERO_Y, 2 * mm, 100 * mm, stroke=0, fill=1)
    for i in range(11):
        y = ZERO_Y + i * 10 * mm
        c.line(x0 + 2 * mm, y, x0 + 7 * mm, y)
    for i in range(101):
        y = ZERO_Y + i * mm
        c.line(x0 + 2 * mm, y, x0 + (4 if i % 5 else 5) * mm, y)
    c.setFont("Helvetica", 7)
    c.drawString(x0 + 8 * mm, ZERO_Y + 100 * mm - 1, "100 mm")
    c.drawString(x0 + 8 * mm, ZERO_Y - 1, "0")


def notes(c, x0):
    c.setFillColorRGB(0, 0, 0)
    t = c.beginText(x0, ZERO_Y + 255 * mm)
    t.setFont("Helvetica-Bold", 10)
    t.textLine("DraftMark mini-barge strip (1:10)")
    t.setFont("Helvetica", 8)
    for line in [
        "Print at 100 % / Actual size (no 'fit to page').",
        "Check: the black bar must be exactly 100 mm.",
        "Then check one 10-pitch span (2 -> 2M = 180 mm).",
        "Digits are 10 mm tall; bottom edge = draft.",
        "1M = 10 cm, 2M = 20 cm.",
        "Cut along the strip edges. The strip's",
        "BOTTOM edge is the zero (the cut marks).",
        "Laminate or cover fully with clear tape.",
        "Tape the zero edge at the box's outer",
        "bottom edge; photograph it against a ruler",
        "and write the offset (mm) in barge.md.",
        "Two strips: one per side (two-ruler check)",
        "or one spare.",
    ]:
        t.textLine(line)
    c.drawText(t)


def main(out):
    c = canvas.Canvas(out, pagesize=A4)
    c.setTitle("DraftMark mini-barge draft-mark strip 1:10")
    strip(c, 18 * mm)
    strip(c, 72 * mm)
    check_bar(c, 122 * mm)
    notes(c, 140 * mm)
    c.showPage()
    c.save()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "strip-print.pdf")
