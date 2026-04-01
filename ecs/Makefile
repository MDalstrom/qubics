ifeq ($(origin O), command line)
  BUILD_DIR := $(O)
else
  BUILD_DIR := .
endif

all: $(BUILD_DIR)/ecs.dylib $(BUILD_DIR)/ecs.h $(BUILD_DIR)/scheduler.h $(BUILD_DIR)/api.h

$(BUILD_DIR)/scheduler.h:
	@cp scheduler.h $(BUILD_DIR)/scheduler.h
$(BUILD_DIR)/ecs.h:
	@cp ecs.h $(BUILD_DIR)/ecs.h
$(BUILD_DIR)/api.h:
	@cp api.h $(BUILD_DIR)/api.h

$(BUILD_DIR)/ecs.dylib: ecs.c scheduler.c
	gcc -Wall -Wextra -std=c11 -O2 -fPIC -shared ecs.c scheduler.c -o $(BUILD_DIR)/ecs.dylib

.PHONY: test
test:
	gcc -Wall -Wextra -std=c11 -O2 scheduler_test.c scheduler.c -o scheduler_test
	$(BUILD_DIR)/scheduler_test
	rm scheduler_test
