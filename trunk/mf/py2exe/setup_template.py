#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import string

HEADER = """\
#!/usr/bin/python3
# -*- coding: utf-8 -*-

from distutils.core import setup
import py2exe

class Target(object):
    '''Target is the baseclass for all executables that are created.
    It defines properties that are shared by all of them.
    '''
    def __init__(self, **kw):
        self.__dict__.update(kw)

        # the VersionInfo resource, uncomment and fill in those items
        # that make sense:
        
        # self.company_name = "Company Name"
        # self.copyright = "Copyright Company Name © 2013"
        # self.legal_copyright = "Copyright Company Name © 2013"
        # self.legal_trademark = ""
        # self.product_version = "1.0.0.0"
        # self.product_name = "Product Name"

        # self.private_build = "foo"
        # self.special_build = "bar"

    def copy(self):
        return Target(**self.__dict__)

    def __setitem__(self, name, value):
        self.__dict__[name] = value

"""

TARGET = """
$myapp = Target(
    # We can extend or override the VersionInfo of the base class
    # self.version = "1.0.0.0"
    # self.file_description = "File Description"
    # self.comments = "Some Comments"
    # self.internal_name = "spam"

    script="$script", # path of the main script

    # Allows to specify the basename of the executable, if different from '$myapp'
    # dest_base = "$myapp",

    # Icon resources:[(resource_id, path to .ico file), ...]
    # icon_resources=[(1, r"icon1.ico")]

    # other_resources = [(RT_MANIFEST, 1, manifest_template % dict(prog="smedit", level="asInvoker")),
    #                    (RT_BITMAP, 1, open("bitmap.bmp).read()[14:])]),
    )
"""

OPTIONS = """
# ``zipfile`` and ``bundle_files`` options explained:
# ===================================================
#
# zipfile is the Python runtime library for your exe/dll-files; it
# contains in a ziparchive the modules needed as compiled bytecode.
#
# If 'zipfile=None' is used, the runtime library is appended to the
# exe/dll-files (which will then grow quite large), otherwise the
# zipfile option should be set to a pathname relative to the exe/dll
# files, and a library-file shared by all executables will be created.
#
# The py2exe runtime *can* use extension module by directly importing
# the from a zip-archive - without the need to unpack them to the file
# system.  The bundle_files option specifies where the extension modules,
# the python dll itself, and other needed dlls are put.
#
# bundle_files == 3:
#     Extension modules, the Python dll and other needed dlls are
#     copied into the directory where the zipfile or the exe/dll files
#     are created, and loaded in the normal way.
#
# bundle_files == 2:
#     Extension modules are put into the library ziparchive and loaded
#     from it directly.
#     The Python dll and any other needed dlls are copied into the
#     directory where the zipfile or the exe/dll files are created,
#     and loaded in the normal way.
#
# bundle_files == 1:
#     Extension modules, the Python dll, and other needed dlls are put
#     into the zipfile or the exe/dll files, and everything is loaded
#     without unpacking to the file system.  This does not work for
#     some dlls, so use with caution.


py2exe_options = dict(
    packages = [$packages],
##    excludes = "tof_specials Tkinter".split(),
##    ignores = "dotblas gnosis.xml.pickle.parsers._cexpat mx.DateTime".split(),
##    dll_excludes = "MSVCP90.dll mswsock.dll powrprof.dll".split(),
    optimize=$optimize,
    compressed=$compressed, # uncompressed may or may not have a faster startup
    bundle_files=$bundle_files,
    dist_dir=$destdir,
    )
"""

SETUP = """
# Some options can be overridden by command line options...

setup(name="name",
      # console based executables
      console=[$console],

      # windows subsystem executables (no console)
      windows=[$windows],

      # py2exe options
      zipfile=$zipfile,
      options={"py2exe": py2exe_options},
      )
"""

def write_setup(args):
    from string import Template
    import sys
    print(sys.argv[1:])
    with open(args.setup_path, "w", encoding="utf-8") as ofi:

        header = Template(HEADER)
        print(header.substitute(locals()), file=ofi)
        console = []
        for script in args.script:
            myapp = os.path.splitext(script)[0]
            target = Template(TARGET)
            print(target.substitute(locals()), file=ofi)
            console.append(myapp)

        console = ", ".join(console)
        windows = ""
        optimize = args.optimize or 0
        compressed = args.compress or False
        destdir = repr(args.destdir)
        zipfile = repr(args.libname)

        packages = ", ".join(args.packages or [])
        bundle_files = args.bundle_files
        options = Template(OPTIONS)
        print(options.substitute(locals()), file=ofi)

        setup = Template(SETUP)
        print(setup.substitute(locals()), file=ofi)

    print("Created %s." % args.setup_path)
