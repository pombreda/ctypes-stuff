# -*- coding: latin-1 -*-
"""Create a private sxs assembly containing a Python interpreter
"""
from __future__ import division, with_statement, absolute_import, print_function

import ctypes
import os
import shutil
import sys
import wapi
import xml.etree.ElementTree as ET


def GetModuleFileName(hmod):
    buf = wapi.create_unicode_buffer(256)
    wapi.GetModuleFileNameW(hmod, buf, 256)
    return buf.value

if __name__ == "__main__":
    dllpath = GetModuleFileName(sys.dllhandle)

    assembly = u"python%d%d.private" % sys.version_info[:2]

    if os.path.exists(assembly):
        print("Removing old %s directory..." % assembly)
        shutil.rmtree(assembly)

    print("Copying Python installation into %s..." % assembly)
    import _socket; extpath = os.path.dirname(_socket.__file__)
    shutil.copytree(extpath, assembly)

    if sys.version_info >= (3, 0):
        # For Python 3, we must also copy these modules:
        # codecs, io, abc, _weakrefset
        # and these packages:
        # encodings
        # otherwise it won't initialize
        for name in ("io", "abc", "codecs", "_weakrefset"):
            __import__(name)
            mod = sys.modules[name]
            src = mod.__file__
            dst = os.path.join(assembly, os.path.basename(src))
            shutil.copyfile(src, dst)
        import encodings
        shutil.copytree(os.path.dirname(encodings.__file__), os.path.join(assembly, "encodings"))

    print("Copying %s" % os.path.basename(dllpath))
    shutil.copyfile(dllpath, os.path.join(assembly, os.path.basename(dllpath)))
    files = os.listdir(assembly)

    # Retrieve the manifest resource (RT_MANIFEST, id=2)
    hr = wapi.FindResourceA(sys.dllhandle, b"#2", wapi.LPCSTR(wapi.RT_MANIFEST))
    hglobal = wapi.LoadResource(sys.dllhandle, hr)
    size = wapi.SizeofResource(sys.dllhandle, hr)
    ptr = wapi.LockResource(hglobal)
    lpstr = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_char))
    m = lpstr[:size]

    e = ET.fromstring(m)
    for name in files:
        if name.lower().endswith((".dll", ".pyd")):
            e.insert(0, ET.Element("ns0:file", name=name))
    manifest64 = ET.tostring(e)

    # Retrieve the file version number
    verinfosize = wapi.GetFileVersionInfoSizeA(dllpath.encode("ascii"), wapi.DWORD())
    buf = wapi.create_string_buffer(verinfosize)
    wapi.GetFileVersionInfoA(dllpath.encode("ascii"), 0, verinfosize, buf)

    pfi = wapi.POINTER(wapi.VS_FIXEDFILEINFO)()

##    wapi.VerQueryValueA(buf, b"\\", pfi, wapi.c_uint())
##    fi = pfi[0]
##    ver = divmod(fi.dwFileVersionMS, 0x10000) + divmod(fi.dwFileVersionLS, 0x10000)
##    print("Version %d.%d.%d.%d" % ver)

    # Replace the RT_MANIFEST resource in the private copy of pythonXY.dll
    print("Replacing RT_MANIFEST in %s..." % os.path.basename(dllpath))
    h = wapi.BeginUpdateResource(os.path.join(assembly, os.path.basename(dllpath)), False)
    wapi.UpdateResource(h,
                        wapi.MAKEINTRESOURCE(wapi.RT_MANIFEST),
                        wapi.MAKEINTRESOURCE(2),
                        0x0409,
                        manifest64,
                        len(manifest64))
    wapi.EndUpdateResource(h, False)

    print()
    print(manifest64.decode("ascii"))

    ## manifest_file = os.path.join(assembly, os.path.basename(assembly) + ".manifest")
    ## with open(manifest_file, "wb") as ofi:
    ##     ofi.write(manifest64)
