from cpptypes import *

class CSimpleClass(Class):
    pass
CSimpleClass._fields_ = [
    ('_vtable', c_void_p),
    ('value', c_int),
]
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
CSimpleClass._finish(CPPDLL("mydll.dll"))

################################################################

if __name__ == "__main__":
##    help(CSimpleClass)

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

    try:
        obj.V1(3.12)
    except TypeError:
        pass
    else:
        raise RuntimeError("expected TypeError not raised")

    aCopy = CSimpleClass(obj)
    del obj
    print aCopy

##    help(CSimpleClass)
