from distutils.core import setup, Extension

_array_struct = Extension("_array_struct",
                         sources = ["_array_struct.c"])

setup(name="_array_struct",
      ext_modules = [_array_struct])
