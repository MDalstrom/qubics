O ?= .
PLUGIN = metal_renderer
BRIDGE_WRAPPER = $(abspath ../../bridges/py/qubics/plugin_wrapper.c)

$(O)/$(PLUGIN).dylib:
	mkdir -p $(O)
	INC=$$(.venv/bin/python -c "import sysconfig; print('-I' + sysconfig.get_path('include'))") ; \
	gcc -Wall -Wextra -std=c11 -O2 -fPIC -shared $$INC \
	-DMODULE_NAME=\"metal_renderer.renderer\" \
	-DFUNC_NAME=\"mk_system\" \
	-DEXPORTED_FUNC_NAME=metal_renderer_system \
	$(BRIDGE_WRAPPER) -o $(O)/$(PLUGIN).dylib -undefined dynamic_lookup
