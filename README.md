# Kavyam (കാവ്യം): Malayalam typeface

Ancient soul. Modern clarity. Effortless reading.

**Status: pipeline scaffold. All outlines are placeholder boxes.** The glyph set,
OpenType shaping, build and tests work. The letterforms still have to be drawn.

## Layout

| Path | What |
|---|---|
| `data/ligatures_modern.txt` | Modern-lipi conjunct ligatures (one cluster per line) |
| `data/ligatures_traditional.txt` | Traditional-lipi ligatures, exposed as `ss01` |
| `features/*.fea` | OpenType features. `modern_ligatures.fea` and `traditional.fea` are **generated** |
| `tools/gen_sources.py` | One-time: creates placeholder UFOs and the designspace |
| `tools/gen_features.py` | Regenerates ligature features and syncs them into the UFOs |
| `sources/` | Light and Black masters (UFO), interpolated to Regular/Medium/Bold |
| `tests/test_shaping.py` | HarfBuzz shaping regression tests |

## Commands

```
make init       # once. Creates placeholder UFOs (refuses to overwrite drawn ones)
make features   # after editing data/*.txt or features/*.fea
make variable   # build/variable/Kavyam[wght].ttf
make static     # Light, Regular, Medium, Bold, Black
make web        # woff2 for all of the above
make test       # shaping tests
```

## Drawing workflow

1. Open `sources/Kavyam-Light.ufo` and `Kavyam-Black.ufo` in Fontra (or Glyphs).
2. Replace outlines. Keep glyph names, unicodes and point structure compatible
   between the two masters (same points, same order).
3. Never run `gen_sources.py --force` after this point.
4. `make test` after every change to features or ligature lists.

## Orthography

- **Modern lipi (default).** Only the clusters in `ligatures_modern.txt` ligate.
  Everything else shows a visible chandrakkala. Ra, ya and va signs come from
  `pref` and `pstf`.
- **Traditional lipi.** `ss01` swaps in `.trad` alternates and adds
  traditional-only ligatures. Planned: also bind it to the `MAL` language
  system so it switches on with `lang="ml"` and `font-language-override`.

## Open items

- Ligature lists need review by a Malayalam typographer.
- Mark and kern positioning (`mark`, `mkmk`, `kern`, `dist`) is not written yet.
- Reph and dot-reph (U+0D4E) rules, and U+0D3B/0D3C virama variants.
- Hinting: `ttfautohint` is not available in the Arch repos (AUR only).
- Latin, digits and punctuation are placeholders.
