#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""resources for py3exe
"""

import _wapi

def add_resources(filename):
    hrsrc = _wapi.BeginUpdateResourceW(filename, False)
    print("Adding Resources")
    ## _wapi.UpdateResourceW(hrsrc,
    ##                       "PYTHONSCRIPT", # lpType
    ##                       _wapi.LPCWSTR(1), # lpName
    ##                       0, # wLanguage
    ##                       "foo", # lpData
    ##                       6)# cbData
    ## _wapi.UpdateResourceA(hrsrc,
    ##                       "PYTHONSCRIPT".encode("mbcs"), # lpType
    ##                       _wapi.LPCSTR(2), # lpName
    ##                       0, # wLanguage
    ##                       "foo".encode("mbcs"), # lpData
    ##                       3)# cbData
    with open("c:\\windows\\system32\\python33.dll", "rb") as ifi:
        pydll_bytes = ifi.read()
    _wapi.UpdateResourceA(hrsrc,
                          b"PYTHON33.DLL",
                          _wapi.LPCSTR(1),
                          0,
                          pydll_bytes,
                          len(pydll_bytes));
    _wapi.EndUpdateResourceW(hrsrc, False)
