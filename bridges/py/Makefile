ifeq ($(origin O), command line)
  BUILD_DIR := $(O)
else
  BUILD_DIR := .
endif

PYTHON        ?= python3.13
PYTHON_CONFIG := $(PYTHON)-config
PY_INCLUDES   := $(shell $(PYTHON_CONFIG) --includes)
PY_LDFLAGS    := $(shell $(PYTHON_CONFIG) --ldflags --embed)
SRC         := src/binder.c

DEPS = build/

$(BUILD_DIR)/binder.dylib: $(DEPS)/lock.toml $(SRC)
	gcc -Wall -Wextra -std=c11 -O2 -fPIC -shared \
		-I./$(BUILD) \
		$(PY_INCLUDES) $(PY_LDFLAGS) \
		$(SRC) -o $@

$(DEPS)/lock.toml: manifest.toml
	epk install --manifest=manifest.toml --build=$(DEPS)
