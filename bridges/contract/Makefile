ifeq ($(origin O), command line)
  BUILD_DIR := $(O)
else
  BUILD_DIR := .
endif

CONTRACT = contract.h
$(BUILD_DIR)/$(CONTRACT): $(CONTRACT)
	cp $(CONTRACT) $(BUILD_DIR)/$(CONTRACT)
