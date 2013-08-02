#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""resources for py3exe
"""

import _wapi

def add_resources(filename, script_info):
    hrsrc = _wapi.BeginUpdateResourceW(filename, False)

    print("Adding Resources")

    ## with open("c:\\windows\\system32\\python33.dll", "rb") as ifi:
    ##     pydll_bytes = ifi.read()

    ## _wapi.UpdateResourceA(hrsrc,
    ##                       b"PYTHON33.DLL",
    ##                       _wapi.LPCSTR(1),
    ##                       0, # wLanguage
    ##                       pydll_bytes,
    ##                       len(pydll_bytes));

    _wapi.UpdateResourceA(hrsrc,
                          b"PYTHONSCRIPT",
                          _wapi.LPCSTR(1),
                          0, # wLanguage
                          script_info,
                          len(script_info))

    _wapi.EndUpdateResourceW(hrsrc, False)
