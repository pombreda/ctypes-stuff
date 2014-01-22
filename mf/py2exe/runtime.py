#!/usr/bin/python3.3-32
# -*- coding: utf-8 -*-
from .dllfinder import Scanner, pydll

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

from .resources import UpdateResources
from .versioninfo import Version

logger = logging.getLogger("runtime")

from importlib.machinery import EXTENSION_SUFFIXES
from importlib.machinery import DEBUG_BYTECODE_SUFFIXES, OPTIMIZED_BYTECODE_SUFFIXES

RT_MANIFEST = 24

class Target:
    """
    A very loosely defined "target".  We assume either a "script" or "modules"
    attribute.  Some attributes will be target specific.
    """
    # A custom requestedExecutionLevel for the User Access Control portion
    # of the manifest for the target. May be a string, which will be used for
    # the 'requestedExecutionLevel' portion and False for 'uiAccess', or a tuple
    # of (string, bool) which specifies both values. If specified and the
    # target's 'template' executable has no manifest (ie, python 2.5 and
    # earlier), then a default manifest is created, otherwise the manifest from
    # the template is copied then updated.
    uac_info = None

    def __init__(self, **kw):
        self.__dict__.update(kw)
        # If modules is a simple string, assume they meant list
        m = self.__dict__.get("modules")
        if m and isinstance(m, str):
            self.modules = [m]

    def get_dest_base(self):
        dest_base = getattr(self, "dest_base", None)
        if dest_base: return dest_base
        script = getattr(self, "script", None)
        if script:
            return os.path.basename(os.path.splitext(script)[0])
        modules = getattr(self, "modules", None)
        assert modules, "no script, modules or dest_base specified"
        return modules[0].split(".")[-1]

    def validate(self):
        resources = getattr(self, "bitmap_resources", []) + \
                    getattr(self, "icon_resources", [])
        for r_id, r_filename in resources:
            if type(r_id) != type(0):
                # Hm, strings are also allowed as resource ids...
                raise DistutilsOptionError("Resource ID must be an integer")
            if not os.path.isfile(r_filename):
                raise DistutilsOptionError("Resource filename '%s' does not exist" % r_filename)

    def analyze(self, modulefinder):
        """Run modulefinder on anything that is needed for this target.

        This may be the script or one or more modules.
        """
        if hasattr(self, "script"):
            modulefinder.run_script(self.script)
        elif hasattr(self, "modules"):
            for mod in self.modules:
                modulefinder.import_hook(mod)
        else:
            raise RuntimeError("Don't know how to build", self)

    def __repr__(self):
        return "Target(dest_base=%r, exe_type=%r)" % (self.get_dest_base(), self.exe_type)


def fixup_targets(targets, default_attribute):
    """Fixup the targets; and ensure that the default_attribute is
    present.  Depending on the type of target, 'default_attribute' is
    "script" or "module".

    Return a list of Target instances.
    """
    if not targets:
        return []
    ret = []
    for target_def in targets:
        if isinstance(target_def, str):
            # Create a default target object, with the string as the attribute
            target = Target(**{default_attribute: target_def})
        else:
            d = getattr(target_def, "__dict__", target_def)
            if not default_attribute in d:
                raise DistutilsOptionError(
                      "This target class requires an attribute '%s'" % default_attribute)
            target = Target(**d)
        target.validate()
        ret.append(target)
    return ret


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

        self.targets = self.options.script + self.options.service

