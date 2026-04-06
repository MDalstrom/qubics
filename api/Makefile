ifeq ($(origin O), command line)
  BUILD_DIR := $(O)
else
  BUILD_DIR := .
endif

all: $(BUILD_DIR)/contract.h

$(BUILD_DIR)/contract.h: contract.h
	@cp contract.h $@
