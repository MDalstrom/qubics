ifeq ($(origin O), command line)
  BUILD_DIR := $(O)
else
  BUILD_DIR := .
endif

NAME  := rs-hello
DYLIB := librs_hello.dylib

all: $(BUILD_DIR)/$(DYLIB) $(BUILD_DIR)/manifest.toml

$(BUILD_DIR)/$(DYLIB): src/lib.rs
	cargo build
	@cp target/debug/$(DYLIB) $(BUILD_DIR)/

$(BUILD_DIR)/manifest.toml: $(BUILD_DIR)/$(DYLIB)
	@cp manifest.toml $(BUILD_DIR)/
