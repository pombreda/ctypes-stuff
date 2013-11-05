# This file imports the _memimporter.pyd extension from the distutils
# build directory.

def __load():
    import imp, os, sys, struct
    if hasattr(sys, "gettotalrefcount"):
        suffix = "-pydebug"
        pyd = "_d.pyd"
    else:
        suffix = ""
        pyd = ".pyd"
    if struct.calcsize("P") == 8:
        dirname = "build\\lib.win-amd64-%d.%d%s" % (sys.version_info[0], sys.version_info[1], suffix)
    else:
        dirname = "build\\lib.win32-%d.%d%s" % (sys.version_info[0], sys.version_info[1], suffix)
    path = os.path.abspath(os.path.join(dirname, '_memimporter' + pyd))
    imp.load_dynamic("_memimporter", path)

__load()
del __load
