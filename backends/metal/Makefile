ifeq ($(origin O), command line)
  BUILD_DIR := $(O)
else
  BUILD_DIR := .
endif


all: $(BUILD_DIR)/metal.dylib $(BUILD_DIR)/contract.h

$(BUILD_DIR)/contract.h: contract.h
	@cp -r contract.h $(BUILD_DIR)/contract.h


DEPS = build/
$(BUILD_DIR)/metal.dylib: $(DEPS)/lock.toml metal.m
	clang -shared \
		-o $(BUILD_DIR)/metal.dylib metal.m \
		-I $(DEPS) \
		-framework Cocoa -framework Metal -framework MetalKit \
		-fobjc-arc \
		-fPIC

$(DEPS)/lock.toml: manifest.toml
	mkdir -p $(DEPS)
	epk install --manifest=manifest.toml --build=$(DEPS)

