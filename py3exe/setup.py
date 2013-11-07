#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
import os
import sys

from setuptools import setup, find_packages

from distutils.core import Extension, Command
from distutils.dist import Distribution
from distutils.command import build_ext, build
from distutils.command.install_data import install_data
from distutils.sysconfig import customize_compiler
from distutils.dep_util import newer_group
from distutils.errors import *
from distutils.util import get_platform

if sys.version_info < (3, 3):
    raise DistutilsError("This package requires Python 3.3 or later")


# We don't need a manifest in the executable, so monkeypath the code away:
from distutils.msvc9compiler import MSVCCompiler
MSVCCompiler.manifest_setup_ldargs = lambda *args: None

class Interpreter(Extension):
    def __init__(self, *args, **kw):
        # Add a custom 'target_desc' option, which matches CCompiler
        # (is there a better way?
        if "target_desc" in kw:
            self.target_desc = kw['target_desc']
            del kw['target_desc']
        else:
            self.target_desc = "executable"
        Extension.__init__(self, *args, **kw)


class Dist(Distribution):
    def __init__(self,attrs):
        self.interpreters = None
        Distribution.__init__(self, attrs)

    def has_interpreters(self):
        return self.interpreters and len(self.interpreters) > 0

    def has_extensions(self):
        return False

class BuildInterpreters(build_ext.build_ext):
    description = "build special python interpreter stubs"

    def finalize_options(self):
        build_ext.build_ext.finalize_options(self)
        self.interpreters = self.distribution.interpreters

    def run (self):
        if not self.interpreters:
            return

        self.setup_compiler()

        # Now actually compile and link everything.
        for inter in self.interpreters:
            sources = inter.sources
            if sources is None or type(sources) not in (type([]), type(())):
                raise DistutilsSetupError(("in 'interpreters' option ('%s'), " +
                       "'sources' must be present and must be " +
                       "a list of source filenames") % inter.name)
            sources = list(sources)

            fullname = self.get_exe_fullname(inter.name)
            if self.inplace:
                # ignore build-lib -- put the compiled extension into
                # the source tree along with pure Python modules
                modpath = fullname.split('.')
                package = '.'.join(modpath[0:-1])
                base = modpath[-1]

                build_py = self.get_finalized_command('build_py')
                package_dir = build_py.get_package_dir(package)
                exe_filename = os.path.join(package_dir,
                                            self.get_exe_filename(base))
            else:
                exe_filename = os.path.join(self.build_lib,
                                            self.get_exe_filename(fullname))
            if inter.target_desc == "executable":
                exe_filename += ".exe"
            else:
                exe_filename += ".dll"

            if not (self.force or \
                    newer_group(sources + inter.depends, exe_filename, 'newer')):
                self.announce("skipping '%s' interpreter (up-to-date)" %
                              inter.name)
                continue # 'for' loop over all interpreters
            else:
                self.announce("building '%s' interpreter" % inter.name)

            extra_args = inter.extra_compile_args or []

            macros = inter.define_macros[:]
            for undef in inter.undef_macros:
                macros.append((undef,))

            objects = self.compiler.compile(sources,
                                            output_dir=self.build_temp,
                                            macros=macros,
                                            include_dirs=inter.include_dirs,
                                            debug=self.debug,
                                            extra_postargs=extra_args,
                                            depends=inter.depends)

            if inter.extra_objects:
                objects.extend(inter.extra_objects)
            extra_args = inter.extra_link_args or []

            if inter.export_symbols:
                # The mingw32 compiler writes a .def file containing
                # the export_symbols.  Since py2exe uses symbols in
                # the extended form 'DllCanUnloadNow,PRIVATE' (to
                # avoid MS linker warnings), we have to replace the
                # comma(s) with blanks, so that the .def file can be
                # properly parsed.
                # XXX MingW32CCompiler, or CygwinCCompiler ?
                from distutils.cygwinccompiler import Mingw32CCompiler
                if isinstance(self.compiler, Mingw32CCompiler):
                    inter.export_symbols = [s.replace(",", " ") for s in inter.export_symbols]
                    inter.export_symbols = [s.replace("=", "\t") for s in inter.export_symbols]

            # XXX - is msvccompiler.link broken?  From what I can see, the
            # following should work, instead of us checking the param:
            self.compiler.link(inter.target_desc,
                               objects, exe_filename,
                               libraries=self.get_libraries(inter),
                               library_dirs=inter.library_dirs,
                               runtime_library_dirs=inter.runtime_library_dirs,
                               export_symbols=inter.export_symbols,
                               extra_postargs=extra_args,
                               debug=self.debug)
    # build_extensions ()

    def get_exe_fullname (self, inter_name):
        if self.package is None:
            return inter_name
        else:
            return self.package + '.' + inter_name

    def get_exe_filename (self, inter_name):
        ext_path = inter_name.split('.')
        if self.debug:
            fnm = os.path.join(*ext_path) + '_d'
        else:
            fnm = os.path.join(*ext_path)
        return '%s-py%s.%s-%s' % (fnm, sys.version_info[0], sys.version_info[1], get_platform())

    def setup_compiler(self):
        # This method *should* be available separately in build_ext!
        from distutils.ccompiler import new_compiler

        # If we were asked to build any C/C++ libraries, make sure that the
        # directory where we put them is in the library search path for
        # linking interpreters.
        if self.distribution.has_c_libraries():
            build_clib = self.get_finalized_command('build_clib')
            self.libraries.extend(build_clib.get_library_names() or [])
            self.library_dirs.append(build_clib.build_clib)

        # Setup the CCompiler object that we'll use to do all the
        # compiling and linking
        self.compiler = new_compiler(compiler=self.compiler,
                                     verbose=self.verbose,
                                     dry_run=self.dry_run,
                                     force=self.force)
        try:
            self.compiler.initialize()
        except AttributeError:
            pass # initialize doesn't exist before 2.5
        customize_compiler(self.compiler)

        # And make sure that any compile/link-related options (which might
        # come from the command-line or from the setup script) are set in
        # that CCompiler object -- that way, they automatically apply to
        # all compiling and linking done here.
        if self.include_dirs is not None:
            self.compiler.set_include_dirs(self.include_dirs)
        if self.define is not None:
            # 'define' option is a list of (name, value) tuples
            for (name,value) in self.define:
                self.compiler.define_macro(name, value)
        if self.undef is not None:
            for macro in self.undef:
                self.compiler.undefine_macro(macro)
        if self.libraries is not None:
            self.compiler.set_libraries(self.libraries)
        if self.library_dirs is not None:
            self.compiler.set_library_dirs(self.library_dirs)
        if self.rpath is not None:
            self.compiler.set_runtime_library_dirs(self.rpath)
        if self.link_objects is not None:
            self.compiler.set_link_objects(self.link_objects)

    # setup_compiler()

