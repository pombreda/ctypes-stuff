/*
 *	   Copyright (c) 2000 - 2013 Thomas Heller
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */

/*
 * $Id: start.c 726 2013-06-05 18:42:13Z theller $
 *
 */

#include <windows.h>
#include <Python.h>
#include <marshal.h>
#include <compile.h>
#include <eval.h>

#if defined(MS_WINDOWS) || defined(__CYGWIN__)
#include <fcntl.h>
#endif

struct scriptinfo {
	int tag;
	int optimize;
	int unbuffered;
	int data_bytes;

	char zippath[0];
};

extern void SystemError(int error, char *msg);
int run_script(void);
void fini(void);
char *pScript;
char *pZipBaseName;
int numScriptBytes;
wchar_t modulename[_MAX_PATH + _MAX_FNAME + _MAX_EXT]; // from GetModuleName()
wchar_t dirname[_MAX_PATH]; // directory part of GetModuleName()
wchar_t libdirname[_MAX_PATH]; // library directory - probably same as above.
wchar_t libfilename[_MAX_PATH + _MAX_FNAME + _MAX_EXT]; // library filename
struct scriptinfo *p_script_info;

void SystemError(int error, char *msg)
{
	char Buffer[1024];

	if (msg)
		fprintf(stderr, msg);
	if (error) {
		LPVOID lpMsgBuf;
		FormatMessage( 
			FORMAT_MESSAGE_ALLOCATE_BUFFER | 
			FORMAT_MESSAGE_FROM_SYSTEM,
			NULL,
			error,
			MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
			(LPSTR)&lpMsgBuf,
			0,
			NULL 
			);
		strncpy(Buffer, lpMsgBuf, sizeof(Buffer));
		LocalFree(lpMsgBuf);
		fprintf(stderr, Buffer);
	}
}

/*
static int dprintf(char *fmt, ...)
{
	char Buffer[4096];
	va_list marker;
	int result;

	va_start(marker, fmt);
	result = vsprintf(Buffer, fmt, marker);
	OutputDebugString(Buffer);
	return result;
}
*/

BOOL calc_dirname(HMODULE hmod)
{
	int is_special;
	wchar_t *modulename_start;
	wchar_t *cp;
	// get module filename
	if (!GetModuleFileNameW(hmod, modulename, sizeof(modulename))) {
		SystemError(GetLastError(), "Retrieving module name");
		return FALSE;
	}
	// get directory of modulename.  Note that in some cases
	// (eg, ISAPI), GetModuleFileName may return a leading "\\?\"
	// (which is a special format you can pass to the Unicode API
	// to avoid MAX_PATH limitations).  Python currently can't understand
	// such names, and as it uses the ANSI API, neither does Windows!
	// So fix that up here.
	is_special = wcslen(modulename) > 4 &&
		wcsncmp(modulename, L"\\\\?\\", 4)==0;
	modulename_start = is_special ? modulename + 4 : modulename;
	wcscpy(dirname, modulename_start);
	cp = wcsrchr(dirname, L'\\');
	*cp = L'\0';
	return TRUE;
}


BOOL locate_script(HMODULE hmod)
{
	HRSRC hrsrc = FindResource(hmod, MAKEINTRESOURCE(1), "PYTHONSCRIPT");
	HGLOBAL hgbl;

	// load the script resource
	if (!hrsrc) {
		SystemError(GetLastError(), "Could not locate script resource:");
		return FALSE;
	}
	hgbl = LoadResource(hmod, hrsrc);
	if (!hgbl) {
		SystemError(GetLastError(), "Could not load script resource:");
		return FALSE;
	}
	p_script_info = (struct scriptinfo *)pScript = LockResource(hgbl);
	if (!pScript)  {
		SystemError(GetLastError(), "Could not lock script resource:");
		return FALSE;
	}
	// validate script resource
	numScriptBytes = p_script_info->data_bytes;
	pScript += sizeof(struct scriptinfo);
	if (p_script_info->tag != 0x78563412) {
		SystemError (0, "Bug: Invalid script resource");
		return FALSE;
	}
	// let pScript point to the start of the python script resource
	pScript += strlen(p_script_info->zippath) + 1;

	// get full pathname of the 'library.zip' file
	if(p_script_info->zippath[0]) {
		_snwprintf(libfilename, sizeof(libfilename),
			   L"%s\\%S", dirname, p_script_info->zippath);
	} else {
		GetModuleFileNameW(hmod, libfilename, sizeof(libfilename));
	}
	printf("LIBFILENAME '%S'\n", libfilename);
	return TRUE; // success
}

void fini(void)
{
	/* The standard Python does also allow this: Set PYTHONINSPECT
	   in the script and examine it afterwards
	*/
	if (getenv("PYTHONINSPECT") && Py_FdIsInteractive(stdin, "<stdin>"))
		PyRun_InteractiveLoop(stdin, "<stdin>");
	/* Clean up */
	Py_Finalize();
}

