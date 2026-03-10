#include <Python.h>

__attribute__((constructor))
static void init(void) {
    Py_Initialize();
}

__attribute__((destructor))
static void fini(void) {
    Py_Finalize();
}

void EXPORTED_FUNC_NAME(void* world_ptr, void* context_ptr) {
    PyGILState_STATE gstate = PyGILState_Ensure();
    PyObject *mod = PyImport_ImportModule(MODULE_NAME);
    if (!mod) { PyErr_Print(); PyGILState_Release(gstate); return; }
    PyObject *func = PyObject_GetAttrString(mod, FUNC_NAME);
    Py_DECREF(mod);
    if (!func) { PyErr_Print(); PyGILState_Release(gstate); return; }
    PyObject *a0 = PyLong_FromVoidPtr(world_ptr);
    PyObject *a1 = PyLong_FromVoidPtr(context_ptr);
    PyObject *args = PyTuple_Pack(2, a0, a1);
    Py_DECREF(a0); Py_DECREF(a1);
    PyObject *res = PyObject_CallObject(func, args);
    Py_DECREF(args); Py_DECREF(func);
    if (!res) PyErr_Print(); else Py_DECREF(res);
    PyGILState_Release(gstate);
}
