#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
from __future__ import division, with_statement, absolute_import, print_function

from mf4 import ModuleFinder

import errno
import imp
import os
import shutil
import string
import sys
import textwrap
import unittest

def create_file(path):
    dirname = os.path.dirname(path)
    try:
        os.makedirs(dirname)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    return open(path, "w")

def create_package(source, test_dir):
    source = textwrap.dedent(source)
    modules = set()

    ofi = None
    try:
        for line in source.splitlines():
            if not line:
                continue
            if line.startswith((" ", "\t")):
                ofi.write(line.strip() + "\n")
            else:
                if ofi:
                    ofi.close()
                fnm = line.strip()
                ofi = create_file(os.path.join(test_dir, fnm))
                modname = os.path.splitext(fnm)[0].replace("/", ".")
                if modname.endswith(".__init__"):
                    modname = modname.rpartition(".__init__")[0]
                modules.add(modname)
##                print(modname)
    finally:
        if ofi:
            ofi.close()
    return modules

class _TestPackageBase(unittest.TestCase):
    def setUp(self):
        create_package(self.data, "foo")
        self.sys_path = sys.path[:]
        sys.path.insert(0, "foo")

    def tearDown(self):
        shutil.rmtree("foo")
        sys.path = self.sys_path

##     data = """
##     package/__init__.py
##     package/sub1/__init__.py
##             from ..sub2.modZ import eggs
##             from ..modA import foo
##     package/sub1/modX.py
##             from .modY import spam
##             from .modY import spam as ham
##             from . import modY
##             from ..sub1 import modY
##     package/sub1/modY.py
##             spam = "spam"
##             # from ...package import bar
##             # from ...sys import path
##     package/sub2/__init__.py
##     package/sub2/modZ.py
##         eggs = "eggs"
##     """
##     create_package(data, test_dir)
##     shutil.rmtree(test_dir)

class Test_NamesImport(_TestPackageBase):
    data = """
    testmods/test_tools.py
            from testmods.tools import bar
            from testmods.tools import baz
            from testmods.tools import spam
            from testmods.tools import foo
            try: from testmods.tools import spam_and_eggs
            except ImportError: pass

    testmods/__init__.py
            # empty

    testmods/tools/spamfoo.py
            spam = 'spam'
            foo = 'foo'

    testmods/tools/bazbar.py
            baz = 'baz'
            bar = 'bar'

    testmods/tools/__init__.py
            from .bazbar import *
            from .spamfoo import spam
            from .spamfoo import foo
    """

    modules = {"testmods",
               "testmods.test_tools",
               "testmods.tools",
               "testmods.tools.bazbar",
               "testmods.tools.spamfoo"}

    missing = {"testmods.tools.spam_and_eggs"}

    def test_imports(self):
        for name in self.modules:
            self.assertNotIn(name, sys.modules)

        import testmods.test_tools
        with self.assertRaises(ImportError):
            import testmods.tools.spam_and_eggs
        for name in self.modules:
            self.assertIn(name, sys.modules)

        for name in self.modules:
            del sys.modules[name]

        for name in self.modules:
            self.assertNotIn(name, sys.modules)

    def test_modulefinder(self):
        mf = ModuleFinder(path=sys.path)
        mf.import_hook("testmods.test_tools")
        found = mf.modules.keys()
        self.assertEqual(set(found), self.modules)
        self.assertEqual(mf.missing(), self.missing)


class Test_PEP328(_TestPackageBase):
    data = """
    package/__init__.py
    package/sub1/__init__.py
            from ..sub2.modZ import eggs
            from ..modA import foo
    package/sub1/modX.py
            from .modY import spam
            from .modY import spam as ham
            from . import modY
            from ..sub1 import modY
    package/sub1/modY.py
            spam = "spam"
            # from ...package import bar
            # from ...sys import path
    package/sub2/__init__.py
    package/sub2/modZ.py
        eggs = "eggs"
    """


class SimpleTests(unittest.TestCase):
    """Simple import tests on the Python standard library. """

    def test_os_path(self):
        from os import path
        import os.path

        mf = ModuleFinder()
        mf.import_hook("os", None, ["path"])
        self.assertIn("os", mf.modules)
        self.assertIn("ntpath", mf.modules)
        self.assertNotIn("os.path", mf.missing())

    def test_collections_abc(self):
        from collections import abc
        import collections.abc
        from collections import namedtuple
        with self.assertRaises(ImportError):
            import collections.namedtuple

        mf = ModuleFinder()
        mf.import_hook("collections.abc")
        mf.import_hook("collections", None, ["namedtuple"])

        self.assertIn("collections.abc", mf.modules)
        self.assertNotIn("collections.namedtuple", mf.missing())

        mf = ModuleFinder()
        mf.import_hook("collections", None, ["abc"])

        self.assertIn("collections.abc", mf.modules)
        self.assertNotIn("collections.namedtuple", mf.missing())

    def test_encodings(self):
        from encodings import big5
        # /python33-64/lib/encodings
        mf = ModuleFinder()
        mf.import_hook("encodings", None, ["big5"])
        mf.import_hook("encodings", None, ["codecs"])
        mf.safe_import_hook("encodings", None, ["foo"])
        self.assertIn("encodings.big5", mf.modules)
        self.assertEqual({"encodings.foo"}, mf.missing())

if __name__ == "__main__":
    unittest.main()
