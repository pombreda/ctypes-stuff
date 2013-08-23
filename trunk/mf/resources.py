#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""resources for py3exe
"""
import os
import sys
import _wapi

# something like this is what we want
## import contextlib

## @contextlib.contextmanager
## def UpdateResources(filename, delete_existing=False):
##     hrscr = _wapi.BeginUpdateResourceW(filename, delete_existing)
##     yield _wapi.UpdateResourceA
##     _wapi.EndUpdateResourceW(hrsrc, False)
    

## def add_resources(filename, script_info):
##     with UpdateResources(filename) as add:
##         add(b"PYTHON33.DLL", 1, pydll_bytes)
##         add(b"PYTHONSCRIPT", 1, script_info)


def add_resources(filename, script_info):

    pydll = "python%d%d.dll" % sys.version_info[:2]

    hrsrc = _wapi.BeginUpdateResourceW(filename, False)

    with open("c:\\windows\\system32\\%s" % pydll, "rb") as ifi:
        pydll_bytes = ifi.read()

    print("Add Resource %s to %s" % (os.path.basename(pydll), filename))

    _wapi.UpdateResourceA(hrsrc,
                          pydll.encode("ascii"),
                          _wapi.LPCSTR(1),
                          0, # wLanguage
                          pydll_bytes,
                          len(pydll_bytes));

    _wapi.UpdateResourceA(hrsrc,
                          b"PYTHONSCRIPT",
                          _wapi.LPCSTR(1),
                          0, # wLanguage
                          script_info,
                          len(script_info))

    _wapi.EndUpdateResourceW(hrsrc, False)
