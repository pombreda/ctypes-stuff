# This file imports the _memimporter.pyd extension from the distutils
# build directory.

def __load():
    import imp, os, sys, struct
    if struct.calcsize("P") == 8:
        dirname = "build\\lib.win-amd64-2.7"
    else:
        dirname = "build\\lib.win32-2.7"
    path = os.path.abspath(os.path.join(dirname, '_memimporter.pyd'))
    imp.load_dynamic("_memimporter", path)

__load()
del __load
