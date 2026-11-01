.PHONY: all init features variable static web test clean

DS := sources/Kavyam.designspace

all: variable static web

# One-time: create PLACEHOLDER UFOs. Refuses to overwrite drawn masters.
init:
	uv run tools/gen_sources.py
	uv run tools/gen_features.py

# Regenerate ligature features and sync them into the UFOs.
features:
	uv run tools/gen_features.py

variable: features
	fontmake -m $(DS) -o variable --output-path "build/variable/Kavyam[wght].ttf"

static: features
	fontmake -m $(DS) -i -o ttf --output-dir build/static

web: variable static
	for f in build/variable/*.ttf build/static/*.ttf; do woff2_compress "$$f"; done

test: variable static
	uv run tests/test_shaping.py

clean:
	rm -rf build instance_ufo sources/instances
	mkdir -p build
