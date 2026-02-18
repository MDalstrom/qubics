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

$(ECSLIB): c/ecs.c c/ecs.h
	gcc -Wall -Wextra -std=c11 -O2 -fPIC -shared c/ecs.c -o $(ECSLIB)
c_lib: $(ECSLIB)

.PHONY: play test typecheck test
test: c/ecs.c c/ecs.h c/network.c c/network.h c/test.c
	gcc -Wall -Wextra -std=c11 -g -o build/test c/ecs.c c/network.c c/test.c
	./build/test

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

play: shaders deps c_lib
	$(VENV)bin/python -m q_engine.main $(ARGS) --scene=server --api=metal

edit: deps c_lib
	$(VENV)bin/python -m q_engine.main $(ARGS) --scene=client --api=tui

typecheck: dev-deps deps c_lib
	cd py/ && .venv/bin/ty check . --output-format=concise

