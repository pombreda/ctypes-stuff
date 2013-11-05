/*
  For the _memimporter compiled into py2exe exe-stubs we need "Python-dynload.h".
  For the standalone .pyd we need <Python.h>
*/

#ifdef STANDALONE
#  include <Python.h>
#  include "Python-version.h"
#else
#  include "Python-dynload.h"
#  include <stdio.h>
#endif
#include <windows.h>

static char module_doc[] =
"Importer which can load extension modules from memory";

#include "MyLoadLibrary.h"
#include "actctx.h"

static PyObject *
import_module(PyObject *self, PyObject *args)
{
	char *initfuncname;
	char *modname;
	char *pathname;
	HMODULE hmem;
	FARPROC do_init;

	char *oldcontext;
	ULONG_PTR cookie = 0;
	PyObject *findproc;
	PyObject* (*p)(void);
	PyObject *m = NULL;
	struct PyModuleDef *def;
	char *namestr/*, *lastdot, *shortname, *packagecontext*/;

	/* code, initfuncname, fqmodulename, path */
	if (!PyArg_ParseTuple(args, "sssO:import_module",
			      &modname, &pathname,
			      &initfuncname,
			      &findproc))
		return NULL;
    
	cookie = _My_ActivateActCtx();//try some windows manifest magic...
	hmem = MyLoadLibrary(pathname, NULL, findproc);
	_My_DeactivateActCtx(cookie);

	if (!hmem) {
	        char *msg;
		FormatMessageA(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
			       NULL,
			       GetLastError(),
			       MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
			       (void *)&msg,
			       0,
			       NULL);
		msg[strlen(msg)-2] = '\0';
		PyErr_Format(PyExc_ImportError,
			     "MemoryLoadLibrary failed loading %s: %s (%d)",
			     pathname, msg, GetLastError());
		LocalFree(msg);
		/* PyErr_Format(PyExc_ImportError, */
		/* 	     "MemoryLoadLibrary failed loading %s (Error %d loading %s)", */
		/* 	     pathname, GetLastError(), LastErrorString); */
		/* PyErr_Format(PyExc_ImportError, */
		/* 	     "MemoryLoadLibrary failed loading %s", pathname); */
		return NULL;
	}
	do_init = MyGetProcAddress(hmem, initfuncname);
	if (!do_init) {
		MyFreeLibrary(hmem);
		PyErr_Format(PyExc_ImportError,
			     "Could not find function %s", initfuncname);
		return NULL;
	}

/* c:/users/thomas/devel/code/cpython-3.4/Python/importdl.c 73 */

        oldcontext = _Py_PackageContext;
	_Py_PackageContext = modname;
#if 0
	do_init();
#else
	p = (PyObject*(*)(void))do_init;
	m = (*p)();
#endif
	_Py_PackageContext = oldcontext;

	if (PyErr_Occurred())
		return NULL;
#if 1
	/* Remember pointer to module init function. */
	def = PyModule_GetDef(m);
	if (def == NULL) {
		PyErr_Format(PyExc_SystemError,
			     "initialization of %s did not return an extension "
			     "module", modname);
		return NULL;
	}
	def->m_base.m_init = p;

#if 0
	if (_PyImport_FixupExtensionObject(m,
					   PyUnicode_FromString(modname),
					   PyUnicode_FromString(pathname)) < 0)
		return NULL;
#else
	{
		PyObject *name = PyUnicode_FromString(modname);
		PyObject *path = PyUnicode_FromString(pathname);
		int res = _PyImport_FixupExtensionObject(m, name, path);
		Py_XDECREF(name);
		Py_XDECREF(path);
		if (res < 0)
			return NULL;
	}
#endif

#endif
	/* Retrieve from sys.modules */
	return PyImport_ImportModule(modname);
}

static PyObject *
get_verbose_flag(PyObject *self, PyObject *args)
{
	return PyLong_FromLong(Py_VerboseFlag);
}

static PyMethodDef methods[] = {
	{ "import_module", import_module, METH_VARARGS,
	  "import_module(modname, pathname, initfuncname, finder) -> module" },
	{ "get_verbose_flag", get_verbose_flag, METH_NOARGS,
	  "Return the Py_Verbose flag" },
	{ NULL, NULL },		/* Sentinel */
};

#if PY_MAJOR_VERSION >= 3

static struct PyModuleDef moduledef = {
	PyModuleDef_HEAD_INIT,
	"_memimporter", /* m_name */
	module_doc, /* m_doc */
	-1, /* m_size */
	methods, /* m_methods */
	NULL, /* m_reload */
	NULL, /* m_traverse */
	NULL, /* m_clear */
	NULL, /* m_free */
};


PyMODINIT_FUNC PyInit__memimporter(void)
{
	return PyModule_Create(&moduledef);
}

#else

DL_EXPORT(void)
init_memimporter(void)
{
	Py_InitModule3("_memimporter", methods, module_doc);
}

#endif
