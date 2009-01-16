from ctypes import *

def multimethod(cls, name, mth):
    old_mth = getattr(cls, name)
    argtypes = mth.cpp_func.argtypes
    nargs = len(argtypes)

    def call(self, *args):
        # If the number of arguments is what 'mth' expects, try to
        # call it.  If the actual argument types are not accepted,
        # ctypes will raise an ArgumentError, and the next method is
        # tried.
        #
        # Probably too expensive, but it works.
        #
        # nargs includes the (implicit) self argument
        if len(args) == nargs - 1:
            try:
                result = mth(self, *args)
##                print "\tMATCH   :", argtypes[1:], args
                return result
            except ArgumentError, details:
                pass
##        print "\tNO MATCH:", argtypes[1:], args
        try:
            return old_mth(self, *args)
        except (ArgumentError, TypeError):
            raise TypeError("no overloaded function matches")
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
        return multimethod(cls, mth_name, call)
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
    dll = CPPDLL("mydll.dll")
    print dll
    print getattr(dll, "??0CSimpleClass@@QAE@ABV0@@Z")
    print getattr(dll, "??0CSimpleClass@@QAE@H@Z")
    print getattr(dll, "CSimpleClass::CSimpleClass(int)")
    print getattr(dll, "CSimpleClass::CSimpleClass(int)")
    print getattr(dll, "CSimpleClass::~CSimpleClass()")

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
