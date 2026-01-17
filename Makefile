.venv:
	python3 -m venv .venv

.venv/.deps-installed: pyproject.toml | .venv
	.venv/bin/pip install .
	touch .venv/.deps-installed

BUILD := build
SHADERS := shaders

AIR := $(BUILD)/shaders.air
METALLIB := $(BUILD)/default.metallib

$(METALLIB): $(SHADERS) | $(BUILD) 
	xcrun -sdk macosx metal -c $(SHADERS)/*.metal -o $(AIR);
	xcrun -sdk macosx metallib $(AIR) -o $(METALLIB)

PY := .venv/bin/python3

.PHONY: exp
.PHONY: run

exp: .venv/.deps-installed | $(METALLIB)
	rm -f output.mp4;
	$(PY) src/main.py --output=output.mp4 --duration=60 --fps=60 --width=1080 --height=1920

run: .venv/.deps-installed | $(METALLIB)
	$(PY) src/main.py --fps=120 --duration=5 --width=480 --height=854 --watch=false
