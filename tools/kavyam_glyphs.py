"""Shared glyph naming and glyph-set definitions for the Kavyam sources."""
import unicodedata
from pathlib import Path

from fontTools.agl import UV2AGL

ROOT = Path(__file__).resolve().parent.parent
VIRAMA = 0x0D4D
CONSONANTS = range(0x0D15, 0x0D3B)

NAME_OVERRIDES = {
    0x0020: "space",
    0x00A0: "nbspace",
    0x200C: "zwnj",
    0x200D: "zwj",
    0x25CC: "dottedcircle",
}

EXTRA_LATIN = [0x00A0, 0x20B9, 0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D,
               0x2026, 0x200C, 0x200D, 0x25CC]


def ml_name(cp: int) -> str:
    stem = unicodedata.name(chr(cp)).removeprefix("MALAYALAM ").removeprefix("LETTER ")
    return "ml_" + stem.lower().replace(" ", "_").replace("-", "_")


def short(cp: int) -> str:
    return unicodedata.name(chr(cp)).split()[-1].lower()


def glyph_name(cp: int) -> str:
    if cp in NAME_OVERRIDES:
        return NAME_OVERRIDES[cp]
    if 0x0D00 <= cp < 0x0D80:
        return ml_name(cp)
    return UV2AGL.get(cp) or f"uni{cp:04X}"


def malayalam_codepoints() -> list[int]:
    return [cp for cp in range(0x0D00, 0x0D80) if unicodedata.name(chr(cp), None)]


def encoded_codepoints() -> list[int]:
    return [0x0020] + list(range(0x21, 0x7F)) + malayalam_codepoints() + EXTRA_LATIN


def read_ligatures(path: Path) -> list[dict]:
    """Parse a ligature list: one consonant+virama+consonant(+...) cluster per line."""
    out = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        text = raw.split("#")[0].strip()
        if not text:
            continue
        cps = [ord(c) for c in text]
        for i, cp in enumerate(cps):
            want_virama = i % 2 == 1
            ok = cp == VIRAMA if want_virama else cp in CONSONANTS
            if not ok:
                raise ValueError(f"{path.name}:{lineno}: bad cluster {text!r} at index {i}")
        if len(cps) % 2 == 0:
            raise ValueError(f"{path.name}:{lineno}: cluster {text!r} must end on a consonant")
        out.append({
            "text": text,
            "seq": [glyph_name(cp) for cp in cps],
            "name": "ml_" + "_".join(short(cp) for cp in cps[::2]),
        })
    return out


def modern_ligatures() -> list[dict]:
    return read_ligatures(ROOT / "data" / "ligatures_modern.txt")


def traditional_ligatures() -> list[dict]:
    return read_ligatures(ROOT / "data" / "ligatures_traditional.txt")
