#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""Modulefinder based on importlib
"""

from collections import defaultdict
import dis
import importlib
import os
import struct
import sys

# XXX Clean up once str8's cstor matches bytes.
LOAD_CONST = bytes([dis.opname.index('LOAD_CONST')])
IMPORT_NAME = bytes([dis.opname.index('IMPORT_NAME')])
STORE_NAME = bytes([dis.opname.index('STORE_NAME')])
STORE_GLOBAL = bytes([dis.opname.index('STORE_GLOBAL')])
STORE_OPS = [STORE_NAME, STORE_GLOBAL]
HAVE_ARGUMENT = bytes([dis.HAVE_ARGUMENT])

################################################################
if sys.version_info[:3] == (3, 3, 0):
    def patch():
        # Work around Python bug #17098:
        # Set __loader__ on modules imported by the C level
        for name in sys.builtin_module_names + ("_frozen_importlib",):
            m = __import__(name)
            try:
                m.__loader__
            except AttributeError:
                m.__loader__ = importlib.machinery.BuiltinImporter
    patch()
    del patch
################################################################
            
# /python33/lib/importlib/_bootstrap.py

_ERR_MSG = 'No module named {!r}'

class ModuleFinder:

    # Most methods literally copied from python3.3's
    # importlib._bootstrap module, with only very few changes.

    def __init__(self):
        self.modules = {} # simulates sys.modules
        self.badmodules = defaultdict(set) # modules that have not been found


    # /python33/lib/importlib/_bootstrap.py 1455
    def _resolve_name(self, name, package, level):
        """Resolve a relative module name to an absolute one."""
        bits = package.rsplit('.', level - 1)
        if len(bits) < level:
            raise ValueError('attempted relative import beyond top-level package')
        base = bits[0]
        return '{}.{}'.format(base, name) if name else base


    # /python33/lib/importlib/_bootstrap.py 1481
    def _sanity_check(self, name, package, level):
        """Verify arguments are 'sane'."""
        if not isinstance(name, str):
            raise TypeError("module name must be str, not {}".format(type(name)))
        if level < 0:
            raise ValueError('level must be >= 0')
        if package:
            if not isinstance(package, str):
                raise TypeError("__package__ not set to a string")
            elif package not in self.modules:
                msg = ("Parent module {!r} not loaded, cannot perform relative "
                       "import")
                raise SystemError(msg.format(package))
        if not name and level == 0:
            raise ValueError("Empty module name")


    # /python33/lib/importlib/_bootstrap.py 1500
    def _find_and_load(self, name):
        """Find and load the module"""
        path = None
        parent = name.rpartition('.')[0]
        if parent:
            if parent not in self.modules:
                self._gcd_import(parent)
            # Crazy side-effects!
            if name in self.modules:
                return self.modules[name]
            # Backwards-compatibility; be nicer to skip the dict lookup.
            parent_module = self.modules[parent]
            try:
                path = parent_module.__path__
            except AttributeError:
                msg = (_ERR_MSG + '; {} is not a package').format(name, parent)
                raise ImportError(msg, name=name)
        loader = importlib.find_loader(name, path)
        if loader is None:
            exc = ImportError(_ERR_MSG.format(name), name=name)
            # TODO(brett): switch to a proper ModuleNotFound exception in Python
            # 3.4.
            exc._not_found = True
            raise exc
        elif name not in self.modules:
            # The parent import may have already imported this module.
            self._load_module(loader, name)
##            _verbose_message('import {!r} # {!r}', name, loader)
        # Backwards-compatibility; be nicer to skip the dict lookup.
        module = self.modules[name]

        # TODO(theller): Move all this into _load_module!
        if parent:
            # Set the module as an attribute on its parent.
            parent_module = self.modules[parent]
            setattr(parent_module, name.rpartition('.')[2], module)
        # Set __package__ if the loader did not.
        if getattr(module, '__package__', None) is None:
            try:
                module.__package__ = module.__name__
                if not hasattr(module, '__path__'):
                    module.__package__ = module.__package__.rpartition('.')[0]
            except AttributeError:
                pass
        # Set loader if need be.
        if not hasattr(module, '__loader__'):
            try:
                module.__loader__ = loader
            except AttributeError:
                pass

        # It is important that all the required __...__ attributes at
        # the module are set before the code is scanned.
        if module.__code__:
            self._scan_code(module.__code__, module)

        return module


    # /python33/lib/importlib/_bootstrap.py 1563
    def _gcd_import(self, name, package=None, level=0):
        """Import and return the module based on its name, the package the call is
        being made from, and the level adjustment.

        This function represents the greatest common denominator of functionality
        between import_module and __import__. This includes setting __package__ if
        the loader did not.

        """
        self._sanity_check(name, package, level)
        if level > 0:
            name = self._resolve_name(name, package, level)
        if name in self.badmodules:
            raise ImportError(_ERR_MSG.format(name), name=name)
        if name not in self.modules:
            return self._find_and_load(name)
        module = self.modules[name]
        if module is None:
            message = ("import of {} halted; "
                        "None in sys.modules".format(name))
            raise ImportError(message, name=name)
        return module


    # /python33/lib/importlib/_bootstrap.py 1587
    def _handle_fromlist(self, module, fromlist):
        """Figure out what __import__ should return.

        """
        # The hell that is fromlist ...
        # If a package was imported, try to import stuff from fromlist.
        if hasattr(module, '__path__'):
            if '*' in fromlist:
                fromlist = list(fromlist)
                fromlist.remove('*')
                if hasattr(module, '__all__'):
                    fromlist.extend(module.__all__)
            for x in fromlist:
                if not hasattr(module, x):
                    try:
                        self._gcd_import('{}.{}'.format(module.__name__, x))
                    except ImportError as exc:
                        # Backwards-compatibility dictates we ignore failed
                        # imports triggered by fromlist for modules that don't
                        # exist.
                        # TODO(brett): In Python 3.4, have import raise
                        #   ModuleNotFound and catch that.
                        if hasattr(exc, '_not_found') and exc._not_found:
                            pass
                        else:
                            raise
        # XXX Should be extended to import names???  globalnames???
        return module


    # /python33/lib/importlib/_bootstrap.py 1621
    def _calc___package__(self, caller):
        """Calculate what __package__ should be.

        __package__ is not guaranteed to be defined or could be set to None
        to represent that its proper value is unknown.

        """
        package = caller.__package__
        if package is None:
            package = caller.__name__
            if not hasattr(caller, "__path__"):
                package = package.rpartition('.')[0]
        return package


    # /python33/lib/importlib/_bootstrap.py 1647
    def import_hook(self, name, caller=None, fromlist=(), level=0):
        """Import a module.

        The 'caller' argument is used to infer where the import is
        occuring from to handle relative imports. The 'fromlist'
        argument specifies what should exist as attributes on the
        module being imported (e.g. ``from module import
        <fromlist>``).  The 'level' argument represents the package
        location to import from in a relative import (e.g. ``from
        ..pkg import mod`` would have a 'level' of 2).

        """
        if level == 0:
            module = self._gcd_import(name)
        else:
            package = self._calc___package__(caller)
            module = self._gcd_import(name, package, level)
        if not fromlist:
            # Return up to the first dot in 'name'. This is complicated by the fact
            # that 'name' may be relative.
            if level == 0:
                return self._gcd_import(name.partition('.')[0])
            elif not name:
                return module
            else:
                cut_off = len(name) - len(name.partition('.')[0])
                return self.modules[module.__name__[:len(module.__name__)-cut_off]]
        else:
            return self._handle_fromlist(module, fromlist)

    ################################################################
    def safe_import_hook(self, name, caller=None, fromlist=(), level=0):

        ## if level == 0:
        ##     if fromlist:
        ##         print("%sfrom %s import %s" % (self.indent, name, ", ".join(fromlist)))
        ##     else:
        ##         print("%simport %s" % (self.indent, name))
        ## elif name:
        ##     print("%sfrom %s import %s" % (self.indent, "."*level + name, ", ".join(fromlist)))
        ## else:
        ##     print("%sfrom %s import %s" % (self.indent, "."*level, ", ".join(fromlist)))

##        self.pr(name, caller, fromlist, level)
##        self.indent += " "
        try:
            res = self.import_hook(name, caller, fromlist, level)
        except ImportError as exc:
            ## print("%s=>" % self.indent, None)
            self.pr(name, caller, fromlist, level)
            if level:
                name = self._resolve_name(name, caller.__name__, level)
            print("BAD", exc)
            print()
            self.badmodules[name].add(caller.__name__)
            res = None

##        self.indent = self.indent[:-1]
        ## print("%s=>" % self.indent, res)

    indent = ""
    def pr(self, name, caller, fromlist, level):
        print("caller", caller.__name__)
        if level == 0:
            if fromlist:
                print("%sfrom %s import %s" % (self.indent, name, ", ".join(fromlist)))
            else:
                print("%simport %s" % (self.indent, name))
        elif name:
            print("%sfrom %s import %s" % (self.indent, "."*level + name, ", ".join(fromlist)))
        else:
            print("%sfrom %s import %s" % (self.indent, "."*level, ", ".join(fromlist)))

    def _load_module(self, loader, name):
        """Simulate loader.load_module(name).

        If the requested module already exists in sys.modules, that
        module should be used and returned.  Otherwise the loader
        should create a new module and insert it into sys.modules
        before any loading begins, to prevent recursion from the
        import. If the loader inserted a module and the load fails, it
        must be removed by the loader from sys.modules; modules
        already in sys.modules before the loader began execution
        should be left alone. The importlib.util.module_for_loader()
        decorator handles all of these details.

        The loader should set several attributes on the module:

        __name__ The name of the module.

        __file__ The path to where the module data is stored (not set
        for built-in modules).

        __path__ A list of strings specifying the search path within a
        package. This attribute is not set on modules.

        __package__ The parent package for the module/package. If the
        module is top-level then it has a value of the empty
        string. The importlib.util.set_package() decorator can handle
        the details for __package__.

        __loader__ The loader used to load the module. (This is not
        set by the built-in import machinery, but it should be set
        whenever a loader is used.)

        """
        if name in self.modules:
            return self.modules[name]

        # __package__ is set elsewhere!

        # See importlib.abc.Loader
        self.modules[name] = Module(loader, name)

    def _scan_code(self, code, mod):
        for what, args in self._scan_opcodes(code):
            if what == "store":
                name, = args
                mod.__globalnames__.add(name)
            elif what == "import":
                level, fromlist, name = args
                self.safe_import_hook(name, mod, fromlist, level)
            else:
                # We don't expect anything else from the generator.
                raise RuntimeError(what)

        for c in code.co_consts:
            if isinstance(c, type(code)):
                self._scan_code(c, mod)

    def _scan_opcodes(self, co, unpack=struct.unpack):
        """
        Scan the code object, and yield 'interesting' opcode combinations

        """
        code = co.co_code
        names = co.co_names
        consts = co.co_consts
        LOAD_LOAD_AND_IMPORT = LOAD_CONST + LOAD_CONST + IMPORT_NAME
        while code:
            c = bytes([code[0]])
            if c in STORE_OPS:
                oparg, = unpack('<H', code[1:3])
                yield "store", (names[oparg],)
                code = code[3:]
                continue
            if code[:9:3] == LOAD_LOAD_AND_IMPORT:
                oparg_1, oparg_2, oparg_3 = unpack('<xHxHxH', code[:9])
                yield "import", (consts[oparg_1], consts[oparg_2], names[oparg_3])
                code = code[9:]
                continue
            if c >= HAVE_ARGUMENT:
                code = code[3:]
            else:
                code = code[1:]


    def report(self):
        """Print a report to stdout, listing the found modules with
        their paths, as well as modules that are missing, or seem to
        be missing.

        """

    def report_missing(self):
        """Print a report to stdout, listing those modules that are
        missing.

        """
        print()
        for name in sorted(self.badmodules):
            parent, _, symbol = name.rpartition(".")
            if parent and parent in self.modules:
                if symbol in self.modules[parent].__globalnames__:
                    print(name, "->", parent)
                    continue
            else:
                mods = sorted(self.badmodules[name])
                print("? %-35s imported by %s" % (name, ', '.join(mods)))
                

##         print(self.badmodules)
##         missing = self.badmodules
##         if missing:
##             print()
##             print("Missing modules:")
##             for name in missing:
## ##                mods = sorted(self.badmodules[name].keys())
##                 print("?", name)#, "imported from", ', '.join(mods))

    def report_modules(self):
        """Print a report about found modules to stdout, with their
        found paths.
        """
        print()
        print("  %-35s %s" % ("Name", "File"))
        print("  %-35s %s" % ("----", "----"))
        # Print modules found
        keys = sorted(self.modules.keys())
        for key in keys:
            m = self.modules[key]
            if getattr(m, "__path__", None):
                print("P", end=" ")
            else:
                print("m", end=" ")
            print("%-35s" % key, getattr(m, "__file__", ""))

################################################################

class Module:
    def __init__(self, loader, name):
        self.__globalnames__ = set()

        self.__name__ = name

        if hasattr(loader, "get_filename"):
            fnm = loader.get_filename(name)
            self.__file__ = fnm
            if loader.is_package(name):
                self.__path__ = [os.path.dirname(fnm)]
        elif hasattr(loader, "path"):
            fnm = loader.path
            self.__file__ = fnm
            if loader.is_package(name):
                self.__path__ = [os.path.dirname(fnm)]
        else:
            # frozen or builtin modules
            if loader.is_package(name):
                self.__path__ = [name]

        # self.__package__ is set elsewhere
        self.__loader__ = loader
        self.__code__ = loader.get_code(name)

    def __repr__(self):
        s = "Module(%s" % self.__name__
        if getattr(self, "__file__", None) is not None:
            s = s + ", %r" % (self.__file__,)
        if getattr(self, "__path__", None) is not None:
            s = s + ", %r" % (self.__path__,)
        return s + ")"

################################################################

if __name__ == "__main__":

    sys.path.insert(0, ".")
    mf = ModuleFinder()
    for name in sys.argv[1:]:
        mf.import_hook(name)
##    mf.import_hook("pep328.subpackage1")
##    mf.import_hook("collections.abc")
    mf.report_modules()
    mf.report_missing()
