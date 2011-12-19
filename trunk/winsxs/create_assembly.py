# -*- coding: latin-1 -*-
"""Create a private sxs assembly containing a Python2.6 interpreter
"""
from __future__ import division, with_statement, absolute_import
import os
import shutil
import wapi

manifest = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
    <noInheritable/>
    <assemblyIdentity
        type="win32"
        name="python26.manifest"
        version="2.6.6.0"
        processorArchitecture="x86"
    />
    <file name="python26.dll" />
    <file name="bz2.pyd" />
    <file name="pyexpat.pyd" />
    <file name="select.pyd" />
    <file name="unicodedata.pyd" />
    <file name="winsound.pyd" />
    <file name="_bsddb.pyd" />
    <file name="_ctypes.pyd" />
    <file name="_ctypes_test.pyd" />
    <file name="_elementtree.pyd" />
    <file name="_hashlib.pyd" />
    <file name="_msi.pyd" />
    <file name="_multiprocessing.pyd" />
    <file name="_socket.pyd" />
    <file name="_sqlite3.pyd" />
    <file name="_ssl.pyd" />
    <file name="_testcapi.pyd" />
    <file name="sqlite3.dll" />
    <file name="tcl85.dll" />
    <file name="tclpip85.dll" />
    <file name="tk85.dll" />
    <dependency>
      <dependentAssembly>
        <assemblyIdentity type="win32" name="Microsoft.VC90.CRT" version="9.0.21022.8" processorArchitecture="x86" publicKeyToken="1fc8b3b9a1e18e3b"></assemblyIdentity>
      </dependentAssembly>
    </dependency>
</assembly>
"""

if __name__ == "__main__":
    if os.path.exists("python26.private"):
        print "Removing old python26.private directory..."
        shutil.rmtree("python26.private")

    print "Copying Python26 installation into python26.private..."
    shutil.copytree("c:\\python26\\DLLs", "python26.private")

    print "Copying Python26.dll..."
    shutil.copyfile("c:\\windows\\system32\\python26.dll", "python26.private\\python26.dll")

    # Remove the RT_MANIFEST resource from the private copy of python26.dll
    print "Replacing RT_MANIFEST in Python26.dll..."
    h = wapi.BeginUpdateResource("python26.private\\python26.dll", False)
    wapi.UpdateResource(h,
                        wapi.MAKEINTRESOURCE(wapi.RT_MANIFEST),
                        wapi.MAKEINTRESOURCE(2),
                        0x0409,
                        manifest,
                        len(manifest))
    wapi.EndUpdateResource(h, False)
