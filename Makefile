BUILD := build/
$(BUILD):
	mkdir $(BUILD)

#

SHADERS := $(wildcard shaders/*.metal)
METALLIB := $(BUILD)/default.metallib

$(METALLIB): $(SHADERS)
	rm -f $(METALLIB)
	xcrun -sdk macosx metal -g -frecord-sources $(SHADERS) -o $(METALLIB)
shaders: $(METALLIB)

#

SCHEMAS := $(wildcard schemas/*.fbs)
PYSCHEMAS := py/src/q_generated/

$(PYSCHEMAS)__init__.py: $(SCHEMAS)
	rm -r $(PYSCHEMAS)/* || true
	flatc --python -o $(PYSCHEMAS) $(SCHEMAS)
	touch $(PYSCHEMAS)__init__.py
py-schemas: $(PYSCHEMAS)__init__.py

#

ECSLIB = $(BUILD)libecs_core.dylib

$(ECSLIB): c/ecs_core.c c/ecs_core.h
	gcc -Wall -Wextra -std=c11 -O2 -fPIC -shared c/ecs_core.c -o $(ECSLIB)
c_lib: $(ECSLIB)

#

VENV := py/.venv/
PYPROJECT := py/pyproject.toml

$(VENV):
	python3.13 -m venv $(VENV)

$(VENV).lock: $(PYPROJECT) $(VENV)
	$(VENV)bin/python -m pip install -e py
	touch $(VENV).lock
deps: $(VENV).lock

$(VENV).devlock: $(PYPROJECT) $(VENV)
	$(VENV)bin/python -m pip install -e "py[dev]"
	touch $(VENV).devlock
dev-deps: $(VENV).devlock

ARGS := --api=metal --scene=simple_c --shaderslib="$(METALLIB)"

.PHONY: play test typecheck
play: shaders deps py-schemas c_lib
	$(VENV)bin/python -m q_engine.main $(ARGS)
test: dev-deps deps c_lib
	$(VENV)bin/python -m unittest py/src/q_tests/test_ecs.py
typecheck: dev-deps deps c_lib
	cd py/ && .venv/bin/ty check . --output-format=concise

#

edit:
	cd rs && cargo run
