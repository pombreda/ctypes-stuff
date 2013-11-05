#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""dllfinder
"""
import _wapi
import collections
import os
import sys

################################
# XXX Move these into _wapi???
_buf = _wapi.create_unicode_buffer(260)

_wapi.GetWindowsDirectoryW(_buf, len(_buf))
windir = _buf.value.lower()

_wapi.GetSystemDirectoryW(_buf, len(_buf))
sysdir = _buf.value.lower()

_wapi.GetModuleFileNameW(sys.dllhandle, _buf, len(_buf))
pydll = _buf.value.lower()

def SearchPath(imagename, path=None):
    pfile = _wapi.c_wchar_p()
    if _wapi.SearchPathW(path,
                         imagename,
                         None,
                         len(_buf),
                         _buf,
                         pfile):
        return _buf.value
    return None

################################

class DllFinder:

    def __init__(self):
        # _loaded_dlls contains ALL dlls that are bound, this includes
        # the loaded extension modules; maps lower case basename to
        # full pathname.
        self._loaded_dlls = {}

        # _dlls contains the full pathname of the dlls that
        # are NOT considered system dlls.
        #
        # The pathname is mapped to a set of modules/dlls that require
        # this dll. This allows to find out WHY a certain dll has to
        # be included.
        self._dlls = collections.defaultdict(set)

    def import_extension(self, pyd, callers=None):
        """Add an extension module and scan it for dependencies.

        """
        todo = {pyd} # todo contains the dlls that we have to examine

        while todo:
            dll = todo.pop() # get one and check it
            if dll in self._loaded_dlls:
                continue
            for dep_dll in self.bind_image(dll):
                if dep_dll in self._loaded_dlls:
                    continue
                if not self.is_system_dll(dep_dll):
                    todo.add(dep_dll)
                    self._dlls[dep_dll].add(dll)


    def bind_image(self, imagename):
        """Call BindImageEx and collect all dlls that are bound.
        """
        path = ";".join([os.path.dirname(imagename),
                         os.path.dirname(sys.executable),
                         os.environ["PATH"]])
        result = set()

        @_wapi.PIMAGEHLP_STATUS_ROUTINE
        def status_routine(reason, imagename, dllname, va, parameter):
            if reason == _wapi.BindImportModule: # 5
                # imagename binds to dllname
                dllname = self.search_path(dllname.decode("mbcs"), path)
                result.add(dllname)
            return True

        self._loaded_dlls[os.path.basename(imagename).lower()] = imagename
        _wapi.BindImageEx(_wapi.BIND_ALL_IMAGES
                           | _wapi.BIND_CACHE_IMPORT_DLLS
                           | _wapi.BIND_NO_UPDATE,
                           imagename.encode("mbcs"),
                           path.encode("mbcs"),
                           None,
                           status_routine)
        return result


    def is_system_dll(self, imagename):
        """is_system_dll must be called with a full pathname.

        For any dll in the Windows or System directory or any subdirectory
        of those, except when the dll binds to or IS the current python
        dll.

        For any other dll it returns False.
        """
        fnm = imagename.lower()
        if fnm == pydll:
            return False
        deps = self.bind_image(imagename)
        if pydll in [x.lower() for x in deps]:
            return False
        return fnm.startswith(windir + os.sep) or fnm.startswith(sysdir + os.sep)


    def search_path(self, imagename, path):
        """Find an image (exe or dll) on the PATH."""
        if imagename.lower() in self._loaded_dlls:
            return self._loaded_dlls[imagename.lower()]
        # SxS files (like msvcr90.dll or msvcr100.dll) are only found in
        # the SxS directory when the PATH is NULL.
        if path is not None:
            found = SearchPath(imagename)
            if found is not None:
                return found
        return SearchPath(imagename, path)

    def required_dlls(self):
        """Return a set containing the pathnames of required dlls.
        System dlls are not included in the result.
        """
        return self._dlls

    def system_dlls(self):
        """Return a set containing the pathnames of system dlls.
        The required_dlls are NOT included in the result.
        """
        return set(self._loaded_dlls.values()) - set(self._dlls)

################################################################

from  mf4 import ModuleFinder
from importlib.machinery import EXTENSION_SUFFIXES

class Scanner(ModuleFinder):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.dllfinder = DllFinder()

    def _add_module(self, name, mod):
        super()._add_module(name, mod)
        if hasattr(mod, "__file__") \
               and mod.__file__.endswith(tuple(EXTENSION_SUFFIXES)):
            callers = {self.modules[n]
                       for n in self._depgraph[name]}
            self._add_pyd(mod.__file__, callers)

    def _add_pyd(self, name, callers):
        self.dllfinder.import_extension(name, callers)

    def required_dlls(self):
        return self.dllfinder.required_dlls()

    ## def report_dlls(self):
    ##     import pprint
    ##     pprint.pprint(set(self.dllfinder.required_dlls()))
    ##     pprint.pprint(set(self.dllfinder.system_dlls()))

################################################################
    
if __name__ == "__main__":
    # test script and usage example
    #
    # Should we introduce an 'offical' subclass of ModuleFinder
    # and DllFinder?

    scanner = Scanner()
    scanner.import_package("numpy")
    scanner.report_dlls()