#include <Python.h>
#include <windows.h>
#include "MyLoadLibrary.h"

/*
  This module allows us to dynamically load the python DLL.

  We have to #define Py_BUILD_CORE when we cmpile our stuff,
  then the exe doesn't try to link with pythonXY.lib, and also
  the following definitions compile.

  We use MyGetProcAddress to get the functions from the dynamically
  loaded python DLL, so it will work both with the DLL loaded from the
  file system as well as loaded from memory.

  Problems:
  - We cannot use vararg functions that have no va_list counterpart.
  - What about the flags or other data exported from Python?
  - Error handling MUST be improved...
  - Should we use a python script to generate this code
    from function prototypes automatically?
*/

HMODULE hPYDLL;

#define NYI(x) MessageBox(NULL, x, "not yet implemented", MB_OK)

#define FUNC(res, name, args) \
  static res(*proc)args; \
  if (!proc) (FARPROC)proc = MyGetProcAddress(hPYDLL, #name)

////////////////////////////////////////////////////////////////

PyObject *PyErr_SetImportError(PyObject *msg, PyObject *name, PyObject *path)
{
  FUNC(PyObject *, PyErr_SetImportError, (PyObject *, PyObject *, PyObject *));
  return proc(msg, name, path);
}

int Py_FdIsInteractive(FILE *fp, const char *filename)
{
  FUNC(int, Py_FdIsInteractive, (FILE *, const char *));
  return proc(fp, filename);
}

int PyRun_InteractiveLoopFlags(FILE *fp, const char *filename, PyCompilerFlags *flags)
{
  FUNC(int, PyRun_InteractiveLoopFlags, (FILE *, const char *, PyCompilerFlags *));
  return proc(fp, filename, flags);
}

wchar_t *Py_GetPath(void)
{
  FUNC(wchar_t *, Py_GetPath, (void));
  return proc();
}

void Py_SetPath(const wchar_t *path)
{
  FUNC(void, Py_SetPath, (const wchar_t *));
  proc(path);
}

void Py_Finalize(void)
{
  FUNC(void, Py_Finalize, (void));
  proc();
}

void Py_Initialize(void)
{
  FUNC(void, Py_Initialize, (void));
  proc();
}

void PyErr_Clear(void)
{
  FUNC(void, PyErr_Clear, (void));
  proc();
}

PyObject *PyErr_Occurred(void)
{
  FUNC(PyObject *, PyErr_Occurred, (void));
  return proc();
}

void PyErr_Print(void)
{
  FUNC(void, PyErr_Print, (void));
  proc();
}

void Py_SetProgramName(wchar_t *name)
{
  FUNC(void, Py_SetProgramName, (wchar_t *));
  proc(name);
}

void PySys_SetArgvEx(int argc, wchar_t **argv, int updatepath)
{
  FUNC(void, PySys_SetArgvEx, (int, wchar_t **, int));
  proc(argc, argv, updatepath);
}

PyObject *PyImport_AddModule(const char *name)
{
  FUNC(PyObject *, PyImport_AddModule, (const char *));
  return proc(name);
}

PyObject *PyModule_GetDict(PyObject *m)
{
  FUNC(PyObject *, PyModule_GetDict, (PyObject *));
  return proc(m);
}

PyObject *PyMarshal_ReadObjectFromString(char *string, Py_ssize_t len)
{
  FUNC(PyObject *, PyMarshal_ReadObjectFromString, (char *, Py_ssize_t));
  return proc(string, len);
}

PyObject *PySequence_GetItem(PyObject *seq, Py_ssize_t i)
{
  FUNC(PyObject *, PySequence_GetItem, (PyObject *, Py_ssize_t));
  return proc(seq, i);
}

Py_ssize_t PySequence_Size(PyObject *seq)
{
  FUNC(Py_ssize_t, PySequence_Size, (PyObject *));
  return proc(seq);
}

PyObject *PyEval_EvalCode(PyObject *co, PyObject *globals, PyObject *locals)
{
  FUNC(PyObject *, PyEval_EvalCode, (PyObject *, PyObject *, PyObject *));
  return proc(co, globals, locals);
}

int PyImport_AppendInittab(const char *name, PyObject* (*initfunc)(void)) 
{
  FUNC(int, PyImport_AppendInittab, (const char *, PyObject *(*)(void)));
  return proc(name, initfunc);
}

PyObject *PyModule_Create2(PyModuleDef *module, int module_api_version)
{
  FUNC(PyObject *, PyModule_Create2, (PyModuleDef *, int));
  return proc(module, module_api_version);
}

PyObject *PyLong_FromLong(long n)
{
  FUNC(PyObject *, PyLong_FromLong, (long));
  return proc(n);
}

int PyArg_ParseTuple(PyObject *args, const char *format, ...)
{
  int result;
  va_list marker;
  FUNC(int, PyArg_VaParse, (PyObject *, const char *, va_list));
  va_start(marker, format);
  result = proc(args, format, marker);
  va_end(marker);
  return -1;
}

PyObject *PyObject_CallObject(PyObject *callable, PyObject *args)
{
  FUNC(PyObject *, PyObject_CallObject, (PyObject *, PyObject *));
  return proc(callable, args);
}

PyObject *PyTuple_New(Py_ssize_t len)
{
  FUNC(PyObject *, PyTuple_New, (Py_ssize_t));
  return proc(len);
}

int PyTuple_SetItem(PyObject *p, Py_ssize_t pos, PyObject *o)
{
  FUNC(int, PyTuple_SetItem, (PyObject *, Py_ssize_t, PyObject *));
  return proc(p, pos, o);
}

PyObject *PyUnicode_FromString(const char *u)
{
  FUNC(PyObject *, PyUnicode_FromString, (const char *));
  return proc(u);
}

#ifdef Py_LIMITED_API
void _Py_Dealloc(PyObject *ob)
{
  FUNC(void, _Py_Dealloc, (PyObject *));
  proc(ob);
}
#endif

char *PyBytes_AsString(PyObject *string)
{
  FUNC(char *, PyBytes_AsString, (PyObject *));
  return proc(string);
}

PyModuleDef *PyModule_GetDef(PyObject *module)
{
  FUNC(PyModuleDef *, PyModule_GetDef, (PyObject *));
  return proc(module);
}

PyObject *PyImport_ImportModule(const char *name)
{
  FUNC(PyObject *, PyImport_ImportModule, (const char *));
  return proc(name);
}

/* The following two functions are NOT part of the stable ABI !!! */


PyObject *_PyImport_FindExtensionObject(PyObject *a, PyObject *b)
{
  FUNC(PyObject *, _PyImport_FindExtensionObject, (PyObject *, PyObject *));
  return proc(a, b);
}

int _PyImport_FixupExtensionObject(PyObject *m, PyObject *a, PyObject *b)
{
  FUNC(int, _PyImport_FixupExtensionObject, (PyObject *, PyObject *, PyObject *));
  return proc(m, a, b);
}

// c:\Python33-64\include\Python.h

int PySys_SetObject(const char *name, PyObject *v)
{ // Why do 
  FUNC(int, PySys_SetObject, (const char *, PyObject *));
  return proc(name, v);
}

////////////////////////////////////////////////////////////////

PyObject *PyErr_Format(PyObject *exception, const char *format, ...)
{
  NYI("PyErrFormat");
  DebugBreak();
  return NULL;
}

void PyErr_SetObject(PyObject *type, PyObject *value)
{
  NYI("PyErr_SetObject");
  DebugBreak();
}

PyObject *PyExc_SystemError;
PyObject *PyExc_ImportError;

//Py_VerboseFlag

PyObject *PyUnicode_FromFormat(const char *format, ...)
{
  NYI("PyUnicode_FromFormat");
  DebugBreak();
  return NULL;
}
