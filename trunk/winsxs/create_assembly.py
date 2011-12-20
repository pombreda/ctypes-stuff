# -*- coding: latin-1 -*-
"""Create a private sxs assembly containing a Python interpreter
"""
from __future__ import division, with_statement, absolute_import
import os
import shutil
import wapi
import xml.etree.ElementTree as ET


def GetModuleFileName(hmod):
    buf = wapi.create_unicode_buffer(256)
    wapi.GetModuleFileNameW(hmod, buf, 256)
    return buf.value

if __name__ == "__main__":
    import sys
    dllpath = GetModuleFileName(sys.dllhandle)

    assembly = "python%d%d.private" % sys.version_info[:2]

    if os.path.exists(assembly):
        print "Removing old %s directory..." % assembly
        shutil.rmtree(assembly)

    print "Copying Python installation into %s..." % assembly
    import _socket; extpath = os.path.dirname(_socket.__file__)
    shutil.copytree(extpath, assembly)

    print "Copying", os.path.basename(dllpath)
    shutil.copyfile(dllpath, os.path.join(assembly, os.path.basename(dllpath)))
    files = os.listdir(assembly)

    # Retrieve the manifest resource (FT_MANIFEST, id=2)
    hr = wapi.FindResourceA(sys.dllhandle, "#2", wapi.LPCSTR(wapi.RT_MANIFEST))
    hglobal = wapi.LoadResource(sys.dllhandle, hr)
    size = wapi.SizeofResource(sys.dllhandle, hr)
    ptr = wapi.LockResource(hglobal)
    import ctypes
    lpstr = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_char))
    m = lpstr[:size]

    e = ET.fromstring(m)
    for name in files:
        e.insert(0, ET.Element("ns0:file", name=name))
    manifest64 = ET.tostring(e)

    # Retrieve the file version number
    verinfosize = wapi.GetFileVersionInfoSizeA(dllpath, wapi.DWORD())
    buf = wapi.create_string_buffer(verinfosize)
    wapi.GetFileVersionInfoA(dllpath, 0, verinfosize, buf)

    pfi = wapi.POINTER(wapi.VS_FIXEDFILEINFO)()

    wapi.VerQueryValueA(buf, "\\", pfi, wapi.c_uint())
    fi = pfi[0]
    ver = divmod(fi.dwFileVersionMS, 0x10000) + divmod(fi.dwFileVersionLS, 0x10000)
    print "Version %d.%d.%d.%d" % ver

    # Remove the RT_MANIFEST resource from the private copy of pythonXY.dll
    print "Replacing RT_MANIFEST in %s..." % os.path.basename(dllpath)
    h = wapi.BeginUpdateResource(os.path.join(assembly, os.path.basename(dllpath)), False)
    wapi.UpdateResource(h,
                        wapi.MAKEINTRESOURCE(wapi.RT_MANIFEST),
                        wapi.MAKEINTRESOURCE(2),
                        0x0409,
                        manifest64,
                        len(manifest64))
    wapi.EndUpdateResource(h, False)

    print
    print manifest64
