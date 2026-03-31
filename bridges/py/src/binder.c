#include <Python.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#include "ecs/ecs.h"
#include "ecs/scheduler.h"
#include "bridge-contracts/contract.h"

PluginSystems qubics_plugin(Registry *registry) {
  if (!Py_IsInitialized()) {
    Py_Initialize();
    PyEval_SaveThread(); // release GIL — callbacks will manage it via PyGILState
  }

  PyGILState_STATE gstate = PyGILState_Ensure();

  const char *qubics_path = getenv("QUBICS_PATH");
  if (qubics_path) {
    PyObject *sys_mod = PyImport_ImportModule("sys");
    PyObject *path = PyObject_GetAttrString(sys_mod, "path");

    PyObject *entry = PyUnicode_FromString(qubics_path);
    PyList_Insert(path, 0, entry);
    Py_DECREF(entry);

    Py_DECREF(path);
    Py_DECREF(sys_mod);
  }

  PyObject *mod = PyImport_ImportModule("systems.register");
  if (!mod) { PyErr_Print(); PyGILState_Release(gstate); return (PluginSystems){0}; }

  PyObject *fn = PyObject_GetAttrString(mod, "register");
  Py_DECREF(mod);
  if (!fn) { PyErr_Print(); PyGILState_Release(gstate); return (PluginSystems){0}; }

  PyObject *registry_arg = PyLong_FromVoidPtr(registry);
  PyObject *result = PyObject_CallOneArg(fn, registry_arg);
  Py_DECREF(registry_arg);
  Py_DECREF(fn);
  if (!result) { PyErr_Print(); PyGILState_Release(gstate); return (PluginSystems){0}; }

  if (!PyList_Check(result)) {
    fprintf(stderr, "systems.register() must return a list\n");
    Py_DECREF(result);
    PyGILState_Release(gstate);
    return (PluginSystems){0};
  }

  Py_ssize_t n = PyList_Size(result);
  SystemDescriptor *descs = malloc((size_t)n * sizeof(SystemDescriptor));
  if (!descs) {
    Py_DECREF(result);
    PyGILState_Release(gstate);
    return (PluginSystems){0};
  }

  for (Py_ssize_t i = 0; i < n; i++) {
    PyObject *item = PyList_GetItem(result, i); // borrowed
    Py_buffer view;
    if (PyObject_GetBuffer(item, &view, PyBUF_SIMPLE) < 0) {
      PyErr_Print();
      free(descs);
      Py_DECREF(result);
      PyGILState_Release(gstate);
      return (PluginSystems){0};
    }
    memcpy(&descs[i], view.buf, sizeof(SystemDescriptor));
    PyBuffer_Release(&view);
  }

  Py_DECREF(result);
  PyGILState_Release(gstate);

  return (PluginSystems){ .descriptors = descs, .count = (size_t)n };
}
