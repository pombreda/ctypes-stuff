from ctypes import *
import sys

# TODO:
#
# CPPDLL should be able to load functions via demangled names?
#
# How are overloaded virtual functions ordered in the vtable???
# It seems not in the same order as they appear in the include file???
#
# XXX When an instance is created, we could parse the vtable addresses
# and assert that they are the same as the adresses of the exported
# functions we can also load from the dll...
#
# See also the undocumented MSVC /d1reportAllClassLayout command line flag

def parse_names(dll):
    try:
        import get_exports
    except ImportError:
        from ctypeslib.contrib import get_exports
    import undecorate
    dll.member_names = member_names = {}
    flags = undecorate.UNDNAME_NO_MS_KEYWORDS | undecorate.UNDNAME_NO_ACCESS_SPECIFIERS

    for name in get_exports.read_export_table(dll._name):
        name_with_args = undecorate.symbol_name(name, flags).strip()
        # Convert the name to what gccxml creates
        # Replace the (void) argument list with ()
        gccxml_name = name_with_args.replace("(void)", "()")
        # Remove 'virtual void '
        # XXX We should instead remove everything before '<classname>::'.
        for prefix in ("virtual ", "void "):
            # Order of prefixes is important!
            if gccxml_name.startswith(prefix):
                gccxml_name = gccxml_name[len(prefix):]
        if "-v" in sys.argv:
            print gccxml_name
        member_names[gccxml_name] = name

if "-v" in sys.argv:
    print; print

def virtual(name, prototype):
    def func(self, *args):
        return getattr(self._vtable[0], name)(self, *args)
    func.prototype = prototype
    return func

def method(dll, name, prototype):
    member = prototype((name, dll))
    def func(self, *args):
        return member(self, *args)
    func.prototype = prototype
    return func

def multimethod(cls, name, mth):
    old_mth = getattr(cls, name)
    # nargs includes the (implicit) self argument
    nargs = len(mth.prototype._argtypes_)
    def call(self, *args):
        # If the number of arguments is what 'mth' expects, try to
        # call it.  If the actual argument types are not accepted,
        # ctypes will raise an ArgumentError, and the next method is
        # tried.
        #
        # Probably too expensive, but it works.
        if len(args) == nargs - 1:
            try:
                return mth(self, *args)
            except ArgumentError:
                pass
        return old_mth(self, *args)
    call.__name__ = name
    call.__doc__ = "%s\n%s" % (mth.__doc__, old_mth.__doc__)
    return call

class Class(Structure):
    def __new__(cls, *args):
        if not hasattr(cls, "_fields_"):
            if not hasattr(cls.__dll__, "member_names"):
                parse_names(cls.__dll__)

            virtual_methods = []
            for m in cls._methods_:
                name, is_virt, demangled, restype = m[:4]
                argtypes = m[4:]
                prototype = CPPMETHODTYPE(restype, POINTER(cls), *argtypes)
                if is_virt:
                    # Make sure the method exists
                    func_name = cls.__dll__.member_names[demangled]
                    prototype((func_name, cls.__dll__))
                    # Create a virtual method
                    # Names must be unique to allow overloading
                    v_name = "%s(%s)" % (name, len(virtual_methods))
                    virtual_methods.append((v_name, prototype))
                    mth = virtual(v_name, prototype)
                else:
                    # Create a 'normal' method
                    func_name = cls.__dll__.member_names[demangled]
                    mth = method(cls.__dll__, func_name, prototype)
                mth.__name__ = name
                mth.__doc__ = demangled
                if hasattr(cls, name):
                    # Overloaded function
                    mm = multimethod(cls, name, mth)
                    setattr(cls, name, mm)
                else:
                    setattr(cls, name, mth)

            if virtual_methods:
                class VTBL(Structure):
                    _fields_ = virtual_methods
                cppfields = cls._cppfields_
                assert cppfields[0][0] == "_vtable"
                cppfields[0] = ("_vtable", POINTER(VTBL))
                cls._fields_ = cppfields
        result = super(Class, cls).__new__(cls, *args)
        result._needs_free = False
        return result

    def __init__(self, *args):
        # __init__ calls the cpp constructor, and also sets the
        # _needs_free flag so the the cpp desctructor is called when
        # the Python instance goes away.
        self.__cpp_constructor__(*args)
        self._needs_free = True

    def __del__(self):
        if self._needs_free:
            self._needs_free = False
            self.__cpp_destructor__()

################################################################

class CSimpleClass(Class):
    __dll__ = CDLL("mydll.dll")
CSimpleClass._methods_ = [
    # python-method-name, is_virtual, C++ name, restype, *argtypes
    ('__cpp_constructor__', False, 'CSimpleClass::CSimpleClass(int)', None, c_int),
    ('__cpp_constructor__', False, 'CSimpleClass::CSimpleClass(class CSimpleClass const &)', None, POINTER(CSimpleClass)),
    ('M1', False, 'CSimpleClass::M1()', None, ),
    ('M1', False, 'CSimpleClass::M1(int)', None, c_int),
    ('V0', True, 'CSimpleClass::V0()', None, ),
    ('V1', True, 'CSimpleClass::V1()', None),
    ('V1', True, 'CSimpleClass::V1(int)', None, c_int),
    ('V2', True, 'CSimpleClass::V2()', None, ),
    ('__cpp_destructor__', False, 'CSimpleClass::~CSimpleClass()', None, ),
]
CSimpleClass._cppfields_ = [
    ('_vtable', c_void_p),
    ('value', c_int),
]

################################################################

def make():
    return CSimpleClass(99)

if __name__ == "__main__":
    obj = CSimpleClass(42)
##    print obj.value
    print "M1(42)"
    obj.M1(42)
    print "M1()"
    obj.M1()
    print "V1(96)"
    obj.V1(96)
    print "V2()"
    obj.V2()
    print "V1()"
    obj.V1()

    aCopy = CSimpleClass(obj)
    del obj
    print aCopy

##    help(CSimpleClass)
