#!/usr/bin/env -S uv run
# /// script
# dependencies = ["ufoLib2", "fonttools"]
# ///
"""Generate PLACEHOLDER masters (Light, Black) and the designspace.

Every glyph is a hollow box so shaping, interpolation and the build can be
tested before any real letterform is drawn. Replace the outlines in the UFOs
(for example in Fontra); keep the glyph names and unicodes.
"""
import sys
from pathlib import Path

import ufoLib2
from fontTools.designspaceLib import (AxisDescriptor, DesignSpaceDocument,
                                      InstanceDescriptor, SourceDescriptor)

sys.path.insert(0, str(Path(__file__).parent))
from kavyam_glyphs import (ROOT, encoded_codepoints, glyph_name,  # noqa: E402
                           modern_ligatures, traditional_ligatures)

FAMILY = "Kavyam"
MASTERS = {"Light": (300, 30), "Black": (900, 120)}  # name: (weight, stem)
INSTANCES = {"Light": 300, "Regular": 400, "Medium": 500, "Bold": 700, "Black": 900}

LETTER_W, SIGN_W, DIGIT_W, LATIN_W = 650, 400, 600, 550
NO_OUTLINE = {"space", "nbspace", "zwnj", "zwj"}


def frame(pen, x0, y0, x1, y1, t):
    """Hollow box: outer counter-clockwise, inner clockwise (UFO convention)."""
    pen.moveTo((x0, y0)); pen.lineTo((x1, y0)); pen.lineTo((x1, y1)); pen.lineTo((x0, y1))
    pen.closePath()
    pen.moveTo((x0 + t, y0 + t)); pen.lineTo((x0 + t, y1 - t))
    pen.lineTo((x1 - t, y1 - t)); pen.lineTo((x1 - t, y0 + t))
    pen.closePath()


def kind(name: str) -> str:
    if name in NO_OUTLINE:
        return "blank"
    if name.endswith("_sign") or "_sign_" in name or name.startswith("ml_sign"):
        return "sign"
    return "letter"


def glyph_specs() -> dict[str, dict]:
    """name -> {unicodes, width}; insertion order is the glyph order."""
    specs = {".notdef": {"unicodes": [], "width": 500}}
    for cp in encoded_codepoints():
        name = glyph_name(cp)
        if name in {"space", "nbspace"}:
            width = 250
        elif name in {"zwnj", "zwj"}:
            width = 0
        elif 0x0D00 <= cp < 0x0D80:
            width = SIGN_W if kind(name) == "sign" else LETTER_W
        elif 0x30 <= cp <= 0x39:
            width = DIGIT_W
        else:
            width = LATIN_W
        specs[name] = {"unicodes": [cp], "width": width}
    for sign in ("ml_ra_sign", "ml_ya_sign", "ml_va_sign"):
        specs[sign] = {"unicodes": [], "width": SIGN_W}
    for lig in modern_ligatures():
        n = len(lig["seq"]) // 2 + 1
        specs[lig["name"]] = {"unicodes": [], "width": int(LETTER_W * n * 0.85)}
    for lig in traditional_ligatures():
        n = len(lig["seq"]) // 2 + 1
        specs[lig["name"] + ".trad"] = {"unicodes": [], "width": int(LETTER_W * n * 0.85)}
    return specs


def build_master(style: str, weight: int, stem: int, specs: dict) -> ufoLib2.Font:
    font = ufoLib2.Font()
    info = font.info
    info.familyName, info.styleName = FAMILY, style
    info.unitsPerEm = 1000
    info.ascender, info.descender = 1000, -400
    info.capHeight, info.xHeight = 700, 480
    info.openTypeOS2WeightClass = weight
    info.openTypeOS2TypoAscender, info.openTypeOS2TypoDescender = 1000, -400
    info.openTypeOS2TypoLineGap = 0
    info.openTypeOS2WinAscent, info.openTypeOS2WinDescent = 1150, 550
    info.openTypeHheaAscender, info.openTypeHheaDescender = 1000, -400
    info.openTypeHheaLineGap = 0
    info.versionMajor, info.versionMinor = 0, 1
    info.copyright = "PLACEHOLDER outlines - not for release."
    font.features.text = ""  # filled in by tools/gen_features.py

    for name, spec in specs.items():
        g = font.newGlyph(name)
        g.width = spec["width"]
        g.unicodes = spec["unicodes"]
        k = "letter" if name == ".notdef" else kind(name)
        if k == "blank":
            continue
        w = spec["width"]
        if k == "sign":
            frame(g.getPen(), 60, 380, w - 60, 680, stem)
        else:
            frame(g.getPen(), 50, 0, w - 50, 700, stem)
    font.lib["public.glyphOrder"] = list(specs)
    return font


def main() -> None:
    src = ROOT / "sources"
    src.mkdir(exist_ok=True)
    existing = sorted(src.glob("*.ufo"))
    if existing and "--force" not in sys.argv:
        sys.exit("Refusing to overwrite existing UFOs (they may contain real drawings). "
                 "Pass --force to regenerate the placeholders.")
    specs = glyph_specs()

    ds = DesignSpaceDocument()
    axis = AxisDescriptor(name="weight", tag="wght", minimum=300, default=300, maximum=900)
    ds.addAxis(axis)
    for style, (weight, stem) in MASTERS.items():
        path = src / f"{FAMILY}-{style}.ufo"
        build_master(style, weight, stem, specs).save(path, overwrite=True)
        ds.addSource(SourceDescriptor(filename=path.name, familyName=FAMILY,
                                      styleName=style, location={"weight": weight}))
    for style, weight in INSTANCES.items():
        ds.addInstance(InstanceDescriptor(
            filename=f"instances/{FAMILY}-{style}.ufo", familyName=FAMILY,
            styleName=style, styleMapFamilyName=FAMILY if style in ("Regular", "Bold")
            else f"{FAMILY} {style}",
            styleMapStyleName="bold" if style == "Bold" else "regular",
            location={"weight": weight}))
    ds.write(src / f"{FAMILY}.designspace")
    print(f"wrote {len(MASTERS)} masters, {len(specs)} glyphs each")


if __name__ == "__main__":
    main()
