#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
import argparse
import logging
import os
import runtime

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build runtime archive for a script")

    parser.add_argument("-i", "--include",
                        help="module to include",
                        dest="includes",
                        metavar="modname",
                        action="append"
                        )
    parser.add_argument("-x", "--exclude",
                        help="module to exclude",
                        dest="excludes",
                        metavar="modname",
                        action="append")
    parser.add_argument("-p", "--package",
                        help="module to exclude",
                        dest="packages",
                        metavar="package_name",
                        action="append")

    # how to scan...
    parser.add_argument("-O", "--optimize",
                        help="scan optimized bytecode",
                        dest="optimize",
                        action="count")

    # reporting options...
    parser.add_argument("-s", "--summary",
                        help="""print a single line listing how many modules were
                        found and how many modules are missing""",
                        dest="summary",
                        action="store_true")
    parser.add_argument("-r", "--report",
                        help="""print a detailed report listing all found modules,
                        the missing modules, and which module imported them.""",
                        dest="report",
                        action="store_true")
    parser.add_argument("-f", "--from",
                        help="""print a detailed report listing all found modules,
                        the missing modules, and which module imported them.""",
                        metavar="modname",
                        dest="show_from",
                        action="append")

    parser.add_argument("-v",
                        dest="verbose",
                        action="store_true")

    parser.add_argument("script",
                        metavar="script",
##                        nargs="+",
                        )

    # what to build
    parser.add_argument("-d", "--dest",
##                        required=True,
                        default="dist",
                        help="""destination directory""",
                        dest="destdir")

    parser.add_argument("-l", "--library",
                        help="""relative pathname of the python archive""",
                        dest="libname")

    parser.add_argument("-b", "--bundle-files",
                        help="""How to bundle the files. 3 - create an .exe, a zip-archive, and .pyd
                        files in the file system.  2 - create .exe and
                        a zip-archive that contains the pyd files.
                        pyd files are extracted on demand to a
                        temporary directory, this directory is removed
                        after the program has finished.""",
                        choices=[1, 2, 3],
                        type=int,
                        default=3)

    options = parser.parse_args()

    level = logging.INFO if options.verbose else logging.WARNING
    logging.basicConfig(level=level)

    if not os.path.exists(options.destdir):
        os.mkdir(options.destdir)
    destdir = options.destdir

    # basename of the exe to create
    dest_base = os.path.splitext(os.path.basename(options.script))[0]

    # full path to exe-file
    exe_path = os.path.join(destdir, dest_base + ".exe")

    # XXX move to builder...
    if os.path.isfile(exe_path):
        os.remove(exe_path)

    # 'libname' is the path of the runtime library RELATIVE to the runner directory.
    # XXX move to builder...
    if options.libname:
        libpath = os.path.join(destdir, options.libname)
        if os.path.isfile(libpath):
            os.remove(libpath)

        if not os.path.exists(os.path.dirname(libpath)):
            os.mkdir(os.path.dirname(libpath))

    builder = runtime.Runtime(options)
    builder.analyze()
    builder.build_exe(exe_path, options.libname)
    builder.build(exe_path, options.libname)

if __name__ == "__main__":
    main()