int run_script(void)
{
	int rc = 0;

	/* load the code objects to execute */
	PyObject *m=NULL, *d=NULL, *seq=NULL;
	/* We execute then in the context of '__main__' */
	m = PyImport_AddModule("__main__");
	if (m) d = PyModule_GetDict(m);
	if (d) seq = PyMarshal_ReadObjectFromString(pScript, numScriptBytes);
	if (seq) {
		Py_ssize_t i, max = PySequence_Length(seq);
		for (i=0;i<max;i++) {
			PyObject *sub = PySequence_GetItem(seq, i);
			if (sub /*&& PyCode_Check(sub) */) {
				PyObject *discard = PyEval_EvalCode((PyObject *)sub,
								    d, d);
				if (!discard) {
					PyErr_Print();
					rc = 255;
				}
				Py_XDECREF(discard);
				/* keep going even if we fail */
			}
			Py_XDECREF(sub);
		}
	}
	return rc;
}

BOOL unpack_python_dll(HMODULE hmod)
{
	HANDLE hrsrc;
	// Try to locate pythonxy.dll as resource in the exe
	hrsrc = FindResource(hmod, MAKEINTRESOURCE(1), PYTHONDLL);
	printf("FindResource %s %p\n", PYTHONDLL, hrsrc);
	if (hrsrc) {
		wchar_t pydll[260];
		HGLOBAL hgbl;
		DWORD size;
		char *ptr;
		FILE *f;
		hgbl = LoadResource(hmod, hrsrc);
		size = SizeofResource(hmod, hrsrc);
		ptr = LockResource(hgbl);
		_snwprintf(pydll, sizeof(pydll), L"%s\\%S", dirname, PYTHONDLL);
		printf("PYTHONDLL: %S\n", pydll);
		f = _wfopen(pydll, L"wb");
		fwrite(ptr, size, 1, f);
		fclose(f);
	}
	return TRUE;
}


void set_vars(void)
{
	HMODULE py = GetModuleHandle(PYTHONDLL);
	int *pflag = (int *)GetProcAddress(py, "Py_NoSiteFlag");
	printf("GetProcAddress(%p, 'Py_NoSiteFlag') -> %p\n", py, pflag);
	*pflag = 1;
}

void free_lib(wchar_t *name)
{
	HMODULE hmod = GetModuleHandleW(name);
	int res;
	do {
		res = (int)FreeLibrary(hmod);
		printf("Free %S -> %d\n", name, res);
	} while (res);
	res = _wunlink(name);
	printf("unlinked %S -> %d\n", name, res);
}

/****************************************************************
 * the _p2e builtin helper module
 */
/*
static struct DLL {
	wchar_t *dllname;
	struct DLL *next;
} *dll_pointer;

void free_dlls()
{
	struct DLL *ptr = dll_pointer;
	while(ptr) {
		printf("FOUND %S\n", ptr->dllname);
		free_lib(ptr->dllname);
		ptr = ptr->next;
	}
}

static PyObject *
_p2e_register_dll(PyObject *self, PyObject *args)
{
	wchar_t *dll;
	struct DLL *ptr;
	if (!PyArg_ParseTuple(args, "u", &dll))
		return NULL;
	printf("REGISTERED %S\n", dll);
	ptr = (struct DLL *)malloc(sizeof(struct DLL));
	ptr->dllname = _wcsdup(dll);
	ptr->next = dll_pointer;
	dll_pointer = ptr;
	return PyLong_FromLong(42);
}

static PyMethodDef _p2eMethods[] = {
	{"register_dll", _p2e_register_dll, METH_VARARGS, "register a dll for cleanup"},
	{NULL, NULL, 0, NULL},
};

static struct PyModuleDef _p2emodule = {
	PyModuleDef_HEAD_INIT,
	"_p2e",
	"py2exe runtime helper module",
	-1,
	_p2eMethods
};

PyMODINIT_FUNC
PyInit__p2e(void)
{
	return PyModule_Create(&_p2emodule);
}
*/

/*****************************************************************/

int wmain (int argc, wchar_t **argv)
{
	int rc = 0;

/*	Py_NoSiteFlag = 1; /* Suppress 'import site' */
/*	Py_InspectFlag = 1; /* Needed to determine whether to exit at SystemExit */

	calc_dirname(NULL);
//	wprintf(L"modulename %s\n", modulename);
//	wprintf(L"dirname %s\n", dirname);

//	unpack_python_dll(GetModuleHandle(NULL));

	if (!locate_script(GetModuleHandle(NULL))) {
		printf("FATAL ERROR locating script\n");
		return -1;
	}


//	Py_IsInitialized();

	set_vars();
/*
	// provide builtin modules:
	PyImport_AppendInittab("_p2e", PyInit__p2e);
*/	

	Py_SetProgramName(modulename);
	Py_SetPath(libfilename);
	Py_Initialize();
	PySys_SetArgvEx(argc, argv, 0);

//	PyRun_SimpleString("import sys; print(sys.path)");

/*
	rc = run_script();
*/
	PyRun_SimpleString("import __SCRIPT__; __SCRIPT__.main()");
//	PyRun_SimpleString("import __main__; print(dir(__main__))");

	fini();

	return rc;
}
