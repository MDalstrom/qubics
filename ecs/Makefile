ifeq ($(origin O), command line)
  BUILD_DIR := $(O)
else
  BUILD_DIR := .
endif

all: $(BUILD_DIR)/ecs.dylib $(BUILD_DIR)/ecs.h 

$(BUILD_DIR)/ecs.h:
	@cp ecs.h $(BUILD_DIR)/ecs.h

$(BUILD_DIR)/ecs.dylib: ecs.c
	gcc -Wall -Wextra -std=c11 -O2 -fPIC -shared ecs.c \
		-Wl,-install_name,@rpath/ecs.dylib \
		-o $@
