#include <Python.h>
#include <windows.h>

static char module_doc[] =
"Importer which can load extension modules from memory";

#include "MyLoadLibrary.h"
#include "actctx.h"

#if (PY_VERSION_HEX >= 0x03030000)

/* Magic for extension modules (built-in as well as dynamically
   loaded).  To prevent initializing an extension module more than
   once, we keep a static dictionary 'extensions' keyed by the tuple
   (module name, module name)  (for built-in modules) or by
   (filename, module name) (for dynamically loaded modules), containing these
   modules.  A copy of the module's dictionary is stored by calling
   _PyImport_FixupExtensionObject() immediately after the module initialization
   function succeeds.  A copy can be retrieved from there by calling
   _PyImport_FindExtensionObject().

   Modules which do support multiple initialization set their m_size
   field to a non-negative number (indicating the size of the
   module-specific state). They are still recorded in the extensions
   dictionary, to avoid loading shared libraries twice.
*/


/* c:/users/thomas/devel/code/cpython-3.4/Python/importdl.c 73 */

int do_import(FARPROC init_func, char *modname)
{
	int res = -1;
	PyObject* (*p)(void);
	PyObject *m = NULL;
	struct PyModuleDef *def;
//	char *oldcontext;
	PyObject *name = PyUnicode_FromString(modname);

	if (name == NULL)
		return -1;

	m = _PyImport_FindExtensionObject(name, name);
	if (m != NULL) {
		Py_DECREF(name);
		return 0;
	}

	if (init_func == NULL) {
		PyObject *msg = PyUnicode_FromFormat("dynamic module does not define "
						     "init function (PyInit_%s)",
						     modname);
		if (msg == NULL)
			return -1;
		PyErr_SetImportError(msg, name, NULL);
		Py_DECREF(msg);
		Py_DECREF(name);
		return -1;
	}
/*
        oldcontext = _Py_PackageContext;
	_Py_PackageContext = modname;
*/
	p = (PyObject*(*)(void))init_func;
	m = (*p)();
/*
	_Py_PackageContext = oldcontext;
*/

	if (PyErr_Occurred()) {
		Py_DECREF(name);
		return -1;
	}

	/* Remember pointer to module init function. */
	def = PyModule_GetDef(m);
	if (def == NULL) {
		PyErr_Format(PyExc_SystemError,
			     "initialization of %s did not return an extension "
			     "module", modname);
		Py_DECREF(name);
		return -1;
	}
	def->m_base.m_init = p;

	res = _PyImport_FixupExtensionObject(m, name, name);
	Py_DECREF(name);
	return res;
}

#else
# error "Python 3.0, 3.1, and 3.2 are not supported"

#endif


static PyObject *
import_module(PyObject *self, PyObject *args)
{
	char *initfuncname;
	char *modname;
	char *pathname;
	HMODULE hmem;
	FARPROC init_func;

	ULONG_PTR cookie = 0;
	PyObject *findproc;

	//	MessageBox(NULL, "ATTACH", "NOW", MB_OK);
	//	DebugBreak();

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

	init_func = MyGetProcAddress(hmem, initfuncname);
	if (do_import(init_func, modname) < 0) {
		MyFreeLibrary(hmem);
		return NULL;
	}

	/* Retrieve from sys.modules */
	return PyImport_ImportModule(modname);
}

static PyObject *
get_verbose_flag(PyObject *self, PyObject *args)
{
//	return PyLong_FromLong(Py_VerboseFlag);
	return PyLong_FromLong(0);
}

static PyMethodDef methods[] = {
	{ "import_module", import_module, METH_VARARGS,
	  "import_module(modname, pathname, initfuncname, finder) -> module" },
	{ "get_verbose_flag", get_verbose_flag, METH_NOARGS,
	  "Return the Py_Verbose flag" },
	{ NULL, NULL },		/* Sentinel */
};

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
