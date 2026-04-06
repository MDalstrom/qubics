BUILD_DIR  = $(abspath ./build)
LOCK_FILE = $(BUILD_DIR)/lock.toml

.PHONY: run

run: install
	epk install --lock-file $(LOCK_FILE) --build-dir $(BUILD_DIR) --rebuild
	epk watch --lock-file $(LOCK_FILE) --build-dir $(BUILD_DIR) \
		& QUBICS_PATH=$(BUILD_DIR) \
		DYLD_LIBRARY_PATH=$(DYLD_LIBRARY_PATH):$(BUILD_DIR)/ecs:$(BUILD_DIR)/scheduler $(BUILD_DIR)/entrypoint/main

install: manifest.toml
	mkdir -p $(BUILD_DIR)
	rm -f $(LOCK_FILE)
	epk install --lock-file $(LOCK_FILE) --build-dir $(BUILD_DIR) --rebuild

clean:
	rm -r $(BUILD_DIR)
