from cpptypes import *

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
                print "\tMATCH   :", argtypes[1:], args
                return result
            except ArgumentError, details:
                pass
        print "\tNO MATCH:", argtypes[1:], args
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
        """This class method scans the _methods_ list, and creates Python methods
        that forward to the C++ methods.
        """
        for info in cls._methods_:
            mth_name, func_name = info[:2]
            print mth_name, func_name
            func = getattr(dll, func_name)
            func.restype = info[2]
            func.argtypes = (POINTER(cls),) + info[3:]
            mth = make_method(cls, func, mth_name, func_name)
            setattr(cls, mth_name, mth)


################################################################

class CSimpleClass(Class):
    pass
CSimpleClass._methods_ = [
    # python-method-name, C++ name, restype, *argtypes
    ('__cpp_constructor__', 'CSimpleClass::CSimpleClass(int)', None, c_int),
    ('__cpp_constructor__', 'CSimpleClass::CSimpleClass(CSimpleClass const&)', None, POINTER(CSimpleClass)),
    ('M1', 'CSimpleClass::M1()', None, ),
    ('M1', 'CSimpleClass::M1(int)', None, c_int),
    ('V0', 'CSimpleClass::V0()', None, ),
    ('V1', 'CSimpleClass::V1()', None),
    ('V1', 'CSimpleClass::V1(int)', None, c_int),
    ('V1', 'CSimpleClass::V1(char*)', None, c_char_p),
    ('V2', 'CSimpleClass::V2()', None, ),
    ('__cpp_destructor__', 'CSimpleClass::~CSimpleClass()', None, ),
]
CSimpleClass._fields_ = [
    ('_vtable', c_void_p),
    ('value', c_int),
]
CSimpleClass._finish(CPPDLL("mydll.dll"))

################################################################

def make():
    return CSimpleClass(99)

if __name__ == "__main__":
    help(CSimpleClass)

    obj = CSimpleClass(42)
    print obj.value
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
    print "V1('foo')"
    obj.V1("foo")

    aCopy = CSimpleClass(obj)
    del obj
    print aCopy

##    help(CSimpleClass)
