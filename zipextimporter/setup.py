from distutils.core import setup, Extension

extra_link_args = []
extra_compile_args = []

if 0:
    # enable this to include debug info into a release build
    extra_compile_args.append("/Z7")
    extra_link_args.append("/DEBUG")

_memimporter = Extension("_memimporter",
                         ["source/MemoryModule.c",
                          "source/MyLoadLibrary.c",
                          "source/_memimporter.c",
                          "source/actctx.c"],
                         define_macros=[("STANDALONE", "1"),
##                                        ("VERBOSE", "1"),
                                        ("_CRT_SECURE_NO_WARNINGS", "1")],
                         extra_compile_args=extra_compile_args,
                         extra_link_args=extra_link_args,
                         )

setup(name="zipextimporter",
      description="import extension modules from zipfiles without unpacking them to disk",
      version="0.3",
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
