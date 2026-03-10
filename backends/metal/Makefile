ifeq ($(origin O), command line)
  BUILD_DIR := $(O)
else
  BUILD_DIR := .
endif

SOURCES = metal.m

$(BUILD_DIR)/metal.dylib: $(SOURCES)
	clang -shared \
		-o $(BUILD_DIR)/metal.dylib $(SOURCES) \
		-framework Cocoa -framework Metal -framework MetalKit \
		-fobjc-arc \
		-fPIC
