r"""zipextimporter - an importer which can import extension modules
from zipfiles without unpacking them to the file system.

This file and _memimporter.pyd is part of the py2exe package.

Overview
========

zipextimporter.py contains the ZipExtImporter class which allows to
load Python binary extension modules contained in a zip.archive,
without unpacking them to the file system.

Call the zipextimporter.install() function to install the import hook,
add a zip-file containing .pyd or .dll extension modules to sys.path,
and import them.

It uses the _memimporter extension which uses code from Joachim
Bauch's MemoryModule library.  This library emulates the win32 api
function LoadLibrary.

Sample usage
============

You have to prepare a zip-archive 'lib.zip' containing
your Python's _socket.pyd for this example to work.

>>> import zipextimporter
>>> zipextimporter.install()
>>> import sys
>>> sys.path.insert(0, "lib.zip")
>>> import _socket
>>> print(_socket)
<module '_socket' from 'lib.zip\_socket.pyd'>
>>> _socket.__file__
'lib.zip\\_socket.pyd'
>>> _socket.__loader__
<ZipExtensionImporter object 'lib.zip'>
>>> # Reloading also works correctly:
>>> _socket is reload(_socket)
True
>>>

"""
from __future__ import division, with_statement, absolute_import, print_function

import imp, sys
import zipimport
import _memimporter

class ZipExtensionImporter(zipimport.zipimporter):
    _suffixes = [s[0] for s in imp.get_suffixes() if s[2] == imp.C_EXTENSION]

    def find_loader(self, fullname):
        """We need to override this method for Python 3.x.
        """
        loader, portions = super().find_loader(fullname)
        if loader is None:
            for s in self._suffixes:
                if (fullname + s) in self._files:
                    return self, []
        return loader, portions

    def find_module(self, fullname, path=None):
        result = zipimport.zipimporter.find_module(self, fullname, path)
        if result:
            return result
        if fullname in ("pywintypes", "pythoncom"):
            fullname = fullname + "%d%d" % sys.version_info[:2]
            fullname = fullname.replace(".", "\\") + ".dll"
            if fullname in self._files:
                return self
        else:
            fullname = fullname.replace(".", "\\")
            for s in self._suffixes:
                if (fullname + s) in self._files:
                    return self
        return None

    def load_module(self, fullname):
        verbose = _memimporter.get_verbose_flag()
        if fullname in sys.modules:
            mod = sys.modules[fullname]
            if verbose:
                sys.stderr.write(
                    "import %s # previously loaded from zipfile %s\n"
                    % (fullname, self.archive))
            return mod
        try:
            return zipimport.zipimporter.load_module(self, fullname)
        except zipimport.ZipImportError:
            pass
        if sys.version_info >= (3, 0):
            # name of initfunction
            initname = "PyInit_" + fullname.split(".")[-1]
        else:
            # name of initfunction
            initname = "init" + fullname.split(".")[-1]
        filename = fullname.replace(".", "\\")
        if filename in ("pywintypes", "pythoncom"):
            filename = filename + "%d%d" % sys.version_info[:2]
            suffixes = ('.dll',)
        else:
            suffixes = self._suffixes
        for s in suffixes:
            path = filename + s
            if path in self._files:
                if verbose > 1:
                    sys.stderr.write("# found %s in zipfile %s\n"
                                     % (path, self.archive))
                mod = _memimporter.import_module(fullname, path,
                                                 initname,
                                                 self.get_data)
                mod.__file__ = "%s\\%s" % (self.archive, path)
                mod.__loader__ = self
                if verbose:
                    sys.stderr.write("import %s # loaded from zipfile %s\n"
                                     % (fullname, mod.__file__))
                return mod
        raise zipimport.ZipImportError("can't find module %s" % fullname)

    def __repr__(self):
        return "<%s object %r>" % (self.__class__.__name__, self.archive)

def install():
    "Install the zipextimporter"
    sys.path_hooks.insert(0, ZipExtensionImporter)
    # Not sure if this is needed...
    sys.path_importer_cache.clear()
    ## # Not sure if this is needed...
    ## import importlib
    ## importlib.invalidate_caches()

################################################################

if __name__ == "__main__":
    # test code
    import glob
    import os
    import struct
    import sys
    import zipextimporter
    import zipfile

    try:
        reload
    except NameError:
        from imp import reload

    print(sys.version)

##    input("Attach debugger...")

    if hasattr(sys, "gettotalrefcount"):
        suffix = "_d"
    else:
        suffix = ""
    if struct.calcsize("P") == 4:
        zippath = "lib-%d.%d-32%s.zip" % (sys.version_info[0],
                                          sys.version_info[1],
                                          suffix)
    else:
        zippath = "lib-%d.%d-64%s.zip" % (sys.version_info[0],
                                          sys.version_info[1],
                                          suffix)
    if not os.path.isfile(zippath):
        print("Creating zip-archive containing extension modules...")
        z = zipfile.ZipFile(zippath, "w")
        for subdir in ("pcbuild", "DLLs"):
            for path in glob.glob(os.path.join(sys.prefix,
                                               subdir,
                                               "*%s.pyd" % suffix)):
                print(path)
                z.write(path, os.path.basename(path))
        z.close()

    z = zipfile.ZipFile(zippath)

    extensions = [os.path.splitext(name)[0]
                  for name in z.namelist()]

##    print(extensions)
    extensions = [name[:len(name) - len(suffix)] for name in extensions
                  if name not in sys.modules]

    zipextimporter.install()
    sys.path.insert(0, zippath)

    for ext in extensions:
        if ext not in ("_sqlite3", "_tkinter"):
            print(ext, end=": ")
            try:
                x = __import__(ext)
            except Exception as details:
                import traceback; traceback.print_exc()
                print("\n\tError:", repr(details))
            else:
                print(x)

    import _socket
    print(_socket)
    reload(_socket)
    print(_socket)
