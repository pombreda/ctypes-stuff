#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""ModuleFinder based on importlib
"""

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

class ModuleFinder:
    def __init__(self, path=None):
        self.path = path
        self.modules = {}
        self.badmodules = set()

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
        if fromlist:
            symbols = self._handle_fromlist(module, fromlist, caller)


    # for now:
    def safe_import_hook(self, name, caller=None, fromlist=(), level=0):
        """Wrapper for import_hook() that catches ImportError.

        """
        try:
            self.import_hook(name, caller, fromlist, level)
        except ImportError as exc:
##            import traceback; traceback.print_exc(0)
            pass

    # /python33-64/lib/collections
    def _handle_fromlist(self, mod, fromlist, caller):
        """handele the fromlist.

        Names on the fromlist can be modules or global symbols.
        """

        for name in fromlist:
            if name == "*":
                continue
            if name in mod.__globalnames__:
                continue
            ## if mod.__name__ == "collections":
            ##     print("FROMLIST", mod.__name__, name, caller)
            ##     print("   ", sorted(mod.__globalnames__))
        ## if mod.__name__.startswith("collections"):
        ##     print("HANDLE_FROMLIST", mod.__name__, fromlist)
        ##     print("   ", sorted(mod.__globalnames__))
        ## return fromlist


    # /python33/lib/importlib/_bootstrap.py 1455
    def _resolve_name(self, name, package, level):
        """Resolve a relative module name to an absolute one."""
        assert level > 0
        # This method must only be called for relative imports.
        # Probably it could return <name> when level == 0;
        # and we can save the 'if level > 0:' test in the calling code.
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


    # /python33/lib/importlib/_bootstrap.py 1563
    def _gcd_import(self, name, package=None, level=0):
        """Import and return the module based on its name, the package the call is
        being made from, and the level adjustment.

        """
        # __main__ is always the current main module; do never import that.
        if name == "__main__":
            raise ImportError()

        self._sanity_check(name, package, level)
        if level > 0:
            name = self._resolve_name(name, package, level)
        # 'name' is now the fully qualified, absolute name of the module we want to import.

        ## self.depgraph[name].add(self.__last_caller.__name__ if self.__last_caller else "-")

        ## if name in self.excludes:
        ##     raise ImportError(_ERR_MSG.format(name), name=name)
        if name in self.modules:
            return self.modules[name]
        return self._find_and_load(name)


    # /python33/lib/importlib/_bootstrap.py 1500
    def _find_and_load(self, name):
        """Find and load the module.

        Inserts the module into self.modules and returns it.
        If the module is not found or could not be imported,
        it is inserted in self.badmodules.
        """
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
                msg = ('No module named {!r}; {} is not a package').format(name, parent)
                self._add_badmodule(name)
                raise ImportError(msg, name=name)
        loader = importlib.find_loader(name, path)
        if loader is None:
            self._add_badmodule(name)
            raise ImportError(name)
        elif name not in self.modules:
            # The parent import may have already imported this module.
            try:
                self._load_module(loader, name)
            except ImportError:
                self._add_badmodule(name)
                raise

        # Backwards-compatibility; be nicer to skip the dict lookup.
        module = self.modules[name]

        if parent:
            # Set the module as an attribute on its parent.
            parent_module = self.modules[parent]
            setattr(parent_module, name.rpartition('.')[2], module)

        # It is important that all the required __...__ attributes at
        # the module are set before the code is scanned.
        if module.__code__:
            self._scan_code(module.__code__, module)

        return module

    def _add_badmodule(self, name):
        self.badmodules.add(name)

    def _load_module(self, loader, name):
        self.modules[name] = Module(loader, name)

    def _scan_code(self, code, mod):
        """
        Scan the module bytecode.

        When we encounter in import statement, we simulate the import
        by calling safe_import_hook() to find the imported modules.

        We also take note of 'static' global symbols in the module and
        add them to __globalnames__.
        """

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


    ################################

    def missing(self):
        """Return a list of modules that appear to be missing. Use
        any_missing_maybe() if you want to know which modules are
        certain to be missing, and which *may* be missing.

        """
        return self.badmodules


    def report(self):
        """Print a report to stdout, listing the found modules with
        their paths, as well as modules that are missing, or seem to
        be missing. """

        self.report_modules()
        self.report_missing()


    def report_modules(self):
        """Print a report about found modules to stdout, with their
        found paths.
        """
        print()
        print("  %-35s %s" % ("Name", "File"))
        print("  %-35s %s" % ("----", "----"))
        # Print modules found
        for name in sorted(self.modules):
            m = self.modules[name]
            if m is None:
                ## print("?", end=" ")
                continue
            elif getattr(m, "__path__", None):
                print("P", end=" ")
            else:
                print("m", end=" ")
            print("%-35s" % name, getattr(m, "__file__", ""))
            ## deps = sorted(self.depgraph[name])
            ## print("   imported from %s" % ", ".join(deps))
            ## print()


    def report_missing(self):
        """Print a report to stdout, listing those modules that are
        missing.

        """
        print()
        print("  %-35s" % "Missing Modules")
        print("  %-35s" % "---------------")
        for name in sorted(self.missing()):
##            deps = sorted(self.depgraph[name])
            deps = {"?"}
            print("? %-35s imported from %s" % (name, ", ".join(deps)))

################################################################

class Module:
    """Represents a Python module.

    These attributes are set, depending on the loader:

    __name__: The name of the module.

    __file__: The path to where the module data is stored (not set for
    built-in modules).

    __path__: A list of strings specifying the search path within a
    package. This attribute is not set on modules.

    __package__: The parent package for the module/package. If the
    module is top-level then it has a value of the empty string.

    __loader__: The loader for this module.

    __code__: the code object provided by the loader; can be None.

    __globalnames__: a set containing the global names that are defined.
    
    """

    def __init__(self, loader, name):
        self.__globalnames__ = set()

        self.__name__ = name
        self.__loader__ = loader

        if hasattr(loader, "get_filename"):
            # python modules
            fnm = loader.get_filename(name)
            self.__file__ = fnm
            if loader.is_package(name):
                self.__path__ = [os.path.dirname(fnm)]
        elif hasattr(loader, "path"):
            # extension modules
            fnm = loader.path
            self.__file__ = fnm
            if loader.is_package(name):
                self.__path__ = [os.path.dirname(fnm)]
        else:
            # frozen or builtin modules
            if loader.is_package(name):
                self.__path__ = [name]

        if getattr(self, '__package__', None) is None:
            try:
                self.__package__ = self.__name__
                if not hasattr(self, '__path__'):
                    self.__package__ = self.__package__.rpartition('.')[0]
            except AttributeError:
                pass

        self.__code__ = loader.get_code(name)

        # This would allow to find submodules (but it fails in ziparchives):
        ## if hasattr(self, "__path__"):
        ##     print(self)
        ##     for pathname in os.listdir(self.__path__[0]):
        ##         dir, fname = os.path.split(pathname)
        ##         modname, ext = os.path.splitext(fname)
        ##         if modname != "__init__" and ext in (".py", ".pyc", ".pyo", ".pyd"):
        ##             print("   ", modname)
        ##     print()

    def __repr__(self):
        s = "Module(%s" % self.__name__
        if getattr(self, "__file__", None) is not None:
            s = s + ", %r" % (self.__file__,)
        if getattr(self, "__path__", None) is not None:
            s = s + ", %r" % (self.__path__,)
        return s + ")"

################################################################

if __name__ == "__main__":
    import getopt
    opts, args = getopt.getopt(sys.argv[1:],
                               "dm:x:r",
                               ["module=", "exclude=", "debug", "report"])

    debug = 0
    excludes = []
    report = 0
    modules = []
    for o, a in opts:
        if o in ("-x", "--excludes"):
            excludes.append(a)
        elif o in ("-m", "--module"):
            modules.append(a)
        elif o in ("-d", "--debug"):
            debug = 1
        elif o in ("-r", "--report"):
            report += 1

    if args:
        raise getopt.error("No arguments expected, got '%s'" % ", ".join(args))

    mf = ModuleFinder(
##        excludes=excludes,
##        debug=debug,
        )
    sys.path.insert(0, ".")
    for name in modules:
        # Hm, call import_hook() or safe_import_hook() here?
        if name.endswith(".*"):
            mf.safe_import_hook(name[:-2], None, ["*"])
        else:
            mf.safe_import_hook(name)
    if report:
        mf.report_modules()
        mf.report_missing()
