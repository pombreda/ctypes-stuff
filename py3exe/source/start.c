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

#include "MyLoadLibrary.h"

extern HMODULE hPYDLL;


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

PyMODINIT_FUNC PyInit__memimporter(void);
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
	pScript = p_script_info->zippath + strlen(p_script_info->zippath) + 1;

	// get full pathname of the 'library.zip' file
	if(p_script_info->zippath[0]) {
		_snwprintf(libfilename, sizeof(libfilename),
			   L"%s\\%S", dirname, p_script_info->zippath);
	} else {
		GetModuleFileNameW(hmod, libfilename, sizeof(libfilename));
	}
//	printf("LIBFILENAME '%S'\n", libfilename);
	
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
//	printf("m %p\n", m);
	if (m) d = PyModule_GetDict(m);
//	printf("d %p\n", d);
	if (d) seq = PyMarshal_ReadObjectFromString(pScript, numScriptBytes);
//	printf("seq %p\n", seq);
	if (seq) {
		Py_ssize_t i, max = PySequence_Length(seq);
//		printf("len(seq) %d\n", max);
		for (i=0; i<max; i++) {
			PyObject *sub = PySequence_GetItem(seq, i);
//			printf("seq[%d] %p\n", i, seq);
			if (sub /*&& PyCode_Check(sub) */) {
				PyObject *discard = PyEval_EvalCode(sub, d, d);
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

void set_vars(void)
{
	HMODULE py = MyGetModuleHandle(PYTHONDLL);
	int *pflag = (int *)MyGetProcAddress(py, "Py_NoSiteFlag");
	printf("GetProcAddress(%p, 'Py_NoSiteFlag') -> %p\n", py, pflag);
	*pflag = 1;

	pflag = (int *)MyGetProcAddress(py, "Py_OptimizeFlag");
	printf("GetProcAddress(%p, 'Py_OptimizeFlag') -> %p\n", py, pflag);
	if (pflag)
		*pflag = p_script_info->optimize;
}

/*****************************************************************/

int load_pythondll(void)
{
	HANDLE hrsrc;
	HMODULE hmod = LoadLibraryExW(libfilename, NULL, LOAD_LIBRARY_AS_DATAFILE);
	hPYDLL = NULL;
	
	wprintf(L"libfilename %s, hmod %p\n", libfilename, hmod);

	// Try to locate pythonxy.dll as resource in the exe
	hrsrc = FindResource(hmod, MAKEINTRESOURCE(1), PYTHONDLL);
	printf("FindResource(%p) %s %p\n", hmod, PYTHONDLL, hrsrc);
	if (hrsrc) {
		HGLOBAL hgbl;
		DWORD size;
		char *ptr;
		hgbl = LoadResource(hmod, hrsrc);
		size = SizeofResource(hmod, hrsrc);
		ptr = LockResource(hgbl);
		hPYDLL = MyLoadLibrary(PYTHONDLL, ptr, NULL);
	} else
		hPYDLL = LoadLibrary(PYTHONDLL);
	FreeLibrary(hmod);
	printf("load_pythondll: %p\n", hPYDLL);
	return hPYDLL ? 0 : -1;
}

int wmain (int argc, wchar_t **argv)
{
	int rc = 0;
	wchar_t *path = NULL;

/*
	MessageBox(NULL, "Attach Debugger", "", MB_OK);
	DebugBreak();
*/

/*	Py_NoSiteFlag = 1; /* Suppress 'import site' */
/*	Py_InspectFlag = 1; /* Needed to determine whether to exit at SystemExit */

	calc_dirname(NULL);
	wprintf(L"modulename %s\n", modulename);
	wprintf(L"dirname %s\n", dirname);

	if (!locate_script(GetModuleHandle(NULL))) {
		printf("FATAL ERROR locating script\n");
		return -1;
	}

	rc = load_pythondll();
	if (rc < 0) {
		printf("FATAL Error: could not load python library\n");
		return -1;
	}


//	Py_IsInitialized();

	set_vars();

	// provide builtin modules:
	PyImport_AppendInittab("_memimporter", PyInit__memimporter);

	Py_SetProgramName(modulename);
	path = Py_GetPath();
	Py_SetPath(libfilename);
	Py_Initialize();
	// We don't care for the additional refcount here...
	PySys_SetObject("frozen", PyUnicode_FromString("exe"));
	PySys_SetArgvEx(argc, argv, 0);

	rc = run_script();

	fini();

	return rc;
}
