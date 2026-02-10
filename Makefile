BUILD := build/
$(BUILD):
	mkdir $(BUILD)

#

SHADERS := $(wildcard shaders/*.metal)
METALLIB := $(BUILD)default.metallib

$(METALLIB): $(SHADERS)
	rm -f $(METALLIB)
	xcrun -sdk macosx metal -g -frecord-sources $(SHADERS) -o $(METALLIB)
shaders: $(METALLIB)

#

ECSLIB = $(BUILD)ecs.dylib

$(ECSLIB): c/ecs.c c/ecs.h c/ecs_network.c c/ecs_network.h
	gcc -Wall -Wextra -std=c11 -O2 -fPIC -shared c/ecs.c c/ecs_network.c -o $(ECSLIB)
c_lib: $(ECSLIB)

.PHONY: play test typecheck test_ecs
test_ecs: c/ecs.c c/ecs.h c/ecs_network.c c/ecs_network.h c/test_ecs.c
	gcc -Wall -Wextra -std=c11 -g -o build/test_ecs c/ecs.c c/ecs_network.c c/test_ecs.c
	./build/test_ecs

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

ARGS := --shaderslib="$(METALLIB)" \
	--ecslib="$(ECSLIB)"
SERVER_ARGS := $(ARGS) --scene=server --api=metal
EDITOR_ARGS := $(ARGS) --scene=client --api=tui

play: shaders deps c_lib
	$(VENV)bin/python -m q_engine.main $(SERVER_ARGS)

edit: deps c_lib
	$(VENV)bin/python -m q_engine.main $(EDITOR_ARGS)

test: dev-deps deps c_lib
	PYTHONPATH=py/src $(VENV)bin/python -m unittest q_tests.test_ecs
typecheck: dev-deps deps c_lib
	cd py/ && .venv/bin/ty check . --output-format=concise

