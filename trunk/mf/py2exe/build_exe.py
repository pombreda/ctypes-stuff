#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
import argparse
import logging
import os
from . import runtime

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build runtime archive for a script")

    # what to include, what to exclude...
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

    # how to compile the code...
    parser.add_argument("-O", "--optimize",
                        help="use optimized bytecode",
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
                        help="""print where the module <modname> is imported.""",
                        metavar="modname",
                        dest="show_from",
                        action="append")

    parser.add_argument("-v",
                        dest="verbose",
                        action="store_true")

    parser.add_argument("-c", "--compress",
                        dest="compress",
                        action="store_true")

    # exe files to build...
    parser.add_argument("script",
                        metavar="script",
                        nargs="+",
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
                        XXX more
                        pyd files are extracted on demand to a
                        temporary directory, this directory is removed
                        after the program has finished.""",
                        choices=[0, 1, 2, 3],
                        type=int,
                        default=3)

    parser.add_argument("-W", "--write-setup-script",
                        help="""Instead of building the executables write a setup script
                        that allows further customizations of the build process.""",
                        metavar="setup_path",
                        dest="setup_path")

    options = parser.parse_args()

    options.script = runtime.fixup_targets(options.script, "script")
    for script in options.script:
        if script.script.endswith(".pyw"):
            script.exe_type = "windows_exe"
        else:
            script.exe_type = "console_exe"
    
    if options.setup_path:
        if os.path.isfile(options.setup_path):
            message = "File %r already exists, are you sure you want to overwrite it? [yN]: "
            answer = input(message % options.setup_path)
            if answer not in "yY":
                print("Canceled.")
                return
        from .setup_template import write_setup
        write_setup(options)
        # no further action
        return

    level = logging.INFO if options.verbose else logging.WARNING
    logging.basicConfig(level=level)

    builder = runtime.Runtime(options)
    builder.analyze()
    builder.build()

if __name__ == "__main__":
    main()
