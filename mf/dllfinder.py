#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""dllfinder
"""
import _wapi
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
    if _wapi.SearchPathW(None,
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
        # _loaded_dlls contains ALL dlls that are bound;
        # maps lower case basename to full pathname.
        self._loaded_dlls = {}
        # _dlls contains the full pathname of the dlls (and pyds) that
        # are NOT considered system dlls.
        self._dlls = set()

    def import_extension(self, pyd):
        """Add an extension module and scan it for dependencies.

        """
        self._dlls.add(pyd)

        todo = {pyd}
        while todo:
            dll = todo.pop()
            self._loaded_dlls[os.path.basename(dll).lower()] = dll
            for dep_dll in self.bind_image(dll):
                self._loaded_dlls[os.path.basename(dep_dll).lower()] = dep_dll
                if not self.is_system_dll(dep_dll):
                    todo.add(dep_dll)
                    self._dlls.add(dep_dll)


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
        return set(self._loaded_dlls.values()) - self._dlls

##    def report(self):
        

################################################################
    
if __name__ == "__main__":
    from  mf4 import ModuleFinder
    from importlib.machinery import EXTENSION_SUFFIXES

    class Scanner(ModuleFinder):

        def __init__(self, *args, **kw):
            super(Scanner, self).__init__(*args, **kw)
            self.dllfinder = DllFinder()

        def _add_module(self, name, mod):
            super(Scanner, self)._add_module(name, mod)
            if hasattr(mod, "__file__") \
                   and mod.__file__.endswith(tuple(EXTENSION_SUFFIXES)):
                self._add_pyd(mod.__file__)

        def _add_pyd(self, name):
            self.dllfinder.import_extension(name)

        def report_dlls(self):
            import pprint
            pprint.pprint(self.dllfinder.required_dlls())
            pprint.pprint(self.dllfinder.system_dlls())

    scanner = Scanner()
    scanner.import_hook("numpy")
    scanner.report_dlls()
