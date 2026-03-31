ifeq ($(origin O), command line)
  BUILD_DIR := $(O)
else
  BUILD_DIR := .
endif

DEPS = build/

$(BUILD_DIR)/metal.dylib: $(DEPS)/lock.toml metal.m
	clang -shared \
		-o $(BUILD_DIR)/metal.dylib metal.m \
		-I $(DEPS)/backend-contracts \
		-framework Cocoa -framework Metal -framework MetalKit \
		-fobjc-arc \
		-fPIC

$(DEPS)/lock.toml: manifest.toml
	mkdir -p $(DEPS)
	epk install --manifest=manifest.toml --build=$(DEPS)

