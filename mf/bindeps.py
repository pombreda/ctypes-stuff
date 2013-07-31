#!/usr/bin/python2.7-32
# -*- coding: utf-8 -*-
from __future__ import division, with_statement, absolute_import, print_function

import os
import _wapi
import sys

_buf = _wapi.create_unicode_buffer(256)

_wapi.GetWindowsDirectoryW(_buf, len(_buf))
windir = _buf.value.lower()

_wapi.GetSystemDirectoryW(_buf, len(_buf))
sysdir = _buf.value.lower()

_wapi.GetModuleFileNameW(sys.dllhandle, _buf, len(_buf))
pydll = _buf.value.lower()

def search_path(imagename, path,
                _buf=_wapi.create_unicode_buffer(256)):
    """Find an image (exe or dll) on the PATH."""
    # SxS files (like msvcr90.dll or msvcr100.dll) are only found in
    # the SxS directory when the PATH is NULL.
    pfile = _wapi.c_wchar_p()
    if path is not None and _wapi.SearchPathW(None,
                                              imagename,
                                              None,
                                              len(_buf),
                                              _buf,
                                              pfile):
        return _buf.value

    if _wapi.SearchPathW(path,
                         imagename,
                         None,
                         len(_buf),
                         _buf,
                         pfile):
        return _buf.value
    return None

def depends(imagename):
    """Call BindImageEx and collect all dlls that are bound.
    """
    path = ";".join([os.path.dirname(imagename),
                     os.path.dirname(sys.executable),
                     os.environ["PATH"]])
    result = set()

    @_wapi.PIMAGEHLP_STATUS_ROUTINE
    def status_routine(reason, imagename, dllname, va, parameter):
        if reason == _wapi.BindImportModule: # 5
            dllname = search_path(dllname.decode("mbcs"), path).lower()
            result.add(dllname)
            # imagename binds to dllname
        return True

    _wapi.BindImageEx(_wapi.BIND_ALL_IMAGES
                       | _wapi.BIND_CACHE_IMPORT_DLLS
                       | _wapi.BIND_NO_UPDATE,
                       imagename.encode("mbcs"),
                       path.encode("mbcs"),
                       None,
                       status_routine)
    return result

def is_system_dll(imagename):
    """is_system_dll must be called with a full pathname.

    For any dll in the Windows or System directory or any subdirectory
    of those, except when the dll binds to or is the current python
    dll.

    For any other dll it returns False.
    """
    fnm = imagename.lower()
    if fnm == pydll:
        return False
    deps = depends(imagename)
    if pydll in deps:
        return False
    return fnm.startswith(windir + os.sep) or fnm.startswith(sysdir + os.sep)

def collect_deps(dlls):
    """Return all dlls that are required by the input dlls.
    The input dlls are not included in the result
    """
    result = set()
    current = set(dlls)

    while current:
        dll = current.pop()
        res = {x for x in depends(dll)
               if not is_system_dll(x)}
        current |= res
        result |= res

    return result

################################################################
if __name__ == "__main__":
    from pprint import pprint

    import win32api
    from wx import _activex, _richtext
    print("start")
    res = collect_deps([win32api.__file__,
                        _activex.__file__,
                        _richtext.__file__])
    
    pprint(res)
