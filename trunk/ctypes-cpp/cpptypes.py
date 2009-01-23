# -*- coding: latin-1 -*-
from ctypes import *
import warnings

# I'm not sure the vtable layout is correct.  So, this variable
# determines if virtual functions are called through the vtable (True)
# or by name (False).
USE_VIRTUAL = True

try:
    from itertools import product as _product
except ImportError:
    # Only Python 2.6 and up have itertools.product. Use the pure
    # Python version from the 2.6 docs when not available:
    def _product(*args, **kwds):
        # product('ABCD', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy
        # product(range(2), repeat=3) --> 000 001 010 011 100 101 110 111
        pools = map(tuple, args) * kwds.get('repeat', 1)
        result = [[]]
        for pool in pools:
            result = [x+[y] for x in result for y in pool]
        for prod in result:
            yield tuple(prod)

try:
    all
except NameError:
    # all is only in Python 2.5 and above.
    def all(iterable):
         for element in iterable:
             if not element:
                 return False
         return True

# XXX add all the primitive ctypes types: c_char, c_byte, ...
_argtypes_matches = {c_int: [int, long, c_int],
                     c_long: [int, long, c_long],
                     # XXX c_char_p would also accept (c_char * n) arrays
                     c_char_p: [str, unicode, type(None), c_char_p, POINTER(c_char)]
                     }

def _type_matcher(argtypes):
    # XXX For long argument lists, the result can get pretty large.
    # It will ensure a very fast lookup at the expense of the
    # dictionary size that is built from the result.  Not sure it
    # matters, though, since it is only uses for overloaded functions.
    """Return a generator producing all possible tuples of types that
    will match the specified argtypes.  Here are examples::
    
    >>> import ctypes
    >>> for item in _type_matcher([ctypes.c_char_p]):
    ...     print item
    (<type 'str'>,)
    (<type 'unicode'>,)
    (<type 'NoneType'>,)
    (<class 'ctypes.c_char_p'>,)
    (<class 'ctypes.LP_c_char'>,)
    
    >>> for item in _type_matcher([POINTER(c_long)]):
    ...     print item
    (<class 'ctypes.c_long'>,)
    (<class '__main__.LP_c_long'>,)
    >>>

    >>> for item in _type_matcher([]):
    ...     print item
    ()
    >>>

    >>> for item in _type_matcher([c_long, c_long]):
    ...     print item
    (<type 'int'>, <type 'int'>)
    (<type 'int'>, <type 'long'>)
    (<type 'int'>, <class 'ctypes.c_long'>)
    (<type 'long'>, <type 'int'>)
    (<type 'long'>, <type 'long'>)
    (<type 'long'>, <class 'ctypes.c_long'>)
    (<class 'ctypes.c_long'>, <type 'int'>)
    (<class 'ctypes.c_long'>, <type 'long'>)
    (<class 'ctypes.c_long'>, <class 'ctypes.c_long'>)
    >>>
    """
    result = []
    for tp in argtypes:
        possible = _argtypes_matches.get(tp, None)
        if possible is None:
            if hasattr(tp, "_type_"):
                # ctypes POINTER(tp) does also accept tp instances
                possible = [tp._type_, tp]
        result.append(possible)
    return _product(*result)

class UncatchedCppException(Exception):
    """Raised when Windows SEH catches a C++ exception.

    XXX It seems that SEH also prints 'error -529697949' to stdout?
    """

class method(object):
    """Helper to create a C++ method."""
    def __init__(self, mth_name, func_name, restype=None, argtypes=(), virtual=False):
        self.mth_name = mth_name
        self.func_name = func_name
        self.restype = restype
        self.argtypes = argtypes
        self.virtual = virtual

    def _create(self, dll, cls):
        argtypes = (POINTER(cls),) + tuple(self.argtypes)
        proto = self.virtual_prototype = CPPMETHODTYPE(self.restype, *argtypes)

        if USE_VIRTUAL and self.virtual:
            from operator import attrgetter
            getter = attrgetter(self.func_name)
            def call(self, *args):
##                return getter(self.pvtable[0])(self, *args)
                try:
                    return getter(self.pvtable[0])(self, *args)
                except WindowsError, details:
                    if details.args == ("exception code 0xe06d7363",):
                        raise UncatchedCppException("uncatched C++ exception")
                    raise
        else:
            mangled = dll._names_map[self.func_name]
            func = proto((mangled, dll))
            def call(self, *args):