##         # build the executables
##         for target in dist.console:
##             dst = self.build_executable(target, self.get_console_template(),
##                                         arcname, target.script)
##             self.console_exe_files.append(dst)
##         for target in dist.windows:
##             dst = self.build_executable(target, self.get_windows_template(),
##                                         arcname, target.script)
##             self.windows_exe_files.append(dst)
##         for target in dist.service:
##             dst = self.build_service(target, self.get_service_template(),
##                                      arcname)
##             self.service_exe_files.append(dst)

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

        for target in self.targets:
            target.analyze(mf)

        mf.finish()

        missing, maybe = mf.missing_maybe()
        logger.info("Found %d modules, %d are missing, %d may be missing",
                    len(mf.modules), len(missing), len(maybe))

        if self.options.report:
            self.mf.report()

        elif self.options.summary:
            self.mf.report_summary()
            self.mf.report_missing()

        elif missing:
            mf.report_missing()

        for name, value in self.mf.get_min_bundle().items():
            if value > self.options.bundle_files:
                # warn if modules are know to work only for a minimum
                # bundle_files value
                print("OOPS:", name, value)
                raise SystemExit(-1)

    def build(self):
        """Build everything.
        """
        options = self.options

        destdir = options.destdir
        if not os.path.exists(destdir):
            os.mkdir(destdir)

        for i, target in enumerate(self.targets):
            # basename of the exe to create
            dest_base = target.get_dest_base()

            # full path to exe-file
            exe_path = os.path.join(destdir, dest_base + ".exe")

            if os.path.isfile(exe_path):
                os.remove(exe_path)

            self.build_exe(target, exe_path, options.libname)

            if options.libname is None:
                # Put the library into the exe itself.

                # It would probably make sense to run analyze()
                # separately for each exe so that they do not contain
                # unneeded stuff (from other exes)
                self.build_archive(exe_path)

        if options.libname is not None:
            # Build a library shared by ALL exes.
            libpath = os.path.join(destdir, options.libname)
            if os.path.isfile(libpath):
                os.remove(libpath)

            if not os.path.exists(os.path.dirname(libpath)):
                os.mkdir(os.path.dirname(libpath))

            dll_bytes = pkgutil.get_data("py2exe", "dll.dll")
            with open(libpath, "wb") as ofi:
                  ofi.write(dll_bytes)
            self.build_archive(libpath)

        self.copy_files(destdir)

        # data files
        for name, (src, recursive) in self.mf._data_directories.items():
            if recursive:
                dst = os.path.join(destdir, name)
                if os.path.isdir(dst):
                    # Emit a warning?
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                raise RuntimeError("not yet supported")

    def get_runstub_bytes(self, target):
        from distutils.util import get_platform
        if target.exe_type in ("console_exe", "service"):
            run_stub = 'run-py%s.%s-%s.exe' % (sys.version_info[0], sys.version_info[1], get_platform())
        elif target.exe_type == "windows_exe":
            run_stub = 'run_w-py%s.%s-%s.exe' % (sys.version_info[0], sys.version_info[1], get_platform())
        else:
            raise ValueError("Unknown exe_type %r" % target.exe_type)
        ## if self.options.verbose:
        ##     print("Using exe-stub %r" % run_stub)
        exe_bytes = pkgutil.get_data("py2exe", run_stub)
        if exe_bytes is None:
            raise RuntimeError("run-stub not found")
        return exe_bytes

    def build_exe(self, target, exe_path, libname):
        """Build the exe-file."""
        logger.info("Building exe '%s'", exe_path)

        exe_bytes = self.get_runstub_bytes(target)
        with open(exe_path, "wb") as ofi:
            ofi.write(exe_bytes)

        optimize = self.options.optimize
        unbuffered = False # XXX

        script_data = self._create_script_data(target)

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

        # It seems resources must be updated in chunks if there are
        # many, otherwise EndUpdateResource will fail with
        # WindowsError 13 (invalid data)
        with UpdateResources(exe_path, delete_existing=True) as resource:
            ## if self.options.verbose:
            ##     print("Add RSC %s/%s(%d bytes) to %s"
            ##           % ("PYTHONSCRIPT", 1, len(script_info), exe_path))
            resource.add(type="PYTHONSCRIPT", name=1, value=script_info)
