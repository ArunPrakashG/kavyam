#!/usr/bin/env -S uv run
# /// script
# dependencies = ["uharfbuzz"]
# ///
"""Shaping regression tests: run text through HarfBuzz and check glyph names.

Uses the built static fonts, so it works with placeholder or real outlines.
"""
import sys
from pathlib import Path

import uharfbuzz as hb

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "build" / "static" / "Kavyam-Regular.ttf"

# (label, text, features, expected glyph names in visual order)
CASES = [
    ("geminate ligature", "ക്ക", {}, ["ml_ka_ka"]),
    ("nasal ligature", "ങ്ക", {}, ["ml_nga_ka"]),
    ("nta ligature", "ന്റ", {}, ["ml_na_rra"]),
    ("akhand ksha", "ക്ഷ", {}, ["ml_ka_ssa"]),
    ("akhand jnya", "ജ്ഞ", {}, ["ml_ja_nya"]),
    ("no ligature -> visible chandrakkala", "ക്ല",
     {}, ["ml_ka", "ml_sign_virama", "ml_la"]),
    ("ra sign sits left of consonant", "ക്ര", {}, ["ml_ra_sign", "ml_ka"]),
    ("ya sign sits right", "ക്യ", {}, ["ml_ka", "ml_ya_sign"]),
    ("va sign sits right", "ക്വ", {}, ["ml_ka", "ml_va_sign"]),
    ("vowel sign e is pre-base", "കെ", {}, ["ml_vowel_sign_e", "ml_ka"]),
    ("split vowel o", "കൊ", {}, ["ml_vowel_sign_e", "ml_ka", "ml_vowel_sign_aa"]),
    ("split vowel oo", "കോ", {}, ["ml_vowel_sign_ee", "ml_ka", "ml_vowel_sign_aa"]),
    ("split vowel au", "കൌ", {}, ["ml_vowel_sign_e", "ml_ka", "ml_au_length_mark"]),
    ("legacy chillu n (ZWJ)", "ന്‍", {}, ["ml_chillu_n"]),
    ("atomic chillu n", "ൻ", {}, ["ml_chillu_n"]),
    ("ss01 traditional-only ligature", "ക്ത", {"ss01": True}, ["ml_ka_ta.trad"]),
    ("ss01 traditional alternate", "ക്ക", {"ss01": True}, ["ml_ka_ka.trad"]),
    ("ss01 off keeps modern form", "ക്ത", {}, ["ml_ka", "ml_sign_virama", "ml_ta"]),
]


def shape(font: hb.Font, text: str, features: dict) -> list[str]:
    buf = hb.Buffer()
    buf.add_str(text)
    buf.direction = "ltr"
    buf.script = "Mlym"
    buf.language = "ml"
    hb.shape(font, buf, features)
    return [font.glyph_to_string(i.codepoint) for i in buf.glyph_infos]


def main() -> int:
    if not FONT.exists():
        sys.exit(f"missing {FONT}; run `make static` first")
    font = hb.Font(hb.Face(FONT.read_bytes()))
    failures = 0
    for label, text, feats, want in CASES:
        got = shape(font, text, feats)
        ok = got == want
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {label}")
        if not ok:
            print(f"      text={text!r} features={feats}\n      want={want}\n      got ={got}")
    print(f"\n{len(CASES) - failures}/{len(CASES)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
