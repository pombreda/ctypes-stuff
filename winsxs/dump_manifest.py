#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""This script dumps the manifest of the executable specified.
"""
from __future__ import division, with_statement, absolute_import, print_function

import ctypes
import sys
import wapi
import xml.dom.minidom

def dump_manifest(exe_path):
    is_dll = not exe_path.lower().endswith(".exe")
    handle = wapi.LoadLibraryA(exe_path.encode("ascii"))
    resource_name = b"#2" if is_dll else b"#1"
    hr = wapi.FindResourceA(handle, resource_name, wapi.LPCSTR(wapi.RT_MANIFEST))
    if not hr:
        print("No manifest resource %s found in %r" % (resource_name, exe_path))
        return
    hglobal = wapi.LoadResource(handle, hr)
    size = wapi.SizeofResource(handle, hr)

    ptr = wapi.LockResource(hglobal)
    lpstr = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_char))
    m = lpstr[:size]

    # Pretty print output
    # See http://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
    text = xml.dom.minidom.parseString(m)
    m = text.toprettyxml(indent="  ")
    for line in m.splitlines():
        if line.strip():
            print(line)

if __name__ == "__main__":
    dump_manifest(sys.argv[1])
