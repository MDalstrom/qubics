ifeq ($(origin O), command line)
  BUILD_DIR := $(O)
else
  BUILD_DIR := .
endif

all: $(BUILD_DIR)/scheduler.dylib $(BUILD_DIR)/scheduler.h

$(BUILD_DIR)/scheduler.h:
	@cp scheduler.h $@

$(BUILD_DIR)/scheduler.dylib: scheduler.c
	gcc -Wall -Wextra -std=c11 -O2 -fPIC -shared \
		-I. \
		scheduler.c \
		-Wl,-install_name,@rpath/scheduler.dylib \
		-lpthread \
		-o $@
