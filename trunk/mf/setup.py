#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
import os
import sys

##from setuptools import setup, find_packages
from distutils.core import setup

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
              ("PYTHONCOM", '\\"pythoncom%d%d_d.dll\\"' % sys.version_info[:2]),
              ("_CRT_SECURE_NO_WARNINGS", '1')]
else:
    macros = [("PYTHONDLL", '\\"python%d%d.dll\\"' % sys.version_info[:2]),
              ("PYTHONCOM", '\\"pythoncom%d%d.dll\\"' % sys.version_info[:2]),
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

run = Interpreter("py2exe.run",
                  ["source/start.c",
                   ## "source/run.c",
                   "source/icon.rc",

                   "source/MemoryModule.c",
                   "source/MyLoadLibrary.c",
                   "source/_memimporter.c",
                   "source/actctx.c",

                   "source/python-dynload.c",
                   ],
                  libraries=["user32"],
                  define_macros=macros,
                  extra_compile_args=extra_compile_args,
                  extra_link_args=extra_link_args,
                  )

interpreters = [run] #, run_dll]

if __name__ == "__main__":
    setup(name="py2exe",
          version="0.9.0",
          description="Build standalone executables for Windows (python 3 version)",
          long_description=__doc__,
          author="Thomas Heller",
          author_email="theller@ctypes.org",
    ##      maintainer="Jimmy Retzlaff",
    ##      maintainer_email="jimmy@retzlaff.com",
          url="http://www.py2exe.org/",
          license="MIT/X11",
          platforms="Windows",
    ##      download_url="http://sourceforge.net/project/showfiles.php?group_id=15583",
    ##      classifiers=["Development Status :: 5 - Production/Stable"],
          distclass = Dist,
          cmdclass = {'build_interpreters': BuildInterpreters},
##          scripts = ["build_setup.py"],
          interpreters = interpreters,
          py_modules=['zipextimporter'],
          packages=['py2exe'],
          )

# Local Variables:
# compile-command: "py -3.3 setup.py bdist_egg"
# End:
