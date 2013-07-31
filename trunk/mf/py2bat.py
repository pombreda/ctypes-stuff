#!/usr/bin/python3.3-32
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
                        )

    # what to build
    parser.add_argument("-d", "--dest",
                        help="""destination directory""",
                        dest="destdir")

    options = parser.parse_args()

    level = logging.INFO if options.verbose else logging.WARNING
    logging.basicConfig(level=level)


    basename = os.path.basename(options.script)

    runner = os.path.splitext(basename)[0] + ".bat"
    libname = "_" + os.path.splitext(basename)[0] + ".exe"

    builder = runtime.Runtime(options)

    builder.build_bat(runner, libname)

    builder.analyze()
    builder.build(libname)

if __name__ == "__main__":
    main()
