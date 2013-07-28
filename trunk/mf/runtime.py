#!/usr/bin/python3.3-32
# -*- coding: utf-8 -*-
from mf4 import ModuleFinder

import imp
import io
import marshal
import os
import shutil
import sys
import zipfile

class Runtime(object):
    """This class represents the Python runtime: all needed modules
    and packages.  The runtime will be written to a zip.file
    (typically named pythonxy.zip) that can be added to sys.path.
    """

    # modules which are always needed
    bootstrap_modules = ("codecs",
                         "io",
                         "runpy",
                         "encodings.*")

    def __init__(self, options):
        self.options = options

    def analyze(self):
        global PYC
        PYC = ".pyc" if not self.options.optimize else ".pyo"

        excludes = self.options.excludes if self.options.excludes else ()
        optimize = self.options.optimize if self.options.optimize else 0

        mf = self.mf = ModuleFinder(excludes=excludes,
                                    optimize=optimize)

        for modname in self.bootstrap_modules:
            if modname.endswith(".*"):
                self.mf.import_package(modname[:-2])
            else:
                self.mf.import_hook(modname)

        if self.options.includes:
            for modname in self.options.includes:
                mf.import_hook(modname)

        if self.options.packages:
            for modname in self.options.packages:
                mf.import_package(modname)

        mf.run_script(self.options.script)

    def build(self, filename):
        if self.options.report:
            self.mf.report()
        if self.options.summary:
            self.mf.report_summary()
            self.mf.report_missing()
        arc = zipfile.ZipFile(filename,
                              "w",
                              compression=zipfile.ZIP_DEFLATED)
        for mod in self.mf.modules.values():
            code = mod.__code__
            if code:
                if hasattr(mod, "__path__"):
                    path = mod.__name__.replace(".", "\\") + "\\__init__" + PYC
                else:
                    path = mod.__name__.replace(".", "\\") + PYC
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
                    path = mod.__name__.replace(".", "\\") + "\\__init__" + PYC
                else:
                    path = mod.__name__.replace(".", "\\") + PYC
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
        print("Wrote archive: %s" % filename)
        ################################

        path = os.path.splitext(self.options.script)[0] + ".bat"
        with open(path, "wt") as ofi:
            ofi.write("@echo off\n")
            ofi.write("setlocal\n")
            ofi.write("set PYTHONHOME=.\n")
            ofi.write("set PYTHONPATH=%s\n" % filename)
            ofi.write("%s -S -m __SCRIPT__\n" % sys.executable)
        print("Wrote runner: %s" % path)

# Hm, imp.load_dynamic is deprecated.  What is the replacement?
LOADER = r"""\
def __load():
    import imp, os, sys
    try:
        dirname = os.path.dirname(__loader__.archive)
    except NameError:
        dirname = sys.prefix
    path = os.path.join(dirname, '%s')
    data = __loader__.get_data("--DLLs--\\" + path)
    with open(path, "wb") as dll:
        dll.write(data)
##    print("\t\t\tload_dynamic", __name__, path)
    mod = imp.load_dynamic(__name__, path)
    mod.frozen = 1
__load()
del __load
"""

################################################################

## if __name__ == "__main__":
##     runtime = Runtime(
##         optimize=2,
## ##        excludes=["importlib"],
##         )
## ##    runtime.run_script("hello.py")
## ##    runtime.run_script(r"c:/users/thomas/devel/mytss5/dist/components/_Pythonlib/prog/sme.py")
##     runtime.run_script(r"c:/users/thomas/devel/mytss5/dist/components/_Pythonlib/prog/toflogviewer2.py")
##     runtime.import_package("encodings")
##     runtime.import_module("compat.rename_modules")
##     runtime.import_module("fpgui.controls")
##     runtime.import_module("fpgui.dialogs")
##     ## runtime.import_module("ctypes")
##     ## runtime.import_module("os")
## ##    runtime.import_module("bz2")
## ##    runtime.import_module("zipfile")
## ##    runtime.import_module("_lzma")
##     ## runtime.import_module("importlib.machinery")
##     ## runtime.import_module("importlib._bootstrap")
## ##    runtime.build("dist\\library.zip")
##     runtime.build("python33.zip")

################################################################

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build runtime archive for a script")

    parser.add_argument("-i", "--include",
                        help="module to include",
                        dest="includes",
                        metavar="modname",
##                        nargs="*",
                        action="append"
                        )
    parser.add_argument("-x", "--exclude",
                        help="module to exclude",
                        dest="excludes",
                        metavar="modname",
                        action="append")
    parser.add_argument("-p", "--package",
                        help="module to exclude",
                        dest="packages",
                        metavar="package_name",
##                        nargs="*",
                        action="append")

    # how to scan...
    parser.add_argument("-O", "--optimize",
                        help="scan optimized bytecode",
                        dest="optimize",
                        action="count")

    # reporting options...
    parser.add_argument("-s", "--summary",
                        help="""print a single line listing how many modules were
                        found and how many modules are missing""",
                        dest="summary",
                        action="store_true")
    parser.add_argument("-r", "--report",
                        help="""print a detailed report listing all found modules,
                        the missing modules, and which module imported them.""",
                        dest="report",
                        action="store_true")
    parser.add_argument("-f", "--from",
                        help="""print a detailed report listing all found modules,
                        the missing modules, and which module imported them.""",
                        metavar="modname",
                        dest="from",
                        action="append")

    parser.add_argument("script",
                        metavar="script",
##                        action="append",
##                        nargs="*"
                        )

    options = parser.parse_args()
    print(options)

    runtime = Runtime(options)
    runtime.analyze()
    runtime.build("python33.zip")
    
if __name__ == "__main__":
    main()