# class BuildInterpreters

def InstallSubCommands():
    """Adds our own sub-commands to build and install"""
    has_interpreters = lambda self: self.distribution.has_interpreters()
    buildCmds = [('build_interpreters', has_interpreters)]
    build.build.sub_commands.extend(buildCmds)

InstallSubCommands()

############################################################################

############################################################################

# This ensures that data files are copied into site_packages rather than
# the main Python directory.
class smart_install_data(install_data):
    def run(self):
        #need to change self.install_dir to the library dir
        install_cmd = self.get_finalized_command('install')
        self.install_dir = getattr(install_cmd, 'install_lib')
        return install_data.run(self)

## def iter_samples():
##     excludedDirs = ['CVS', 'build', 'dist']
##     for dirpath, dirnames, filenames in os.walk(r'py2exe\samples'):
##         for dir in dirnames:
##             if dir.startswith('.') and dir not in excludedDirs:
##                 excludedDirs.append(dir)
##         for dir in excludedDirs:
##             if dir in dirnames:
##                 dirnames.remove(dir)
##         qualifiedFiles = []
##         for filename in filenames:
##             if not filename.startswith('.'):
##                 qualifiedFiles.append(os.path.join(dirpath, filename))
##         if qualifiedFiles:
##             yield (dirpath, qualifiedFiles)

class deinstall(Command):
    description = "Remove all installed files"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.run_command('build')
        build = self.get_finalized_command('build')
        install = self.get_finalized_command('install')
        self.announce("removing files")
        for n in 'platlib', 'purelib', 'headers', 'scripts', 'data':
            dstdir = getattr(install, 'install_' + n)
            try:
                srcdir = getattr(build, 'build_' + n)
            except AttributeError:
                pass
            else:
                self._removefiles(dstdir, srcdir)

    def _removefiles(self, dstdir, srcdir):
        # Remove all files in dstdir which are present in srcdir
        assert dstdir != srcdir
        if not os.path.isdir(srcdir):
            return
        for n in os.listdir(srcdir):
            name = os.path.join(dstdir, n)
            if os.path.isfile(name):
                self.announce("removing '%s'" % name)
                if not self.dry_run:
                    try:
                        os.remove(name)
                    except OSError as details:
                        self.warn("Could not remove file: %s" % details)
                    if os.path.splitext(name)[1] == '.py':
                        # Try to remove .pyc and -pyo files also
                        try:
                            os.remove(name + 'c')
                        except OSError:
                            pass
                        try:
                            os.remove(name + 'o')
                        except OSError:
                            pass
            elif os.path.isdir(name):
                self._removefiles(name, os.path.join(srcdir, n))
                if not self.dry_run:
                    try:
                        os.rmdir(name)
                    except OSError as details:
                        self.warn("Are there additional user files?\n"\
                              "  Could not remove directory: %s" % details)
            else:
                self.announce("skipping removal of '%s' (does not exist)" %\
                              name)

