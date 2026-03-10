BUILD_DIR = $(abspath ./build)

.PHONY: run
run:
	mkdir -p $(BUILD_DIR)
	$(MAKE) -C backends/metal O=$(BUILD_DIR)
	$(MAKE) -C ecs O=$(BUILD_DIR)
	$(MAKE) -C samples/metal-renderer O=$(BUILD_DIR)

	./entrypoint/.venv/bin/python -m pip install -e entrypoint
	./entrypoint/.venv/bin/python -m qubics.main \
		--backend=$(BUILD_DIR)/metal.dylib \
		--engine=$(BUILD_DIR)/ecs.dylib
