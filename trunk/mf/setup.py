#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""setup script for py2exe.
"""

import os
import sys

from setuptools import setup
##from distutils.core import setup

from py2exe_distutils import Dist, Interpreter, BuildInterpreters

############################################################################

if sys.version_info < (3, 3):
    raise RuntimeError("This package requires Python 3.3 or later")

############################################################################

def _is_debug_build():
    import imp
    for ext, _, _ in imp.get_suffixes():
        if ext == "_d.pyd":
            return True
    return False

if _is_debug_build():
    macros = [("PYTHONDLL", '\\"python%d%d_d.dll\\"' % sys.version_info[:2]),
##              ("PYTHONCOM", '\\"pythoncom%d%d_d.dll\\"' % sys.version_info[:2]),
              ("_CRT_SECURE_NO_WARNINGS", '1')]
else:
    macros = [("PYTHONDLL", '\\"python%d%d.dll\\"' % sys.version_info[:2]),
##              ("PYTHONCOM", '\\"pythoncom%d%d.dll\\"' % sys.version_info[:2]),
              ("_CRT_SECURE_NO_WARNINGS", '1')]

macros.append(("Py_BUILD_CORE", '1'))

extra_compile_args = []
extra_link_args = []

if 0:
    # enable this to debug a release build
    extra_compile_args.append("/Od")
    extra_compile_args.append("/Z7")
    extra_link_args.append("/DEBUG")
    macros.append(("VERBOSE", "1"))

run_ctypes_dll = Interpreter("py2exe.run_ctypes_dll",
                             ["source/run_ctypes_dll.c",
                              "source/start.c",
                              "source/icon.rc",

                              "source/MemoryModule.c",
                              "source/MyLoadLibrary.c",
                              "source/_memimporter.c",
                              "source/actctx.c",

                              "source/python-dynload.c",
                              ],
                             libraries=["user32", "shell32"],
                             export_symbols=["DllCanUnloadNow,PRIVATE",
                                             "DllGetClassObject,PRIVATE",
                                             "DllRegisterServer,PRIVATE",
                                             "DllUnregisterServer,PRIVATE",
                                             ],
                             target_desc = "shared_library",
                             define_macros=macros,
                             extra_compile_args=extra_compile_args,
                             extra_link_args=extra_link_args,
                             )

run = Interpreter("py2exe.run",
                  ["source/run.c",
                   "source/start.c",
                   "source/icon.rc",

                   "source/MemoryModule.c",
                   "source/MyLoadLibrary.c",
                   "source/_memimporter.c",
                   "source/actctx.c",

                   "source/python-dynload.c",
                   ],
                  libraries=["user32", "shell32"],
                  define_macros=macros,
                  extra_compile_args=extra_compile_args,
                  extra_link_args=extra_link_args,
                  )

run_w = Interpreter("py2exe.run_w",
                    ["source/run_w.c",
                     "source/start.c",
                     "source/icon.rc",

                     "source/MemoryModule.c",
                     "source/MyLoadLibrary.c",
                     "source/_memimporter.c",
                     "source/actctx.c",

                     "source/python-dynload.c",
                     ],
                    libraries=["user32", "shell32"],
                    define_macros=macros,
                    extra_compile_args=extra_compile_args,
                    extra_link_args=extra_link_args,
                    )

# The py2exe.resources name is special handled in BuildInterpreters;
# it will not include the python version and platform name. The final
# name will be 'resources.dll'.
#
# This is a resource only dll, so it needs no entry point.
resource_dll = Interpreter("py2exe.resources",
                           ["source/dll.c"],
                           target_desc = "shared_library",
                           extra_link_args=["/NOENTRY"],
                           )

interpreters = [run, run_w, resource_dll,
                run_ctypes_dll]

if __name__ == "__main__":
    import py2exe
    setup(name="py2exe",
          version=py2exe.__version__,
          description="Build standalone executables for Windows (python 3 version)",
          long_description=open("README.rst").read(),
          author="Thomas Heller",
          author_email="theller@ctypes.org",
    ##      maintainer="Jimmy Retzlaff",
    ##      maintainer_email="jimmy@retzlaff.com",
          url="http://www.py2exe.org/",
          license="MIT/X11",
          platforms="Windows",
    ##      download_url="http://sourceforge.net/project/showfiles.php?group_id=15583",

          classifiers=[
              "Development Status :: 4 - Beta",
              "Environment :: Console",
              "Environment :: Win32 (MS Windows)",
              "Operating System :: Microsoft :: Windows",
              "Programming Language :: C",
              "Programming Language :: Python :: 3",
              "Programming Language :: Python :: 3.2",
              "Programming Language :: Python :: 3.3",
              "Programming Language :: Python :: Implementation :: CPython",
              "Topic :: Software Development",
              "Topic :: Software Development :: Libraries",
              "Topic :: Software Development :: Libraries :: Python Modules",
              "Topic :: System :: Software Distribution",
              "Topic :: Utilities",
              ],

          distclass = Dist,
          cmdclass = {'build_interpreters': BuildInterpreters},
##          scripts = ["build_exe.py"],
          entry_points = {
              'console_scripts': ['build_exe = py2exe.build_exe:main'],
              },
          interpreters = interpreters,
          py_modules=['zipextimporter'],
          packages=['py2exe'],
          zip_safe=True, # pip does unpack anyway, only .egg uses this.
          )

# Local Variables:
# compile-command: "py -3.3 setup.py bdist_egg"
# End:

# c:\python33-64\lib\site-packages
# c:\python33-64\scripts
