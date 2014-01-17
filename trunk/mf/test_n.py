#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""test script for py2exe
"""
from __future__ import division, with_statement, absolute_import, print_function

# XXX Because of pyreadline, this script must be executed with 'python -S'
# XXX convert to unittest
# XXX let pyside do something
# XXX Can pyside and tkinter progs use callLater to close after a short time?
# XXX import and use py2exe.runtime instead of starting processes

# XXX numpy must use bundle_files > 0
# XXX PySide must use bundle_files > 2 (?)
# XXX tkinter (also matp) must use bundle_files > 1 (?)
# XXX Try to build matp with '-x tkinter'

import os
import shutil

def main():
##    for py in ("py -3.3", "py -3.4"):
    py = "py -3.3"
    for bundle in (3, 2, 1, 0):
        for libfile in ("foo.dll", r"lib\foo.dll"):
            for script in ("nump.py", "matp.py", "sql.py", "pys.py", "tki.py"):
                if os.path.isdir("dist_testing"):
                    shutil.rmtree("dist_testing")
                cmd = r"{py} -m py2exe {script} -b{bundle} -l {libfile} -d dist_testing 2> NUL >NUL".format(**locals())
    ##            print("building %r... " % cmd, end="")
                print("Testing %s with '%s -b%d -l %s'." % (script, py, bundle, libfile), end="")
                r = os.system(cmd)
                if r:
                    print("FAILED to build!")
                    continue
                print(".", end="")
                r = os.system(r"dist_testing\%s.exe" % script.split(".")[0])
                print(" Result: %d" % r)
                ## os.system("dir /b/s dist_testing")
                ## print()


if __name__ == "__main__":
    main()
