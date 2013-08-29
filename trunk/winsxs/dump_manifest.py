#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""This script dumps the manifest of the executable specified.
"""
from __future__ import division, with_statement, absolute_import, print_function

import ctypes
import sys
import winapi
import xml.dom.minidom

def _dump_manifest(exe_path, resource_name):
    print()
    handle = winapi.LoadLibraryEx(exe_path.encode("ascii"),
                                  0,
                                  winapi.LOAD_LIBRARY_AS_DATAFILE)
    try:
        hr = winapi.FindResourceA(handle, resource_name, winapi.LPCSTR(winapi.RT_MANIFEST))
        hglobal = winapi.LoadResource(handle, hr)
        size = winapi.SizeofResource(handle, hr)

        ptr = winapi.LockResource(hglobal)
    except Exception as details:
        print("No manifest resource %s found in %r:\n  %s" % (resource_name, exe_path, details))
        return

    lpstr = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_char))
    m = lpstr[:size]

    text = "Manifest %s in '%s'" % (resource_name, exe_path)
    print(text)
    print("=" * len(text))
    # Pretty print output
    # See http://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
    text = xml.dom.minidom.parseString(m)
    m = text.toprettyxml(indent="  ")
    for line in m.splitlines():
        if line.strip():
            print(line)

def dump_manifest(exe_path):
    _dump_manifest(exe_path, b"#1")
    _dump_manifest(exe_path, b"#2")
    

if __name__ == "__main__":
    dump_manifest(sys.argv[1])
