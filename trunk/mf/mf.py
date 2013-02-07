#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
"""Modulefinder based on importlib
"""

# BUGS: Doesn't find all the modules that the old modulefinder finds?
# But it seems this is a bug of the old modulefinder.  Example: the
# old one finds 'multiprocessing.Pool' which is not a module but a
# class.  A module exists with different casing 'multiprocessing.pool'
#

# Differences for Python's standard modulefinder:
#
# Old behaviour:
#
# import_hook("package", None, ["*"]) did find all submodules in a
# package; this does no longer work.
#
# New behaviour:
#
# import_hook("package", None, ["*"]) behaves like Python's
# 'from package import *' (which does not pull in submodules).
#
# It is not clear how importlib could list all the submodules
# in a package
#
# New behaviour: a lot faster
#
#  import_hook("os") => 45% runtime
#  import_hook("numpy") => 46% runtime


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

    def __init__(self, excludes=[], debug=0):
        self._debug = debug
        self._modules = {} # simulates sys.modules

        self.excludes = set(excludes)
        # bdb, for example, imports __main__, and this would
        # find the real __main__!
        self.excludes.add("__main__")

        self.__last_caller = None
        self.depgraph = defaultdict(set)


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
            elif package not in self._modules:
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
            if parent not in self._modules:
                self._gcd_import(parent)
            # Crazy side-effects!
            if name in self._modules:
                return self._modules[name]
            # Backwards-compatibility; be nicer to skip the dict lookup.
            parent_module = self._modules[parent]
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
        elif name not in self._modules:
            # The parent import may have already imported this module.
            self._load_module(loader, name)
        # Backwards-compatibility; be nicer to skip the dict lookup.
        module = self._modules[name]

        if parent:
            # Set the module as an attribute on its parent.
            parent_module = self._modules[parent]
            setattr(parent_module, name.rpartition('.')[2], module)

        # It is important that all the required __...__ attributes at
        # the module are set before the code is scanned.
        if module.__code__:
            self._scan_code(module.__code__, module)

        return module

    # XXX TODO:  Should _gcd_import be the only place in the code where
    # self._modules[...] is checked?  this would allow to do the whole dependency
    # tracking in one place, and would maybe also help the debug logs...
        

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

        # 'name' is now the fully qualified, absolute name of the module we want to import.
        self.depgraph[name].add(self.__last_caller.__name__ if self.__last_caller else "-")

        if name in self.excludes:
            raise ImportError(_ERR_MSG.format(name), name=name)
        if name in self._modules:
            return self._modules[name]
        try:
            return self._find_and_load(name)
        except ImportError:
            self._modules[name] = None
            raise ImportError(name)


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
                ## # This does certainly not work in ModuleFinder:
                ## if hasattr(module, '__all__'):
                ##     fromlist.extend(module.__all__)
            for x in fromlist:
                if x in module.__globalnames__:
                    if self._debug:
                        print("%s  # found global %s in %s" % (self.indent, x, module.__name__))
                    continue
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
        elif module is not None:
            for x in fromlist:
                if x == "*":
                    continue
                if x in module.__globalnames__:
                    if self._debug:
                        print("%s  # found global %s in %s" % (self.indent, x, module.__name__))
                    continue
                raise ImportError("%s.%s" % (module.__name__, x))
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
        
        self.__old_last_caller = self.__last_caller
        self.__last_caller = caller
        try:
            return self._import_hook(name, caller, fromlist, level)
        except:
            raise
        finally:
            self.__last_caller = self.__old_last_caller

    def _import_hook(self, name, caller=None, fromlist=(), level=0):
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
                return self._modules[module.__name__[:len(module.__name__)-cut_off]]
        else:
            try:
                return self._handle_fromlist(module, fromlist)
            except ImportError:
                raise
            except Exception:
                import traceback; traceback.print_exc()

    ################################################################
    def safe_import_hook(self, name, caller=None, fromlist=(), level=0):
        """Wrapper for import_hook() that catches ImportError.

        """
        if self._debug:
            self.indent += self.INDENT
            self._info(name, caller, fromlist, level)

        try:
            mod = self.import_hook(name, caller, fromlist, level)
            if self._debug:
                print("%s=> %s" % (self.indent, mod.__name__))
        except ImportError as exc:
            if level:
                name = self._resolve_name(name, caller.__name__, level)
            if self._debug:
                print("%sImportError: %s" % (self.indent, exc))
        finally:
            self.indent = self.indent[:-len(self.INDENT)]


    INDENT = "    "
    indent = ""
    def _info(self, name, caller, fromlist, level):
        """Print the call as a Python import statement, indented.

        """

        if caller:
            caller_info = "# in %s" % caller.__name__
        else:
            caller_info = ""

        if level == 0:
            if fromlist:
                print("%sfrom %s import %s" % (self.indent, name, ", ".join(fromlist)), caller_info)
            else:
                print("%simport %s" % (self.indent, name), caller_info)
        elif name:
            print("%sfrom %s import %s" % (self.indent, "."*level + name, ", ".join(fromlist)), caller_info)
        else:
            print("%sfrom %s import %s" % (self.indent, "."*level, ", ".join(fromlist)), caller_info)


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
        if name in self._modules:
            return self._modules[name]

        # See importlib.abc.Loader
        try:
            self._modules[name] = Module(loader, name)
        except ImportError:
            raise
        # Don't catch other exceptions: let them propagates
        # loader.get_code() can raise a SyntaxError, for example, when
        # compiling code.
        #
        # In Python 3.3.0 (but not in 3.4), _frozen_importlib's loader
        # raises an exception when is_package() is called.


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

    @property
    def modules(self):
        """
        A dictionary containing the found modules.
        """
        return dict((n, v) for (n, v) in self._modules.items()
                    if v)


    def missing(self):
        """Return a list of modules that appear to be missing. Use
        any_missing_maybe() if you want to know which modules are
        certain to be missing, and which *may* be missing.

        """
        return [n for n in self._modules
                if self._modules[n] is None]

    def any_missing_maybe(self):
        """Return two lists, one with modules that are certainly missing
        and one with modules that *may* be missing. The latter names could
        either be submodules *or* just global names in the package.

        The reason it can't always be determined is that it's impossible to
        tell which names are imported when "from module import *" is done
        with an extension module, short of actually importing it.
        """
        raise NotImplementedError

    def report(self):
        """Print a report to stdout, listing the found modules with
        their paths, as well as modules that are missing, or seem to
        be missing.

        """
        self.report_modules()
        self.report_missing()

    def report_missing(self):
        """Print a report to stdout, listing those modules that are
        missing.

        """
        print()
        print("  %-35s" % "Missing Modules")
        print("  %-35s" % "---------------")
        for name in sorted(self.missing()):
            deps = sorted(self.depgraph[name])
            print("? %-35s imported from %s" % (name, ", ".join(deps)))


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

# /python33/lib/curses
# /python33/lib/site-packages/numpy

# What about IronPath..., clr, ...?

# What about old, deprecated modules (compiler, for example):
# compiler, new, sets, ...

# There is something strange with the importlib package, so we exclude
# it automatically.

WIN32_EXCLUDES = """\
_dummy_threading
_emx_link
_gestalt
_posixsubprocess
_scproxy
_sysconfigdata
ce
curses
fcntl
grp
importlib
importlib._bootstrap
importlib.machinery
java.lang
org.python.core
os2
posix
pwd
termios
vms_lib
""".split()

if __name__ == "__main__":
    import getopt
    opts, args = getopt.getopt(sys.argv[1:],
                               "dm:x:r",
                               ["module=", "exclude=", "debug", "report"])

    debug = 0
    excludes = WIN32_EXCLUDES
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

    mf = ModuleFinder(excludes=excludes,
                      debug=debug,
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
