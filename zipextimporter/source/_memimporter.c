/*
  For the _memimporter compiled into py2exe exe-stubs we need "Python-dynload.h".
  For the standalone .pyd we need <Python.h>
*/

#include <Python.h>
#include <windows.h>

static char module_doc[] =
"Importer which can load extension modules from memory";

#include "MemoryModule.h"
#include "actctx.h"

static FARPROC _GetProcAddress(HCUSTOMMODULE module, LPCSTR name, void *userdata)
{
	FARPROC res;
	res = (FARPROC)GetProcAddress((HMODULE)module, name);
	if (res == NULL) {
		SetLastError(0);
		return MemoryGetProcAddress(module, name);
	} else
		return res;
}

static void _FreeLibrary(HCUSTOMMODULE module, void *userdata)
{
    FreeLibrary((HMODULE) module);
}

static HCUSTOMMODULE _LoadLibrary(LPCSTR filename, void *userdata)
{
	HCUSTOMMODULE result;
//	printf("LoadLibrary(%s)\n", filename);
	if (userdata) {
		PyObject *findproc = (PyObject *)userdata;
		PyObject *res = PyObject_CallFunction(findproc, "s", filename);
		if (res && PyString_AsString(res)) {
			result = MemoryLoadLibraryEx(PyString_AsString(res),
						     _LoadLibrary, _GetProcAddress, _FreeLibrary,
						     userdata);
			Py_DECREF(res);
			printf("MemoryLoadLibrary(%s) -> %p\n", filename, (void *)result);
			return (HCUSTOMMODULE)result;
		} else {
			PyErr_Clear();
		}
	}
	return (HCUSTOMMODULE)LoadLibraryA(filename);
}

static PyObject *
import_module(PyObject *self, PyObject *args)
{
	char *data;
	int size;
	char *initfuncname;
	char *modname;
	char *pathname;
	HMEMORYMODULE hmem;
	FARPROC do_init;

	char *oldcontext;
	ULONG_PTR cookie = 0;
	PyObject *findproc;
	/* code, initfuncname, fqmodulename, path */
	if (!PyArg_ParseTuple(args, "sssO:import_module",
			      &modname, &pathname,
			      &initfuncname,
			      &findproc))
		return NULL;
    
	cookie = _My_ActivateActCtx();//try some windows manifest magic...

	hmem = _LoadLibrary(pathname, findproc);

	printf("MemoryLoadLibrary(%s) -> %p\n", pathname, (void *)hmem);

	_My_DeactivateActCtx(cookie);
	if (!hmem) {
		printf("ERROR %d\n", GetLastError());
		PyErr_Format(PyExc_ImportError,
			     "MemoryLoadLibrary failed loading %s", pathname);
		return NULL;
	}
	do_init = MemoryGetProcAddress(hmem, initfuncname);
	if (!do_init) {
		MemoryFreeLibrary(hmem);
		PyErr_Format(PyExc_ImportError,
			     "Could not find function %s", initfuncname);
		return NULL;
	}

        oldcontext = _Py_PackageContext;
	_Py_PackageContext = modname;
	do_init();
	_Py_PackageContext = oldcontext;
	if (PyErr_Occurred())
		return NULL;
	/* Retrieve from sys.modules */
	return PyImport_ImportModule(modname);
}

static PyObject *
get_verbose_flag(PyObject *self, PyObject *args)
{
	return PyInt_FromLong(Py_VerboseFlag);
}

static PyMethodDef methods[] = {
	{ "import_module", import_module, METH_VARARGS,
	  "import_module(modname, pathname, initfuncname, finder) -> module" },
	{ "get_verbose_flag", get_verbose_flag, METH_NOARGS,
	  "Return the Py_Verbose flag" },
//	{ "set_find_proc", set_find_proc, METH_VARARGS },
	{ NULL, NULL },		/* Sentinel */
};

DL_EXPORT(void)
init_memimporter(void)
{
	Py_InitModule3("_memimporter", methods, module_doc);
}
