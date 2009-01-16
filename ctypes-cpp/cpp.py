from cpptypes import *

class CSimpleClass(Class):
    pass
CSimpleClass._fields_ = [
    ('_vtable', c_void_p),
    ('value', c_int),
]
CSimpleClass._methods_ = [
##    method('__cpp_constructor__', 'CSimpleClass::CSimpleClass(int)', argtypes=[c_int]),
    constructor('CSimpleClass::CSimpleClass(int)', argtypes=[c_int]),
##    ('__cpp_constructor__', 'CSimpleClass::CSimpleClass(CSimpleClass const&)', argtypes=[POINTER(CSimpleClass)]),
    copy_constructor(),
    method('__cpp_constructor__', 'CSimpleClass::CSimpleClass(CSimpleClass const&)', argtypes=[POINTER(CSimpleClass)]),
    method('M1', 'CSimpleClass::M1()'),
    method('M1', 'CSimpleClass::M1(int)', argtypes=[c_int]),
    method('V0', 'CSimpleClass::V0()'),
    method('V1', 'CSimpleClass::V1()'),
    method('V1', 'CSimpleClass::V1(int)', argtypes=[c_int]),
    method('V1', 'CSimpleClass::V1(char*)', argtypes=[c_char_p]),
    method('V1', 'CSimpleClass::V1(int,char*)', argtypes=[c_int, c_char_p]),
    method('V1', 'CSimpleClass::V1(char*,int)', argtypes=[c_char_p, c_int]),
    method('V2', 'CSimpleClass::V2()'),
##    method('__cpp_destructor__', 'CSimpleClass::~CSimpleClass()'),
    destructor(),
]
CSimpleClass._finish(CPPDLL("mydll.dll"))
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
