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

SCHEMAS := $(wildcard schemas/*.fbs)

BSCHEMAS := $(BUILD)bfbs
$(BSCHEMAS).lock: $(SCHEMAS)
	rm $(wildcard $(BSCHEMAS)/*.bfbs) || true
	flatc -b --schema \
		-o $(BSCHEMAS) \
		$(SCHEMAS)
	touch $(BSCHEMAS).lock
b-schemas: $(BSCHEMAS).lock

PYSCHEMAS := py/src/q_generated/
$(PYSCHEMAS)__init__.py: $(SCHEMAS)
	rm -r $(PYSCHEMAS)* || true
	flatc --python \
		-o $(PYSCHEMAS)../ \
		--python \
		--python-typing \
		--python-gen-numpy \
		$(SCHEMAS)
py-schemas: $(PYSCHEMAS)__init__.py

RSSCHEMAS := rs/src/q_generated/
$(RSSCHEMAS)mod.rs: $(SCHEMAS)
	rm -r $(RSSCHEMAS)* || true
	flatc --rust \
		-o $(RSSCHEMAS) \
		$(SCHEMAS)
rs-schemas: $(RSSCHEMAS)mod.rs

#

ECSLIB = $(BUILD)ecs.dylib

$(ECSLIB): c/ecs.c c/ecs.h
	gcc -Wall -Wextra -std=c11 -O2 -fPIC -shared c/ecs.c -o $(ECSLIB)
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

ARGS := --api=metal \
	--scene=simple_c \
	--shaderslib="$(METALLIB)" \
	--ecslib="$(ECSLIB)"

.PHONY: play test typecheck test_ecs
test_ecs: c/ecs.c c/ecs.h c/test_ecs.c
	gcc -Wall -Wextra -std=c11 -g -o build/test_ecs c/ecs.c c/test_ecs.c
	./build/test_ecs

play: shaders deps py-schemas c_lib
	$(VENV)bin/python -m q_engine.main $(ARGS)
test: dev-deps deps c_lib
	PYTHONPATH=py/src $(VENV)bin/python -m unittest q_tests.test_ecs
typecheck: dev-deps deps c_lib
	cd py/ && .venv/bin/ty check . --output-format=concise
edit: deps c_lib
	$(VENV)bin/python -m q_editor.main $(ARGS)

