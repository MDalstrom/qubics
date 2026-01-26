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

PY := .venv/bin/python3

.PHONY: exp
.PHONY: run

run: .venv/.deps-installed | $(METALLIB)
	$(PY) -m q_engine.main --api=metal --scene=optimus
