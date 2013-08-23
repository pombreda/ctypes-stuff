# -*- coding: latin-1 -*-
"""embed python into python."""
from __future__ import division, with_statement, absolute_import, print_function


import os
import sys
import ctypes

import py
from actctx import Context

dllname = "python%d%d.dll" % sys.version_info[:2]
assembly = "python%d%d.private" % sys.version_info[:2]

ctx = Context(os.path.join(assembly, dllname))

with ctx.activate():
    interp = py.Python(dllname)

    interp.Py_VerboseFlag.value = 0
    interp.Py_IgnoreEnvironmentFlag.value = 1
    interp.Py_NoSiteFlag.value = 1
    ##interp.Py_SetProgramName("python27.private")

    directory = os.path.abspath(os.path.dirname(__file__))
    interp.Py_SetPythonHome(directory)

    initial_path = interp.Py_GetPath()
    newpath = os.path.join(directory, assembly)

    # Replace the initial path in the Python dll by another one (assuming
    # the pointer returned by Py_GetPath points to writeable memory)
    interp.Py_GetPath.restype = ctypes.POINTER(py.CHAR)
    ppath = interp.Py_GetPath()
    for i, c in enumerate(newpath + "\0"):
        ppath[i] = c

    interp.Py_GetPath.restype = py.STRING
    print("2nd PATH", interp.Py_GetPath())

    interp.Py_Initialize()
    interp.PyRun_SimpleString(b"import sys; print('sys.path', sys.path)")
    interp.PyRun_SimpleString(b"import sys; print('DllHandle:', hex(sys.dllhandle))")
    interp.PyRun_SimpleString(b"import _socket; print(_socket)")

    interp.PyRun_SimpleString(b"print(__name__)")

    import sys
    print("DllHandle", hex(sys.dllhandle))
    print()
    text = """\
    Please examine the python process to see that 2 instances of
    pythonXY.dll are loaded into one process; then press Enter."""

    if py.PY3:
        input(text)
    else:
        raw_input(text)
