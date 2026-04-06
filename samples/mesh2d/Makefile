ifeq ($(origin O), command line)
  BUILD_DIR := $(O)
else
  BUILD_DIR := .
endif

DEPS = build/

all: $(BUILD_DIR)/mesh2d.dylib $(BUILD_DIR)/mesh2d.h $(BUILD_DIR)/mesh2d.metallib

$(BUILD_DIR)/mesh2d.dylib: $(DEPS)/lock.toml mesh2d.m mesh2d.h
	clang -shared \
		mesh2d.m \
		-o $(BUILD_DIR)/mesh2d.dylib \
		-I $(DEPS) \
		-framework Metal \
		-framework MetalKit \
		-fobjc-arc \
		-fPIC

$(BUILD_DIR)/mesh2d.h: mesh2d.h
	cp mesh2d.h $(BUILD_DIR)/mesh2d.h

$(BUILD_DIR)/mesh2d.metallib: mesh2d.metal
	xcrun metal -c mesh2d.metal -o $(BUILD_DIR)/mesh2d.air
	xcrun metallib $(BUILD_DIR)/mesh2d.air -o $(BUILD_DIR)/mesh2d.metallib

$(DEPS)/lock.toml: manifest.toml
	mkdir -p $(DEPS)
	epk install --manifest=manifest.toml --build=$(DEPS)
