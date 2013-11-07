#!/usr/bin/python3.3-32
# -*- coding: utf-8 -*-
from dllfinder import Scanner, pydll

import distutils.util
import imp
import io
import logging
import marshal
import os
import pkgutil
import shutil
import struct
import sys
import zipfile

from resources import UpdateResources

logger = logging.getLogger("runtime")

from importlib.machinery import EXTENSION_SUFFIXES
from importlib.machinery import DEBUG_BYTECODE_SUFFIXES, OPTIMIZED_BYTECODE_SUFFIXES

class Runtime(object):
    """This class represents the Python runtime: all needed modules
    and packages.  The runtime will be written to a zip.file
    (typically named pythonxy.zip) that can be added to sys.path.
    """

    # modules which are always needed
    bootstrap_modules = {
        # Needed for Python itself:
        "codecs",
        "io",
        "encodings.*",
        }

    def __init__(self, options):
        self.options = options

        if self.options.bundle_files < 3:
            self.bootstrap_modules.add("zipextimporter")

    def analyze(self):
        logger.info("Analyzing the code")

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
        if missing:
            mf.report_missing()

##     def build_bat(self, filename, libname):
##         logger.info("Building batch-file %r", filename)
##         if not self.options.optimize:
##             options = ""
##         elif self.options.optimize == 1:
##             options = " -O "
##         else:
##             options = " -OO "
##         ## if self.options.destdir:
##         ##     path = os.path.join(self.options.destdir, filename)
##         ## else:
##         ##     path = filename
##         path = filename

