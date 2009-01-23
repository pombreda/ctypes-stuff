import cpptypes

class MySimpleClass(cpptypes.Class):
    _realname_ = "CSimpleClass"
MySimpleClass._cpp_fields_ = [
    ('_vtable', cpptypes.c_void_p),
    ('value', cpptypes.c_int),
]
MySimpleClass._methods_ = [
    # The following two lines are equivalent...
##    method('__cpp_constructor__', 'CSimpleClass::CSimpleClass(int)', argtypes=[c_int]),
    cpptypes.constructor('CSimpleClass::CSimpleClass(int)', argtypes=[cpptypes.c_int]),

    # The following two lines are equivalent...
##    method('__cpp_constructor__', 'CSimpleClass::CSimpleClass(CSimpleClass const&)', argtypes=[POINTER(CSimpleClass)]),
    cpptypes.copy_constructor(),

    cpptypes.method('M1', 'CSimpleClass::M1()'),
    cpptypes.method('M1', 'CSimpleClass::M1(int)', argtypes=[cpptypes.c_int]),
    cpptypes.method('V0', 'CSimpleClass::V0()', virtual=True),
    cpptypes.method('V1', 'CSimpleClass::V1(int)', argtypes=[cpptypes.c_int], virtual=True),
    cpptypes.method('V1', 'CSimpleClass::V1()', virtual=True),
    cpptypes.method('V1', 'CSimpleClass::V1(char*)', argtypes=[cpptypes.c_char_p], virtual=True),
    cpptypes.method('V1', 'CSimpleClass::V1(int,char*)', argtypes=[cpptypes.c_int, cpptypes.c_char_p], virtual=True),
    cpptypes.method('V1', 'CSimpleClass::V1(char*,int)', argtypes=[cpptypes.c_char_p, cpptypes.c_int], virtual=True),
    cpptypes.method('V2', 'CSimpleClass::V2()', virtual=True),

    # The following two lines are equivalent...
##    method('__cpp_destructor__', 'CSimpleClass::~CSimpleClass()'),
    cpptypes.destructor(),
]

MySimpleClass._finish(cpptypes.CPPDLL("mydll.dll"))

################################################################

if __name__ == "__main__":
##    help(MySimpleClass)

    obj = MySimpleClass(42)
    print obj.value
    print "M1(4200)"
    obj.M1(42000)
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

    try:
        obj.M1(-1)
    except cpptypes.UncatchedCppException:
        pass
    else:
        raise RuntimeError("expected UnCatchedCppException not raised")

    aCopy = MySimpleClass(obj)
    del obj
    print aCopy

    help(MySimpleClass)
