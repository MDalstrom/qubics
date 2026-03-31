BUILD_DIR  = $(abspath ./build)
LOCK_FILE = $(BUILD_DIR)/lock.toml

.PHONY: run

run: install
	$(MAKE) -C entrypoint O=$(BUILD_DIR)
	epk watch --lock-file $(LOCK_FILE) --build-dir $(BUILD_DIR) & QUBICS_PATH=$(BUILD_DIR) $(BUILD_DIR)/main

install: manifest.toml
	mkdir -p $(BUILD_DIR)
	rm -f $(LOCK_FILE)
	epk install --lock-file $(LOCK_FILE) --build-dir $(BUILD_DIR)