##         with open(path, "wt") as ofi:
##             ofi.write('@echo off\n')
##             ofi.write('setlocal\n')
##             if self.options.bundle_files < 3:
##                 ofi.write('set PY2EXE_DLLDIR=%TMP%\\~py2exe-%RANDOM%-%TIME:~6,5%\n')
##                 ofi.write('mkdir "%PY2EXE_DLLDIR%"\n')
##             ofi.write('for /f %%i in ("%0") do set PYTHONHOME=%%~dpi\n')
##             ofi.write('for /f %%i in ("%0") do set PYTHONPATH=%%~dpi\\{0}\n'.format(libname))
##             ofi.write('%PYTHONHOME%\\{0} -S {1} -m __SCRIPT__\n'.format(libname, options))
##             if self.options.bundle_files < 3:
##                 ofi.write('rmdir /s/q "%PY2EXE_DLLDIR%"\n')

    def build_exe(self, exe_path, libname):
        """Build the exe-file."""
        logger.info("Building exe '%s'", exe_path)
        run_stub = '%s-py%s.%s-%s.exe' % ("run",
                                          sys.version_info[0],
                                          sys.version_info[1],
                                          distutils.util.get_platform())
        print("Using exe-stub %r" % run_stub)
        exe_bytes = pkgutil.get_data("py3exe", run_stub)
        with open(exe_path, "wb") as ofi:
            ofi.write(exe_bytes)

        optimize = self.options.optimize
        unbuffered = False # XXX

        script_data = self._create_script_data()

        if libname is None:
            zippath = b""
        else:
            zippath = libname.encode("mbcs")
            

        script_info = struct.pack("IIII",
                                  0x78563412,
                                  optimize if optimize is not None else 0,
                                  unbuffered,
                                  len(script_data))
        script_info += zippath + b"\0" + script_data + b"\0"

        with UpdateResources(exe_path) as resource:
            if self.options.bundle_files < 3:
                with open(pydll, "rb") as ifi:
                    pydll_bytes = ifi.read()
                resource.add("PYTHON33.DLL", 1, pydll_bytes)

            resource.add("PYTHONSCRIPT", 1, script_info)

    def _create_script_data(self):
        # We create a list of code objects, and return it as a
        # marshaled stream.  The framework code then just exec's these
        # in order.
        code_objects = []

        ## # First is our common boot script.
        ## boot = self.get_boot_script("common")
        ## boot_code = compile(file(boot, "U").read(),
        ##                     os.path.abspath(boot), "exec")
        ## code_objects = [boot_code]
        ## if self.bundle_files < 3:
        ##     code_objects.append(
        ##         compile("import zipextimporter; zipextimporter.install()",
        ##                 "<install zipextimporter>", "exec"))
        ## for var_name, var_val in vars.iteritems():
        ##     code_objects.append(
        ##             compile("%s=%r\n" % (var_name, var_val), var_name, "exec")
        ##     )
        ## if self.custom_boot_script:
        ##     code_object = compile(file(self.custom_boot_script, "U").read() + "\n",
        ##                           os.path.abspath(self.custom_boot_script), "exec")
        ##     code_objects.append(code_object)
        ## if script:
        ##     code_object = compile(open(script, "U").read() + "\n",
        ##                           os.path.basename(script), "exec")
        ##     code_objects.append(code_object)
        ## code_bytes = marshal.dumps(code_objects)

        code_objects = []
        if self.options.bundle_files < 3:
            obj = compile("import sys, os; sys.path.append(os.path.dirname(sys.path[0])); del sys, os",
                          "<bootstrap>", "exec")
            code_objects.append(obj)
            obj = compile("import zipextimporter; zipextimporter.install(); del zipextimporter",
                          "<install zipextimporter>", "exec")
            code_objects.append(obj)

        ## code_objects.append(
        ##     compile("print(__name__); print(dir())",
        ##             "<testing>", "exec"))
        with open(self.options.script, "U") as script_file:
            code_objects.append(
                compile(script_file.read() + "\n",
                        os.path.basename(self.options.script), "exec"))

        return marshal.dumps(code_objects)

    def build_library(self, exe_path, libname):
        """Build the archive containing the Python library."""
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

        if self.options.optimize:
            bytecode_suffix = OPTIMIZED_BYTECODE_SUFFIXES[0]
        else:
            bytecode_suffix = DEBUG_BYTECODE_SUFFIXES[0]

        arc = zipfile.ZipFile(libpath, libmode,
                              compression=zipfile.ZIP_DEFLATED)

        ## with open(self.options.script, "r") as scriptfile:
        ##     arc.writestr("__SCRIPT__.py", scriptfile.read())
        dlldir = os.path.dirname(libpath)

        for mod in self.mf.modules.values():
            code = mod.__code__
            if code:
                if hasattr(mod, "__path__"):
                    path = mod.__name__.replace(".", "\\") + "\\__init__" + bytecode_suffix
                else:
                    path = mod.__name__.replace(".", "\\") + bytecode_suffix
                stream = io.BytesIO()
                stream.write(imp.get_magic())
                stream.write(b"\0\0\0\0") # null timestamp
                stream.write(b"\0\0\0\0") # null size
                marshal.dump(code, stream)
                arc.writestr(path, stream.getvalue())

            elif hasattr(mod, "__file__"):
                assert mod.__file__.endswith(EXTENSION_SUFFIXES[0])

                # bundle_files == 3: put .pyds in the same directory as the zip.archive
                # bundle_files <= 2: put .pyds into the zip-archive, extract to TEMP dir when needed

                pydfile = mod.__name__ + EXTENSION_SUFFIXES[0]

                if self.options.bundle_files < 3:
                    print("Add PYD %s to %s" % (os.path.basename(mod.__file__), libpath))
                    arc.write(mod.__file__, pydfile)
                else:
                    # Copy the extension into dlldir. To be able to
                    # load it without putting dlldir into sys.path, we
                    # create a loader module and put that into the
                    # archive.
                    src = LOAD_FROM_DIR.format(pydfile)

                    code = compile(src, "<string>", "exec")
                    if hasattr(mod, "__path__"):
                        path = mod.__name__.replace(".", "\\") + "\\__init__" + bytecode_suffix
                    else:
                        path = mod.__name__.replace(".", "\\") + bytecode_suffix
                    stream = io.BytesIO()
                    stream.write(imp.get_magic())
                    stream.write(b"\0\0\0\0") # null timestamp
                    stream.write(b"\0\0\0\0") # null size
                    marshal.dump(code, stream)
                    arc.writestr(path, stream.getvalue())

                    print("Copy PYD %s to %s" % (os.path.basename(mod.__file__), dlldir))
                    shutil.copy2(mod.__file__, dlldir)

        for src in self.mf.required_dlls():
            if src.lower() == pydll:
                if self.options.bundle_files < 3:
                    # Python dll is special, will be added as resource to the library archive...
                    # print("Skipping %s" % pydll)
                    pass
                else:
                    print("Copy DLL %s to %s" % (os.path.basename(src), dlldir))
                    shutil.copy2(src, dlldir)
            elif self.options.bundle_files < 3:
                ## dst = os.path.join("--DLLS--", os.path.basename(src))
                ## print("Add DLL %s to %s" % (os.path.basename(dst), libpath))
                ## arc.write(src, dst)

                ## XXX We should refuse to do this with pywintypesXY.dll
                ## or pythoncomXY.dll...  Or write a special loader for them...
                ## Or submit the loader to the PyWin32 project...
                dst = os.path.basename(src)
                print("Add DLL %s to %s" % (dst, libpath))
                arc.write(src, dst)
##                print("SKIP DLL", os.path.basename(src))
            else:
                dst = os.path.join(dlldir, os.path.basename(src))
                print("Copy DLL %s to %s" % (os.path.basename(src), dlldir))
                shutil.copy2(src, dlldir)

        arc.close()

################################################################

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
