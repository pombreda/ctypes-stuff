#!/usr/bin/python3.3-32
# -*- coding: utf-8 -*-
from dllfinder import Scanner

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
        logger.info("Analyzing the code")
        # XXX Use importlib!!! to get extensions...
        global PYC
        PYC = ".pyc" if not self.options.optimize else ".pyo"

        excludes = self.options.excludes if self.options.excludes else ()
        optimize = self.options.optimize if self.options.optimize else 0

        mf = self.mf = Scanner(excludes=excludes,
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

        missing, maybe = mf.missing_maybe()
        logger.info("Found %d modules, %d are missing, %d may be missing",
                    len(mf.modules), len(missing), len(maybe))

    def build_bat(self, filename, libname):
        logger.info("Building batch-file %r", filename)
        if not self.options.optimize:
            options = ""
        elif self.options.optimize == 1:
            options = " -O "
        else:
            options = " -OO "
        ## if self.options.destdir:
        ##     path = os.path.join(self.options.destdir, filename)
        ## else:
        ##     path = filename
        path = filename

        with open(path, "wt") as ofi:
            ofi.write('@echo off\n')
            ofi.write('setlocal\n')
            if self.options.bundle_files < 3:
                ofi.write('set PY2EXE_DLLDIR=%TMP%\\~py2exe-%RANDOM%-%TIME:~6,5%\n')
                ofi.write('mkdir "%PY2EXE_DLLDIR%"\n')
            ofi.write('for /f %%i in ("%0") do set PYTHONHOME=%%~dpi\n')
            ofi.write('for /f %%i in ("%0") do set PYTHONPATH=%%~dpi\\{0}\n'.format(libname))
            ofi.write('%PYTHONHOME%\\{0} -S {1} -m __SCRIPT__\n'.format(libname, options))
            if self.options.bundle_files < 3:
                ofi.write('rmdir /s/q "%PY2EXE_DLLDIR%"\n')

    def build_exe(self, exe_path, libname):
        logger.info("Building exe '%s'", exe_path)
        import pkgutil
        exe_bytes = pkgutil.get_data("py3exe", "run.exe")
        with open(exe_path, "wb") as ofi:
            ofi.write(exe_bytes)

        from resources import add_resources
        import struct

        optimize=True
        unbuffered = False
        data_bytes=0

        if libname is None:
            zippath = b""
        else:
            zippath = libname.encode("mbcs")
            

        script_info = struct.pack("IIII",
                                  0x78563412,
                                  optimize,
                                  unbuffered,
                                  data_bytes) + zippath + b"\0"

        add_resources(exe_path, script_info)

    def build(self, exe_path, libname):
        if self.options.report:
            self.mf.report()
        if self.options.summary:
            self.mf.report_summary()
            self.mf.report_missing()

        if libname is None:
            libpath = exe_path
            libmode = "a"
        else:
            libpath = os.path.join(os.path.dirname(exe_path), libname)
            libmode = "w"
        logger.info("Building the code archive %r", libpath)

        arc = zipfile.ZipFile(libpath, libmode,
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
                stream.write(b"\0\0\0\0") # null timestamp
                stream.write(b"\0\0\0\0") # null size
                marshal.dump(code, stream)
                arc.writestr(path, stream.getvalue())

            elif hasattr(mod, "__file__"):
                # XXX use importlib to get extensions...
                assert mod.__file__.endswith(".pyd")

                # bundle_files == 3: put .pyds in the same directory as the zip.archive
                # bundle_files <= 2: put .pyds into the zip-archive, extract to TEMP dir when needed

                pydfile = mod.__name__ + ".pyd"

                # Build the loader which is contained in the zip-archive
                if self.options.bundle_files < 3:
                    src = EXTRACT_THEN_LOAD.format(pydfile)
                else:
                    src = LOAD_FROM_DIR.format(pydfile)

                code = compile(src, "<string>", "exec")
                if hasattr(mod, "__path__"):
                    path = mod.__name__.replace(".", "\\") + "\\__init__" + PYC
                else:
                    path = mod.__name__.replace(".", "\\") + PYC
                stream = io.BytesIO()
                stream.write(imp.get_magic())
                stream.write(b"\0\0\0\0") # null timestamp
                stream.write(b"\0\0\0\0") # null size
                marshal.dump(code, stream)
                arc.writestr(path, stream.getvalue())

                if self.options.bundle_files < 3:
                    arc.write(mod.__file__, os.path.join("--EXTENSIONS--", pydfile))
                else:
                    shutil.copyfile(mod.__file__,
                                    os.path.join(os.path.dirname(libpath), pydfile))

        dlldir = os.path.dirname(libpath)
        for src in self.mf.required_dlls():
            if self.options.bundle_files < 3:
                dst = os.path.join("--DLLS--", os.path.basename(src))
                arc.write(src, dst)
            else:
                dst = os.path.join(dlldir, os.path.basename(src))
                shutil.copyfile(src, dst)

        arc.close()

################################################################

EXTRACT_THEN_LOAD = r"""\
def __load():
    import imp, os, _p2e
    path = os.path.join(__loader__.archive, "--EXTENSIONS--", '{0}')
    py2exe_dlldir = os.path.dirname(__loader__.archive)
    data = __loader__.get_data(path)
    dstpath = os.path.join(py2exe_dlldir, '{0}')
    with open(dstpath, "wb") as dll:
        dll.write(data)
    _p2e.register_dll(dstpath) # register before importing; just in case.
    mod = imp.load_dynamic(__name__, dstpath)
    mod.frozen = 1
__load()
del __load
"""

LOAD_FROM_DIR = r"""\
def __load():
    import imp, os
    dllpath = os.path.join(os.path.dirname(__loader__.archive), '{0}')
    mod = imp.load_dynamic(__name__, dllpath)
    mod.frozen = 1
__load()
del __load
"""

################################################################
