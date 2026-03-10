ifeq ($(origin O), command line)
  BUILD_DIR := $(O)
else
  BUILD_DIR := .
endif

$(BUILD_DIR)/ecs.dylib:
	@mkdir -p $(BUILD_DIR)
	gcc -Wall -Wextra -std=c11 -O2 -fPIC -shared ecs.c -o $(BUILD_DIR)/ecs.dylib

