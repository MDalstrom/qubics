ifeq ($(origin O), command line)
  BUILD_DIR := $(O)
else
  BUILD_DIR := .
endif

DEPS = build/

$(BUILD_DIR)/main: $(DEPS)/lock.toml main.c
	gcc -Wall -Wextra -std=c11 -O2 \
		-I$(DEPS) \
		main.c -o $(BUILD_DIR)/main

$(DEPS)/lock.toml: manifest.toml
	epk install --manifest=manifest.toml --build=$(DEPS)

