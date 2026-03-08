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

#

RENDER3D = $(BUILD)render_3d.dylib

$(RENDER3D): c/render_3d.m c/render_3d.h c/ecs.h
	clang -dynamiclib -o $(RENDER3D) c/render_3d.m \
		-framework Metal -framework MetalKit -framework Cocoa \
		-ObjC -fobjc-arc
render_3d: $(RENDER3D)

.PHONY: play test typecheck test
test: c/ecs.c c/ecs.h c/network.c c/network.h c/test.c
	gcc -Wall -Wextra -std=c11 -g -o build/test c/ecs.c c/network.c c/test.c
	./build/test

#

METALBOOT := swift/libmetalboot.dylib
METALBOOT_SRC := swift/qubics\ Shared/MetalBoot.swift \
	swift/qubics\ Shared/ECSWorldManager.m

$(METALBOOT): $(METALBOOT_SRC)
	cd swift && swiftc -emit-library -o libmetalboot.dylib \
		-import-objc-header qubics\ Shared/qubics-Bridging-Header.h \
		qubics\ Shared/MetalBoot.swift \
		qubics\ Shared/ECSWorldManager.m \
		-framework Metal -framework MetalKit -framework Cocoa
swift_lib: $(METALBOOT)

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
	--ecslib="$(ECSLIB)" \
	--metalbootlib="$(METALBOOT)" \
	--render3dlib="$(RENDER3D)"

play: shaders deps c_lib swift_lib render_3d
	$(VENV)bin/python -m q_engine.main $(ARGS) --scene=server --api=metal

edit: deps c_lib
	$(VENV)bin/python -m q_engine.main $(ARGS) --scene=client --api=tui

typecheck: dev-deps deps c_lib
	cd py/ && .venv/bin/ty check . --output-format=concise

