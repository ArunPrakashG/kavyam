#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pillow"]
# ///
"""Render docs/preview.png (used in README.md) from the built static fonts.

Needs `make static` first and `hb-view` (harfbuzz-utils) on PATH.
"""
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "build" / "static"
OUT = ROOT / "docs" / "preview.png"

BG, INK, MUTED, RULE = "#f6ecd9", "#3b1c0a", "#8a7358", "#dccaa6"
W, H = 1600, 850
WEIGHTS = ["Light", "Regular", "Medium", "Bold", "Black"]


def shape(font: Path, text: str, size: int) -> Image.Image:
    """Render text with HarfBuzz and return an RGBA image with a transparent background."""
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "t.png"
        subprocess.run(
            ["hb-view", f"--font-size={size}", "--margin=0", "--background=ffffff00",
             f"--foreground={INK[1:]}ff", "-o", str(png), str(font), text],
            check=True)
        return Image.open(png).convert("RGBA")


def label_font(size: int) -> ImageFont.FreeTypeFont:
    path = subprocess.run(["fc-match", "-f", "%{file}", "sans"], capture_output=True,
                          text=True, check=True).stdout
    return ImageFont.truetype(path, size)


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    small, tiny = label_font(26), label_font(22)

    d.text((60, 44), "KAVYAM  ·  A MALAYALAM TYPEFACE", font=small, fill=MUTED)
    d.line((60, 88, W - 60, 88), fill=RULE, width=2)

    title = shape(STATIC / "Kavyam-Bold.ttf", "കാവ്യം", 340)
    img.paste(title, ((W - title.width) // 2, 110), title)

    d.line((60, 620, W - 60, 620), fill=RULE, width=2)
    col = (W - 120) // len(WEIGHTS)
    for i, name in enumerate(WEIGHTS):
        glyph = shape(STATIC / f"Kavyam-{name}.ttf", "അ", 120)
        cx = 60 + col * i + col // 2
        img.paste(glyph, (cx - glyph.width // 2, 660), glyph)
        w = d.textlength(name, font=tiny)
        d.text((cx - w / 2, 800), name, font=tiny, fill=MUTED)

    OUT.parent.mkdir(exist_ok=True)
    img.save(OUT, optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)} {img.size}")


if __name__ == "__main__":
    main()
