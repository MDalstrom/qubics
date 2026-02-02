BUILD := build/
SHADERS := $(wildcard src/**/*.metal)
METALLIB := $(BUILD)default.metallib

$(METALLIB): $(SHADERS)
	mkdir $(BUILD) || rm -f $(METALLIB)
	xcrun -sdk macosx metal -g -frecord-sources $(SHADERS) -o $(METALLIB)
shaders: $(METALLIB)

.venv:
	python3 -m venv .venv
.venv/.lock: pyproject.toml .venv
	.venv/bin/pip install -e .
	touch .venv/.lock
dependencies: .venv/.lock

BIN := .venv/bin/

.PHONY: run test typecheck
run: shaders dependencies
	$(BIN)python -m q_engine.main --api=metal --scene=2d
test: dependencies
	$(BIN)python -m unittest src/q_tests/test_ecs.py
typecheck: dependencies
	$(BIN)ty check --output-format concise
