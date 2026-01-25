.venv:
	python3 -m venv .venv

.venv/.deps-installed: pyproject.toml | .venv
	.venv/bin/python -m pip install -e .
	touch .venv/.deps-installed

BUILD := build
SHADERS := shaders

AIR := $(BUILD)/shaders.air
METALLIB := $(BUILD)/default.metallib

$(METALLIB): $(SHADERS)/$(wildcard *.metal)
	mkdir $(BUILD) || rm -f $(METALLIB)
	xcrun -sdk macosx metal $(SHADERS)/*.metal -o $(METALLIB)
	# xcrun -sdk macosx metallib $(AIR) -o $(METALLIB)

PY := .venv/bin/python3

.PHONY: exp
.PHONY: run

exp: .venv/.deps-installed | $(METALLIB)
	rm -f output.mp4;
	$(PY) src/main.py --output=output.mp4 --duration=120 --fps=60 --width=225 --height=400 --watch=true

run: .venv/.deps-installed | $(METALLIB)
	$(PY) src/main.py --width=480 --height=854 --watch=true

alt: .venv/.deps-installed | $(METALLIB)
	$(PY) -m q_engine.alt.main --api=metal --scene=optimus
