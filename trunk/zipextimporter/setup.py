try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

extra_link_args = []
extra_compile_args = []

if 0:
    # enable this to include debug info into a release build
    extra_compile_args.append("/Z7")
    extra_link_args.append("/DEBUG")

_py2exeimporter = Extension("_py2exeimporter",
                            ["source/MemoryModule.c",
                             "source/MyLoadLibrary.c",
                             "source/_memimporter.c",
                             "source/actctx.c"],
                            depends=["source/MemoryModule.h",
                                     "source/MyLoadLibrary.h",
                                     "source/actctx.h"],
                            define_macros=[("_CRT_SECURE_NO_WARNINGS", "1")],
                            extra_compile_args=extra_compile_args,
                            extra_link_args=extra_link_args,
                            )

setup(name="py2exeimporter",
      long_description=open("README.txt").read(),
      description="import extension modules from zipfiles without unpacking them to disk",
      url="http://code.google.com/p/ctypes-stuff/source/browse/#svn%2Ftrunk%2Fzipextimporter",
      version="0.3",
      author="Thomas Heller",
      author_email="theller@ctypes.org",
      license="MIT/X11, MPL 2.0",
      platforms="Windows",
      ext_modules = [_py2exeimporter],
      py_modules = ["py2exeimporter"],

      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: Console",
          "Environment :: Win32 (MS Windows)",
          "Operating System :: Microsoft :: Windows",
          "Programming Language :: C",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.3",
##          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: Implementation :: CPython",
          "Topic :: Software Development",
          "Topic :: Software Development :: Libraries",
          "Topic :: Software Development :: Libraries :: Python Modules",
          ],

      )

# Local Variables:
# compile-command: "setup.py install"
# End:
