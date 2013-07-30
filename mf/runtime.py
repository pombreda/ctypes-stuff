#!/usr/bin/python3.3-32
# -*- coding: utf-8 -*-
from mf4 import ModuleFinder

import imp
import io
import logging
import marshal
import os
import shutil
import sys
import zipfile

logger = logging.getLogger("runtime")

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

    def build_bat(self, filename, libname):
        if not self.options.optimize:
            options = ""
        elif self.options.optimize == 1:
            options = " -O "
        else:
            options = " -OO "
        with open(filename, "wt") as ofi:
            ofi.write('@echo off\n')
            ofi.write('setlocal\n')
            ofi.write('set PY2EXE_DLLDIR=%TMP%\\py2exe-%RANDOM%-%TIME:~6,5%\n')
            ofi.write('for /f %%i in ("%0") do set PYTHONHOME=%%~dpi\n')
            ofi.write('for /f %%i in ("%0") do set PYTHONPATH=%%~dpi\\{0}\n'.format(libname))
            ofi.write('mkdir "%PY2EXE_DLLDIR%"\n')
            ofi.write('%PYTHONHOME%\\{0} -S{1}-m __SCRIPT__\n'.format(libname, options))
            ofi.write('rmdir /s/q "%PY2EXE_DLLDIR%"\n')


    def build(self, library):
        if self.options.report:
            self.mf.report()
        if self.options.summary:
            self.mf.report_summary()
            self.mf.report_missing()

        shutil.copyfile(sys.executable, library)
        arc = zipfile.ZipFile(library, "a",
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
                src = LOADER.format(pydfile)
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
        ################################

# Hm, imp.load_dynamic is deprecated.  What is the replacement?
LOADER = r"""\
def __load():
    import imp, os
    py2exe_dlldir = os.environ["PY2EXE_DLLDIR"]
    path = os.path.join(__loader__.archive, "--DLLs--", '{0}')
    data = __loader__.get_data(path)
    dstpath = os.path.join(py2exe_dlldir, '{0}')
    with open(dstpath, "wb") as dll:
        dll.write(data)
    mod = imp.load_dynamic(__name__, dstpath)
    mod.frozen = 1
__load()
del __load
"""

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
                        )
    parser.add_argument("-v",
                        help="""
                        """,
                        dest="verbose",
                        action="store_true")
    options = parser.parse_args()

    level = logging.INFO if options.verbose else logging.WARNING
    logging.basicConfig(level=level)

    runner = os.path.splitext(options.script)[0] + ".bat"
    libname = "_" + os.path.splitext(options.script)[0] + ".exe"

    runtime = Runtime(options)
    runtime.build_bat(runner, libname)

    runtime.analyze()
    runtime.build(libname)

if __name__ == "__main__":
    main()