##            # XXX testing
##            resource.add_string(1000, "foo bar")
##            resource.add_string(1001, "Hallöle €")

        with UpdateResources(exe_path, delete_existing=False) as resource:
            for res_type, res_name, res_data in getattr(target, "other_resources", ()):
                if res_type == RT_MANIFEST and isinstance(res_data, str):
                    res_data = res_data.encode("utf-8")
                resource.add(type=res_type, name=res_name, value=res_data)

        # Build and add a versioninfo resource
        def get(name):
            return getattr(target, name, None)

        if hasattr(target, "version"):
            version = Version(target.version,
                              file_description = get("description"),
                              comments = get("comments"),
                              company_name = get("company_name"),
                              legal_copyright = get("copyright"),
                              legal_trademarks = get("trademarks"),
                              original_filename = os.path.basename(exe_path),
                              product_name = get("product_name"),
                              product_version = get("product_version") or target.version)
                                  
        with UpdateResources(exe_path, delete_existing=False) as resource:
            from ._wapi import RT_VERSION
            resource.add(type=RT_VERSION,
                         name=1,
                         value=version.resource_bytes())

        for res_id, ico_file in getattr(target, "icon_resources", ()):
            with UpdateResources(exe_path, delete_existing=False) as resource:
                resource.add_icon(res_id, ico_file)



    def build_archive(self, libpath):
        """Build the archive containing the Python library.
        """
        if self.options.bundle_files <= 1:
            # Add pythonXY.dll as resource into the library file
            with UpdateResources(libpath, delete_existing=False) as resource:
                with open(pydll, "rb") as ifi:
                    pydll_bytes = ifi.read()
                # We do not need to replace the winver string resource
                # in the python dll since it will be loaded via
                # MemoryLoadLibrary, and so python cannot find the
                # string resources anyway.
                if self.options.verbose:
                    print("Add RSC %s/%s(%d bytes) to %s"
                          % (os.path.basename(pydll), 1, len(pydll_bytes), libpath))
                resource.add(type=os.path.basename(pydll), name=1, value=pydll_bytes)

        if self.options.optimize:
            bytecode_suffix = OPTIMIZED_BYTECODE_SUFFIXES[0]
        else:
            bytecode_suffix = DEBUG_BYTECODE_SUFFIXES[0]

        if self.options.compress:
            compression = zipfile.ZIP_DEFLATED
        else:
            compression = zipfile.ZIP_STORED

        # Create a zipfile and append it to the library file
        arc = zipfile.ZipFile(libpath, "a",
                              compression=compression)

        dlldir = os.path.dirname(libpath)

        for mod in self.mf.modules.values():
            if mod.__code__:
                if hasattr(mod, "__path__"):
                    path = mod.__name__.replace(".", "\\") + "\\__init__" + bytecode_suffix
                else:
                    path = mod.__name__.replace(".", "\\") + bytecode_suffix
                stream = io.BytesIO()
                stream.write(imp.get_magic())
                stream.write(b"\0\0\0\0") # null timestamp
                stream.write(b"\0\0\0\0") # null size
                marshal.dump(mod.__code__, stream)
                arc.writestr(path, stream.getvalue())

            elif hasattr(mod, "__file__"):
                assert mod.__file__.endswith(EXTENSION_SUFFIXES[0])
                if self.options.bundle_files <= 2:
                    # put .pyds into the archive
                    arcfnm = mod.__name__.replace(".", "\\") + EXTENSION_SUFFIXES[0]
                    if self.options.verbose:
                        print("Add PYD %s to %s" % (os.path.basename(mod.__file__), libpath))
                    arc.write(mod.__file__, arcfnm)
                else:
                    # The extension modules will be copied into
                    # dlldir.  To be able to import it without dlldir
                    # being on sys.path, create a loader module and
                    # put that into the archive.
                    pydfile = mod.__name__ + EXTENSION_SUFFIXES[0]
                    loader = LOAD_FROM_DIR.format(pydfile)

                    code = compile(loader, "<loader>", "exec")
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

        if self.options.bundle_files == 0:
            # put everything into the arc
            files = self.mf.all_dlls()
        elif self.options.bundle_files in (1, 2):
            # put only extension dlls into the arc
            files = self.mf.extension_dlls()
        else:
            arc.close()
            return

        for src in files:
            if self.options.verbose:
                print("Add DLL %s to %s" % (os.path.basename(src), libpath))
            arc.write(src, os.path.basename(src))

        arc.close()

    def copy_files(self, destdir):
        """Copy files (pyds, dlls, depending on the bundle_files value,
        into the dist resp. library directory.
        """
        if self.options.libname is not None:
            libdir = os.path.join(destdir, os.path.dirname(self.options.libname))
        else:
            libdir = destdir

        if self.options.bundle_files >= 2:
            # Python dll is not bundled; copy it into destdir
            dst = os.path.join(destdir, os.path.basename(pydll))
            if self.options.verbose:
                print("Copy DLL %s to %s" % (pydll, destdir))
            shutil.copy2(pydll, dst)
            with UpdateResources(dst, delete_existing=False) as resource:
                resource.add_string(1000, "py2exe")

        if self.options.bundle_files == 3:
            # copy extension modules; they go to libdir
            for mod in self.mf.modules.values():
                if mod.__code__:
                    # nothing to do for python modules.
                    continue
                if hasattr(mod, "__file__"):
                    assert mod.__file__.endswith(EXTENSION_SUFFIXES[0])
                    pydfile = mod.__name__ + EXTENSION_SUFFIXES[0]

                    dst = os.path.join(libdir, pydfile)
                    if self.options.verbose:
                        print("Copy PYD %s to %s" % (mod.__file__, dst))
                    shutil.copy2(mod.__file__, dst)

        if self.options.bundle_files < 1:
            return

        for src in self.mf.real_dlls():
            # Strange, but was tested with numpy built with
            # libiomp5md.dll...
            if self.options.bundle_files == 3:
                extdlldir = libdir
            else:
                extdlldir = destdir
            if self.options.verbose:
                print("Copy DLL %s to %s" % (src, extdlldir))
            shutil.copy2(src, extdlldir)

        if self.options.bundle_files == 3:
            # extension dlls go to libdir
            for src in self.mf.extension_dlls():
                if self.options.verbose:
                    print("Copy ExtensionDLL %s to %s" % (src, libdir))
                shutil.copy2(src, libdir)

    def _create_script_data(self, target):
        # We create a list of code objects, and return it as a
        # marshaled stream.  The framework code then just exec's these
        # in order.

        ## # First is our common boot script.
        ## boot = self.get_boot_script("common")
        ## boot_code = compile(file(boot, "U").read(),
        ##                     os.path.abspath(boot), "exec")
        ## code_objects = [boot_code]
        ## for var_name, var_val in vars.iteritems():
        ##     code_objects.append(
        ##             compile("%s=%r\n" % (var_name, var_val), var_name, "exec")
        ##     )
        ## if self.custom_boot_script:
        ##     code_object = compile(file(self.custom_boot_script, "U").read() + "\n",
        ##                           os.path.abspath(self.custom_boot_script), "exec")
        ##     code_objects.append(code_object)
        ## code_bytes = marshal.dumps(code_objects)

        code_objects = []

        # sys.executable has already been set in the run-stub

        # XXX should this be done in the exe-stub?
        code_objects.append(
            compile("import os, sys; sys.base_prefix = sys.prefix = os.path.dirname(sys.executable); del os, sys",
                    "<bootstrap2>", "exec"))

        if self.options.bundle_files < 3:
            # XXX do we need this one?
            ## obj = compile("import sys, os; sys.path.append(os.path.dirname(sys.path[0])); del sys, os",
            ##               "<bootstrap>", "exec")
            ## code_objects.append(obj)
            obj = compile("import zipextimporter; zipextimporter.install(); del zipextimporter",
                          "<install zipextimporter>", "exec")
            code_objects.append(obj)

        if target.exe_type == "service":
            # code for services
            code_objects.append(
                compile("cmdline_style = 'py2exe'; service_module_names = ['svc']",
                        "<service_info>", "exec"))

            boot = os.path.join(os.path.dirname(__file__), "boot_service.py")
            boot_code = compile(open(boot, "U").read(),
                                os.path.abspath(boot), "exec")
            code_objects.append(boot_code)

        elif target.exe_type in ("console_exe", "windows_exe"):
            boot = os.path.join(os.path.dirname(__file__), "boot_common.py")
            boot_code = compile(open(boot, "U").read(),
                                os.path.abspath(boot), "exec")
            code_objects.append(boot_code)

            with open(target.script, "U") as script_file:
                code_objects.append(
                    # XXX what about compiler options?
                    # XXX what about source file encodings?
                    compile(script_file.read() + "\n",
                            os.path.basename(target.script), "exec"))

        return marshal.dumps(code_objects)

################################################################

LOAD_FROM_DIR = r"""\
def __load():
    import imp, os
    dllpath = os.path.join(os.path.dirname(__loader__.archive), '{0}')
    try:
        mod = imp.load_dynamic(__name__, dllpath)
    except ImportError as details:
        raise ImportError('(%s) %r' % (details, dllpath)) from None
    mod.frozen = 1
__load()
del __load
"""

################################################################