def _is_debug_build():
    import imp
    for ext, _, _ in imp.get_suffixes():
        if ext == "_d.pyd":
            return True
    return False

if _is_debug_build():
    macros = [("PYTHONDLL", '\\"python%d%d_d.dll\\"' % sys.version_info[:2]),
              ("PYTHONCOM", '\\"pythoncom%d%d_d.dll\\"' % sys.version_info[:2]),
              ("_CRT_SECURE_NO_WARNINGS", '1')]
else:
    macros = [("PYTHONDLL", '\\"python%d%d.dll\\"' % sys.version_info[:2]),
              ("PYTHONCOM", '\\"pythoncom%d%d.dll\\"' % sys.version_info[:2]),
              ("_CRT_SECURE_NO_WARNINGS", '1')]

extra_compile_args = []
##extra_link_args = ["/DELAYLOAD:python%d%d.dll" % sys.version_info[:2], "delayimp.lib"]
extra_link_args = []

if 0:
    # enable this to debug a release build
    extra_compile_args.append("/Z7")
    extra_link_args.append("/DEBUG")
    macros.append(("VERBOSE", "1"))

run = Interpreter("py3exe.run",
                  ["source/start.c",
                   ## "source/run.c",
                   "source/icon.rc",

                   "source/MemoryModule.c",
                   "source/MyLoadLibrary.c",
                   "source/_memimporter.c",
                   "source/actctx.c",

                   ## "source/Python-dynload.c",
                   ## "source/MemoryModule.c",
                   ## "source/MyLoadLibrary.c",
                   ## "source/_memimporter.c",
                   ## "source/actctx.c",
                   ],
                  libraries=["user32"],
##                  depends=depends,
                  define_macros=macros,
                  extra_compile_args=extra_compile_args,
                  extra_link_args=extra_link_args,
                  )

## run_dll = Interpreter("py2exe.run_dll",
##                       ["source/run_dll.c",
##                        "source/start.c",
##                        "source/icon.rc",
##                        "source/Python-dynload.c",
##                        "source/MemoryModule.c",
##                        "source/MyLoadLibrary.c",
##                        "source/_memimporter.c",
##                        "source/actctx.c",
##                        ],
##                       libraries=["user32"],
##                       export_symbols=["DllCanUnloadNow,PRIVATE",
##                                       "DllGetClassObject,PRIVATE",
##                                       "DllRegisterServer,PRIVATE",
##                                       "DllUnregisterServer,PRIVATE",
##                                       ],
##                       target_desc = "shared_library",
## ##                      depends=depends,
##                       define_macros=macros,
##                       extra_compile_args=extra_compile_args,
##                       extra_link_args=extra_link_args,
##                       )

interpreters = [run] #, run_dll]

setup(name="py3exe",
      version="0.1.0",
      description="Build standalone executables for Windows",
      long_description=__doc__,
      author="Thomas Heller",
      author_email="theller@ctypes.org",
##      maintainer="Jimmy Retzlaff",
##      maintainer_email="jimmy@retzlaff.com",
##      url="http://www.py2exe.org/",
      license="MIT/X11",
      platforms="Windows",
##      download_url="http://sourceforge.net/project/showfiles.php?group_id=15583",
##      classifiers=["Development Status :: 5 - Production/Stable"],
      distclass = Dist,
      cmdclass = {'build_interpreters': BuildInterpreters,
##                  'deinstall': deinstall,
##                  'install_data': smart_install_data,
                 },

      scripts = ["build_setup.py"],
      interpreters = interpreters,
      packages = find_packages(),
##       packages=['py3exe',
## ##                'py2exe.resources',
##                ],
      )

# Local Variables:
# compile-command: "py -3.3 setup.py bdist_egg"
# End:
