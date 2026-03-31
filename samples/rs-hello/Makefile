ifeq ($(origin O), command line)
  BUILD_DIR := $(O)
else
  BUILD_DIR := .
endif

$(BUILD_DIR)/rs-hello.dylib: src/lib.rs Cargo.toml
	cargo build --release
	cp target/release/librs_hello.dylib $(BUILD_DIR)
