.venv:
	python3 -m venv .venv

.venv/.deps-installed: pyproject.toml | .venv
	.venv/bin/python -m pip install -e .
	touch .venv/.deps-installed

BUILD := build
SHADERS := shaders

AIR := $(BUILD)/shaders.air
METALLIB := $(BUILD)/default.metallib

$(METALLIB): $(wildcard $(SHADERS/)*.metal)
	mkdir $(BUILD) || rm -f $(METALLIB)
	xcrun -sdk macosx metal -g -frecord-sources $(SHADERS)/*.metal -o $(METALLIB)

PY := .venv/bin/python3

.PHONY: exp
.PHONY: run

run: .venv/.deps-installed | $(METALLIB)
	$(PY) -m q_engine.main --api=metal

.PHONY: test
test: .venv/.deps-installed
	$(PY) -m unittest src/q_tests/test_ecs.py
