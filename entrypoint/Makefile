ifeq ($(origin O), command line)
  BUILD_DIR := $(O)
else
  BUILD_DIR := .
endif

DEPS = build/

$(BUILD_DIR)/main: entrypoint.c adapter.c
	gcc -Wall -Wextra -std=c11 -O2 \
		-I$(DEPS) \
		entrypoint.c adapter.c \
		$(DEPS)/ecs/ecs.dylib \
		$(DEPS)/scheduler/scheduler.dylib \
		-o $@
