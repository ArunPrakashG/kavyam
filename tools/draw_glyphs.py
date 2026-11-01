#!/usr/bin/env -S uv run
# /// script
# dependencies = ["ufoLib2", "fonttools"]
# ///
"""Draw the first real Kavyam letterforms into the master UFOs.

Glyphs are skeleton strokes swept by a broad nib (see strokes.py). Geometry is
in font units, baseline 0, letter height ~700, taken from measurements of the
reference specimen (reference/specimen.png, local only).

STATUS: first draft of six glyphs. Everything else is still a placeholder box.
Once you hand-edit a glyph in a UFO, delete it from GLYPHS below so this script
never overwrites your work.
"""
import sys
from pathlib import Path

import ufoLib2

sys.path.insert(0, str(Path(__file__).parent))
from kavyam_glyphs import ROOT  # noqa: E402
from strokes import Nib, arc, cubic, draw_ops, line, stroke_contour  # noqa: E402

# master style name -> (vertical stem v, horizontal stem h), font units.
# Ratios follow the weight row in the specimen: about 1 : 1.5 : 2 : 2.8 : 3.3.
NIBS = {"Light": (44, 28), "Black": (150, 95)}
OVERSHOOT = 10


def ell(cx, cy, rx_out, ry_out, nib, a0, a1):
    """Skeleton arc whose OUTER extents are rx_out / ry_out (weight-independent)."""
    return arc(cx, cy, rx_out - nib.a, ry_out - nib.b, a0, a1)


# Each glyph function returns [(segments, nib_scale, caps), ...]
def ka(nib):
    a, b = nib.a, nib.b
    bar = 418 - b
    oval = [ell(620, 350, 258, 350 + OVERSHOOT, nib, 250, 250 + 380)]
    lobes = [
        ell(223, 204, 223, 214, nib, 340, 90),   # left lobe, clockwise from lower right
        line((223, bar), (948, bar)),            # crossbar through the oval
        ell(948, 204, 223, 214, nib, 90, -125),  # right lobe ending in a hooked terminal
    ]
    return [(oval, (1, 1), ("round", "round")), (lobes, (1, 1), ("round", "round"))]


def aa(nib):
    return [([ell(261, 350, 261, 350 + OVERSHOOT, nib, 203.5, 525)], (1, 1), ("round", "round"))]


def va(nib):
    a, b = nib.a, nib.b
    xc = 962 - a * 1.25
    r = 85
    bowl = [ell(316, 350, 316, 350 + OVERSHOOT, nib, 254, -75)]
    base = [
        line((340, b), (xc - r, b)),
        arc(xc - r, b + r, r, r, -90, 0),
        line((xc, b + r), (xc, 700)),
    ]
    return [(bowl, (1, 1), ("round", "round")), (base, (1.25, 1), ("round", "flat"))]


def ya_sign(nib):
    a, b = nib.a, nib.b
    cx, cy = 270, -125
    rx, ry = 258 - a, 232 - b
    tail = [
        cubic((420, 665 - b), (240, 430), (cx + rx, 250), (cx + rx, cy)),
        arc(cx, cy, rx, ry, 0, -210),
    ]
    return [(tail, (1.1, 1.1), ("round", "round"))]


def anusvara(nib):
    ring = [ell(237, 244, 237, 244, nib, 90, 90 - 380)]
    return [(ring, (0.72, 0.85), ("round", "round"))]


def a_letter(nib):
    a, b = nib.a, nib.b
    top = 700 - b
    c_and_bar = [
        ell(402, 350, 402, 350 + OVERSHOOT, nib, 250, 90),  # big C, clockwise to the top
        line((402, top), (1400, top)),                      # top bar
        ell(1400, 375, 228, 325, nib, 90, 90 - 380),        # right ring
    ]
    upper = [ell(612, 500, 185, 190, nib, 160, -100)]
    lower = [ell(612, 238, 245, 182, nib, 100, -160)]
    stem = [line((987, top), (987, 0))]
    return [
        (c_and_bar, (1, 1), ("round", "round")),
        (upper, (1, 1), ("round", "round")),
        (lower, (1, 1), ("round", "round")),
        (stem, (1, 1), ("round", "flat")),
    ]


# glyph name -> (builder, left side bearing, advance width)
GLYPHS = {
    "ml_ka": (ka, 60, 1171 + 120),
    "ml_vowel_sign_aa": (aa, 60, 522 + 120),
    "ml_va": (va, 60, 962 + 120),
    "ml_ya_sign": (ya_sign, 40, 516 + 80),
    "ml_sign_anusvara": (anusvara, 60, 474 + 120),
    "ml_a": (a_letter, 60, 1628 + 120),
}


def main() -> None:
    for ufo_path in sorted((ROOT / "sources").glob("*.ufo")):
        font = ufoLib2.Font.open(ufo_path)
        v, h = NIBS[font.info.styleName]
        for name, (build, lsb, advance) in GLYPHS.items():
            glyph = font[name]
            glyph.clearContours()
            glyph.width = advance
            pen = glyph.getPen()
            for segs, (sv, sh), caps in build(Nib(v, h)):
                draw_ops(pen, stroke_contour(segs, Nib(v * sv, h * sh), caps), dx=lsb)
        font.save()
        print(f"drew {len(GLYPHS)} glyphs into {ufo_path.name}")


if __name__ == "__main__":
    main()
