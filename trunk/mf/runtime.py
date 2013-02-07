#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
from mf import ModuleFinder

import imp
import io
import marshal
import os
import shutil
import zipfile

class Runtime(object):
    """This class represents the Python runtime: all needed modules
    and packages.  The runtime will be written to a zip.file
    (typically named pythonxy.zip) that can be added to sys.path.
    """

    # modules which are always needed
    bootstrap_modules = ("codecs",
                         "io",
                         "encodings.aliases",
                         "encodings.cp850",
                         "encodings.latin_1",
                         "encodings.mbcs",
                         "encodings.utf_8")

    def __init__(self, excludes=[]):
        self.mf = ModuleFinder(excludes=excludes)
        for modname in self.bootstrap_modules:
            if modname.endswith(".*"):
                self.mf.include_package(modname)
            else:
                self.mf.import_hook(modname)

    def import_module(self, modname):
        self.mf.import_hook(modname)

    def build(self, filename):
        arc = zipfile.ZipFile(filename, "w")
        for mod in self.mf.modules.values():
            code = mod.__code__
            if code:
                if hasattr(mod, "__path__"):
                    path = mod.__name__.replace(".", "\\") + "\\__init__.pyc"
                else:
                    path = mod.__name__.replace(".", "\\") + ".pyc"
                stream = io.BytesIO()
                stream.write(imp.get_magic())
                stream.write(b"\0\0\0\0") # faked timestamp
                stream.write(b"\0\0\0\0") # faked size
                marshal.dump(code, stream)
                arc.writestr(path, stream.getvalue())
            elif hasattr(mod, "__file__"):
                pydfile = mod.__name__ + ".pyd"
                src = LOADER % pydfile
                code = compile(src, "<string>", "exec")
                if hasattr(mod, "__path__"):
                    path = mod.__name__.replace(".", "\\") + "\\__init__.pyc"
                else:
                    path = mod.__name__.replace(".", "\\") + ".pyc"
                stream = io.BytesIO()
                stream.write(imp.get_magic())
                stream.write(b"\0\0\0\0") # faked timestamp
                stream.write(b"\0\0\0\0") # faked size
                marshal.dump(code, stream)
                arc.writestr(path, stream.getvalue())

                assert mod.__file__.endswith(".pyd")
                arc.write(mod.__file__, os.path.join("--DLLs--", pydfile))

                ## dest = os.path.join("dist", mod.__name__) + ".pyd"
                ## shutil.copyfile(mod.__file__, dest)
                ## print("copy", mod.__file__, dest)
        arc.close()

# Hm, imp.load_dynamic is deprecated.  What is the replacement?
LOADER = """
def __load():
    import imp, os, sys
    try:
        dirname = os.path.dirname(__loader__.archive)
    except NameError:
        dirname = sys.prefix
    path = os.path.join(dirname, '%s')
##    print('Load extension %%s from %%s' %% (__name__, path))
    mod = imp.load_dynamic(__name__, path)
##    mod.frozen = 1
__load()
del __load
"""

if __name__ == "__main__":
    runtime = Runtime(
##        excludes=["importlib"],
        )
    runtime.import_module("ctypes")
    runtime.import_module("os")
    runtime.import_module("bz2")
    runtime.import_module("importlib.machinery")
    runtime.import_module("importlib._bootstrap")
    runtime.build("dist\\library.zip")