##                return func(self, *args)
                try:
                    return func(self, *args)
                except WindowsError, details:
                    if details.args == ("exception code 0xe06d7363",):
                        raise UncatchedCppException("uncatched C++ exception")
                    raise

        call.__doc__ = self.func_name
        call.__name__ = self.mth_name
        return call, self.argtypes

    def __repr__(self):
        return "<method(%r, %r, virtual=%s at %x>" % \
               (self.mth_name, self.func_name, self.virtual, id(self))

class constructor(method):
    """Helper to create a C++ constructor."""
    # Constructors cannot be virtual.
    def __init__(self, func_name, argtypes=()):
        super(constructor, self).__init__("__cpp_constructor__",
                                          func_name,
                                          restype=None,
                                          argtypes=argtypes)

class copy_constructor(method):
    """Helper to create a C++ copy constructor."""
    # Constructors cannot be virtual.
    def __init__(self):
        super(copy_constructor, self).__init__("__cpp_constructor__",
                                               None,
                                               restype=None,
                                               argtypes=())

    def _create(self, dll, cls):
        name = getattr(cls, "_realname_", cls.__name__)
        self.func_name = '%s::%s(%s const&)' % (name, name, name)
        self.argtypes = (POINTER(cls),)
        return super(copy_constructor, self)._create(dll, cls)

class destructor(method):
    """Helper to create a C++ destructor."""
    def __init__(self, virtual=False):
        super(destructor, self).__init__("__cpp_destructor__",
                                         None,
                                         restype=None,
                                         argtypes=(),
                                         virtual=virtual)

    def _create(self, dll, cls):
        name = getattr(cls, "_realname_", cls.__name__)
        self.func_name = '%s::~%s()' % (name, name)
        return super(destructor, self)._create(dll, cls)

class OverloadingError(TypeError):
    """This exception is raised if an overloaded method could not be
    matched to the types of the actual arguments"""

class OverloadingConflict(UserWarning):
    """This warning is emitted when there are conflicting argspec entries
    in an overloaded method."""

def _multimethod(name, info):
    """Return a method that dispatches to one of the C++ overloaded
    methods depending on the actual argument types passed in the call.
    """
    # info is a sequence containing (mth, argtypes) tuples
    methodmap = {}
    docs = ["--overloaded method--"]
    for mth, argtypes in info:
        docs.append(mth.__doc__)
        for argspec in _type_matcher(argtypes):
            if argspec in methodmap:
                warnings.warn("Conflicting entries for '%s'" % mth.__name__,
                              OverloadingConflict, stacklevel=3)
            methodmap[argspec] = mth

    def call(self, *args):
        argtypes = tuple([type(a) for a in args])
        try:
            mth = methodmap[argtypes]
        except KeyError:
            # No exact match found.  It may be possible that one or
            # more arguments are instances of subclasses of argtypes,
            # which would be accepted as well.
            for types in methodmap.iterkeys():
                if len(types) != len(argtypes):
                    continue
                if all(isinstance(a, t) for a, t in zip(args, types)):
                    mth = methodmap[types]
                    # Extend the dispatcher so that we can match
                    # faster next time the methd is called with the
                    # same argument types.
                    methodmap[argtypes] = mth
                    break
            else:
                raise OverloadingError("No matching signature found for overloaded function")
        return mth(self, *args)

    call.__doc__ = "\n".join(docs)
    call.__name__ = name
    return call

class Class(Structure):
    """Base class for C++ class proxies."""
    _needs_free = False
    def __init__(self, *args):
        """__init__ calls the cpp constructor, and also sets the
        _needs_free flag so the the cpp destructor is called when
        the Python instance goes away.
        """
        self.__cpp_constructor__(*args)
        self._needs_free = True

    def __del__(self):
        """The destructor is only called when the _needs_free flag is
        set because this instance has been created by Python code.
        """
        if self._needs_free:
            self._needs_free = False
            self.__cpp_destructor__()

    @classmethod
    def _finish(cls, dll):
        """This classmethod iterates over the _methods_ list, and
        creates Python methods that forward to the C++ methods.
        """
        # XXX TODO: This code is complicated enough so that it should
        # be moved into a ClassBuilder class.
        if "_class_finished" in cls.__dict__:
            warnings.warn("class %s already finished" % cls,
                          stacklevel=2)
            return

        # Determine the order of virtual methods in the vtable.
        virtual_methods = []
        seen = set()
        for item in cls._methods_:
            if not item.virtual:
                continue
            name = item.mth_name
            if name in seen:
                virtual_methods[-1].insert(0, item)
            else:
                virtual_methods.append([item])
            seen.add(name)

        # Assign the vtable_index to virtual methods
        index = 0
        for methods in virtual_methods:
            for m in methods:
                m.vtable_index = index
                index += 1

        # Build all the methods, and collect them into a dictionary.
        # Key is the method name, value is a list containing one (or
        # more, in case of overloading) methods.
        methods = {}
        for item in cls._methods_:
            mth, argtypes = item._create(dll, cls)
            methods.setdefault(mth.__name__, []).append((mth, argtypes))

        # Attach the methods to the class.  Overloaded functions are
        # stuffed into a _multimethod dispatcher.
        for name, info in methods.iteritems():
            if len(info) == 1:
                mth, argtypes = info[0]
                setattr(cls, name, mth)
            else:
                mth = _multimethod(name, info)
                setattr(cls, name, mth)

        # Now, build the vtable structure
        vtable_fields = []
        for methods in virtual_methods:
            for m in methods:
                vtable_fields.append((m.func_name, m.virtual_prototype))
        class VTABLE(Structure):
            _fields_ = vtable_fields

        # Determine _fields_ from _cpp_fields_, and assign to the class
        fields = list(cls._cpp_fields_)[:]
        fields[0] = ("pvtable", POINTER(VTABLE))
        cls._fields_ = fields

        # Done.
        cls._class_finished = True

# XXX The following code should be in Lib/ctypes/__init__.py:

class AnyDLL(CDLL):
    """This class does NOT allow to access functions by attribute access.
    XXX Need to invent an api.

    Functions can be accessed as attributes, using the mangled or the
    demangled name.
    """

    # XXX Should we allow unnormalized, demangled name?  Should we try
    # to read function addresses from a map file?

    def __init__(self, path, *args, **kw):
        import get_exports
        function_names = get_exports.read_export_table(path)
        self._names_map = {}
        for mangled in function_names:
            demangled = self.normalize(self.undecorate(mangled))
            self._names_map[demangled] = mangled
        super(AnyDLL, self).__init__(path, *args, **kw)

    def undecorate(self, name):
        import undecorate
        flags = undecorate.UNDNAME_NO_MS_KEYWORDS \
                | undecorate.UNDNAME_NO_ACCESS_SPECIFIERS
        return undecorate.symbol_name(name, flags)

    def normalize(self, name):
        # Remove the return type from function prototypes.  Types from
        # variable declaration are not removed.
        #
        # XXX Does not work for templates, the regexp would be much
        # more complicated.
        name = name.strip()
        if name.endswith("const"):
            name = name[:-len("const")]
        # Some of these replacements should probably be done with re,
        # to be more immune to whitespace.
        name = name.replace(", ", ",")
        name = name.replace("(void)", "()")
        name = name.replace(" &", "&")
        name = name.replace(" *", "*")
        name = name.replace("class ", "")
        name = name.replace("struct ", "")
        name = name.strip()
        if "(" in name:
            import re
            m = re.search(r"([a-zA-Z]\w*::)?~?[a-zA-Z]\w*\(.*\)$", name)
            if m:
                return m.group(0)
        return name

    def __getattr__(self, name):
        # We override __getattr__ so that accessing functions as
        # attributes does no longer work.
        raise AttributeError(name)

##        """This method allows to access functions by mangled name and
##        by demangled name.  The demangled name does not need to be
##        normalized.
##        """
##        try:
##            # try mangled name
##            result = super(CPPDLL, self).__getattr__(name)
##            # XXX better caching?
##        except AttributeError:
##            # try demangled name
##            try:
##                demangled = self._names_map[name]
##            except KeyError:
##                name = self.normalize(name)
##                demangled = self._names_map[name]
##            result = super(CPPDLL, self).__getattr__(demangled)
##            setattr(self, demangled, result)
##        setattr(self, name, result)
##        return result

from _ctypes import FUNCFLAG_THISCALL as _FUNCFLAG_THISCALL
from _ctypes import CFuncPtr as _CFuncPtr

_cpp_methodtype_cache = {}
def CPPMETHODTYPE(restype, *argtypes):
    try:
        return _cpp_methodtype_cache[(restype, argtypes)]
    except KeyError:
        class CppMethodType(_CFuncPtr):
            _argtypes_ = argtypes
            _restype_ = restype
            _flags_ = _FUNCFLAG_THISCALL
        _cpp_methodtype_cache[(restype, argtypes)] = CppMethodType
        return CppMethodType


if __name__ == "__main__":
    import doctest
    doctest.testmod()
