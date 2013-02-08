#!/usr/bin/python3.3
import unittest

from mf import ModuleFinder

class MFTest(unittest.TestCase):

    # c:/python33/lib/collections/
    def test_collections(self):
        """
        collections contains namedtuple, ChainMap, OrderedDict
        global names, which are imported from string, inspect,
        and others.
        """
        
        mf = ModuleFinder()
        mf.import_hook("collections")
        modules = set([name for name in mf.modules
                       if name.startswith("collections")])
        self.assertEqual({"collections", "collections.abc"},
                         modules)
        missed = [name for name in mf.missing()
                  if name.startswith("collections")]
        self.assertEqual([], missed)

    def test_pep328(self):
        """
        The package structure from pep328.
        """

        mf = ModuleFinder()
        mf.import_hook("pep328.subpackage1")
        self.assertEqual(set(mf.modules.keys()),
                         {"pep328",
                          "pep328.moduleA",
                          "pep328.subpackage1",
                          "pep328.subpackage1.moduleX",
                          "pep328.subpackage1.moduleY",
                          "pep328.subpackage2",
                          "pep328.subpackage2.moduleZ",
                          })
        self.assertEqual(mf.missing(), [])

if __name__ == "__main__":
    unittest.main()
