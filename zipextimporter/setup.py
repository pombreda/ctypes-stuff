#import sys, os, string
from distutils.core import setup, Extension

_memimporter = Extension("_memimporter",
                         ["source/MemoryModule.c",
                          "source/_memimporter.c",
                          "source/actctx.c"],
                         )
setup(name="zipextimporter",
      description="import extension modules from zipfiles without unpacking them",
      version="0.2",
      author="Thomas Heller",
      author_email="theller@ctypes.org",
      license="MIT/X11, MPL 2.0",
      platforms="Windows",
      ext_modules = [_memimporter],
      py_modules = ["zipextimporter"],
      )

# Local Variables:
# compile-command: "setup.py install"
# End:
