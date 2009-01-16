from ctypes import *

try:
    from itertools import product
except ImportError:
    # Only Python 2.6 and up have itertools.product. Use the pure
    # Python version from the 2.6 docs when not available:
    def product(*args, **kwds):
        # product('ABCD', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy
        # product(range(2), repeat=3) --> 000 001 010 011 100 101 110 111
        pools = map(tuple, args) * kwds.get('repeat', 1)
        result = [[]]
        for pool in pools:
            result = [x+[y] for x in result for y in pool]
        for prod in result:
            yield tuple(prod)

# XXX add all the primitive ctypes types
matches = {c_int: [int, long, c_int],
           c_long: [int, long, c_long],
           c_char_p: [str, unicode, type(None), c_char_p]
           }

def type_matcher(argtypes):
    """Return a generator producing tuples of types that will match
    the specified argtypes.
    
    >>> import ctypes
    >>> for item in type_matcher([ctypes.c_long, ctypes.c_char_p]):
    ...     print item
    (<type 'int'>, <type 'str'>)
    (<type 'int'>, <type 'unicode'>)
    (<type 'int'>, <type 'NoneType'>)
    (<type 'int'>, <class 'ctypes.c_char_p'>)
    (<type 'long'>, <type 'str'>)
    (<type 'long'>, <type 'unicode'>)
    (<type 'long'>, <type 'NoneType'>)
    (<type 'long'>, <class 'ctypes.c_char_p'>)
    (<class 'ctypes.c_long'>, <type 'str'>)
    (<class 'ctypes.c_long'>, <type 'unicode'>)
    (<class 'ctypes.c_long'>, <type 'NoneType'>)
    (<class 'ctypes.c_long'>, <class 'ctypes.c_char_p'>)

    >>> class X(Structure):
    ...     pass
    >>> for item in type_matcher([POINTER(X)]):
    ...     print item
    (<class '__main__.X'>,)
    (<class '__main__.LP_X'>,)
    >>>

    >>> for item in type_matcher([]):
    ...     print item
    ()
    >>>
    """
    result = []
    for tp in argtypes:
        possible = matches.get(tp, None)
        if possible is None:
            if hasattr(tp, "_type_"):
                # a ctypes POINTER type, the type itself is also accepted
                possible = matches[tp] = [tp._type_, tp]
        result.append(possible)
    return product(*result)


def overloaded_method(cls, name, mth):
    # This overloadedmethod will try to match the arguments passed to the
    # patterns returned by type_matcher, call the method if a match is
    # found and forward to the next overloaded method when no match is
    # found.
    # XXX Use dictionaty lookup instead of linear searching.
    old_mth = getattr(cls, name)
    argtypes = mth.cpp_func.argtypes
    nargs = len(argtypes)
    patterns = list(type_matcher(argtypes[1:]))

    def call(self, *args):
        signature = tuple(type(a) for a in args)
        if signature in patterns:
            return mth(self, *args)
        return old_mth(self, *args)
    call.__name__ = name
    call.__doc__ = "%s\n%s" % (mth.__doc__, old_mth.__doc__)
    return call


def make_method(cls, func, mth_name, func_name):
    # factory for methods
    def call(self, *args):
        return func(self, *args)
    call.__doc__ = func_name
    call.__name__ = mth_name
    call.cpp_func = func
    if hasattr(cls, mth_name):
        return overloaded_method(cls, mth_name, call)
    else:
        return call

class Class(Structure):
    """Base class for C++ class proxies."""
    _needs_free = False
    def __init__(self, *args):
        # __init__ calls the cpp constructor, and also sets the
        # _needs_free flag so the the cpp desctructor is called when
        # the Python instance goes away.
        self.__cpp_constructor__(*args)
        self._needs_free = True

    def __del__(self):
        # The destructor is only called if this instance has been
        # created by Python code.
        if self._needs_free:
            self._needs_free = False
            self.__cpp_destructor__()

    @classmethod
    def _finish(cls, dll):
        """This classmethod scans the _methods_ list, and creates Python methods
        that forward to the C++ methods.
        """
        if "_class_finished" in cls.__dict__:
            import warnings
            warnings.warn("class %s already finished" % cls)
            return
        for info in cls._methods_:
            mth_name, func_name = info[:2]
            func = getattr(dll, func_name)
            func.restype = info[2]
            func.argtypes = (POINTER(cls),) + info[3:]
            mth = make_method(cls, func, mth_name, func_name)
            setattr(cls, mth_name, mth)
        cls._class_finished = True

class CPPDLL(CPPDLL):
    """This class represents a dll exporting functions using the
    Windows __thiscall calling convention.

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
        super(CPPDLL, self).__init__(path, *args, **kw)

    def undecorate(self, name):
        import undecorate
        flags = undecorate.UNDNAME_NO_MS_KEYWORDS \
                | undecorate.UNDNAME_NO_ACCESS_SPECIFIERS
        return undecorate.symbol_name(name, flags)

    def normalize(self, name):
        # Remove the return type from function prototypes.  Types from
        # variable declaration are not removed.
        #
        # Does not work for templates, the regexp would be much more
        # complicated.
        name = name.strip()
        if name.endswith("const"):
            name = name[:-len("const")]
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
        """This method allows to access functions by mangled name
        and by unmangled normalized name."""
        try:
            # try mangled name
            result = super(CPPDLL, self).__getattr__(name)
            # XXX Should also try to find and cache with the demangled
            # name, but this is only for performance...
        except AttributeError:
            # try demangled name
            try:
                demangled = self._names_map[name]
            except KeyError:
                name = self.normalize(name)
                demangled = self._names_map[name]
            result = super(CPPDLL, self).__getattr__(demangled)
            setattr(self, demangled, result)
        setattr(self, name, result)
        return result

if __name__ == "__main__":
    if 1:
        import doctest
        doctest.testmod()

    if 1:
        dll = CPPDLL("mydll.dll")
        print dll
##        print getattr(dll, "??0CSimpleClass@@QAE@ABV0@@Z")
##        print getattr(dll, "??0CSimpleClass@@QAE@H@Z")
##        print getattr(dll, "CSimpleClass::CSimpleClass(int)")
##        print getattr(dll, "CSimpleClass::CSimpleClass(int)")
##        print getattr(dll, "CSimpleClass::~CSimpleClass()")

        class X(Structure):
            _fields_ = [("allocate some space", c_int * 32)]
            def __init__(self, value):
                func = getattr(dll, "CSimpleClass::CSimpleClass(int)")
                func(byref(self), value)

            def __del__(self):
                func = getattr(dll, "CSimpleClass::~CSimpleClass()")
                func(byref(self))

        x = X(42)
        del x

