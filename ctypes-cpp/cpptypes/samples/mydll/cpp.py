import cpptypes, os

class COLOR(cpptypes.Structure):
    _fields_ = [("red", cpptypes.c_int),
                ("green", cpptypes.c_int),
                ("blue", cpptypes.c_int),
                ("alpha", cpptypes.c_int)]
    def __repr__(self):
        return "<COLOR %d, %d, %d, %d>" % (self.red, self.green, self.blue, self.alpha)

class color(cpptypes.Structure):
    _fields_ = [("red", cpptypes.c_ubyte),
                ("green", cpptypes.c_ubyte),
                ("blue", cpptypes.c_ubyte),
                ("alpha", cpptypes.c_ubyte)]
    def __repr__(self):
        return "<color %d, %d, %d, %d>" % (self.red, self.green, self.blue, self.alpha)

class MySimpleClass(cpptypes.Class):
    _realname_ = "CSimpleClass"
MySimpleClass._cpp_fields_ = [
    ('_vtable', cpptypes.c_void_p),
    ('value', cpptypes.c_int),
]
MySimpleClass._methods_ = [
    cpptypes.copy_constructor(),
    cpptypes.constructor('CSimpleClass::CSimpleClass(int)', argtypes=[cpptypes.c_int]),
    cpptypes.destructor(),

    cpptypes.method('M1', 'CSimpleClass::M1()'),
    cpptypes.method('M1', 'CSimpleClass::M1(int)', argtypes=[cpptypes.c_int]),
    cpptypes.method('V0', 'CSimpleClass::V0()', virtual=True),
    cpptypes.method('V1', 'CSimpleClass::V1(int)', argtypes=[cpptypes.c_int], virtual=True),
    cpptypes.method('V1', 'CSimpleClass::V1()', virtual=True),
    cpptypes.method('V1', 'CSimpleClass::V1(char*)', argtypes=[cpptypes.c_char_p], virtual=True),
    cpptypes.method('V1', 'CSimpleClass::V1(int,char*)', argtypes=[cpptypes.c_int, cpptypes.c_char_p], virtual=True),
    cpptypes.method('V1', 'CSimpleClass::V1(char*,int)', argtypes=[cpptypes.c_char_p, cpptypes.c_int], virtual=True),
    cpptypes.method('RGB', 'CSimpleClass::RGB(int, int, int, int)',
                    argtypes=[cpptypes.c_int, cpptypes.c_int, cpptypes.c_int, cpptypes.c_int],
                    restype = COLOR),
    cpptypes.method('rgb', 'CSimpleClass::rgb(unsigned char,unsigned char,unsigned char,unsigned char)',
                    argtypes=[cpptypes.c_ubyte, cpptypes.c_ubyte, cpptypes.c_ubyte, cpptypes.c_ubyte],
                    restype = color),
    cpptypes.method('V2', 'CSimpleClass::V2()', virtual=True),
    cpptypes.method('Foo', 'CSimpleClass::Foo()', virtual=True, pure_virtual=True),
]

dll = cpptypes.AnyDLL(os.path.join(os.path.dirname(__file__), "mydll.dll"))
MySimpleClass._finish(dll)

################################################################

if __name__ == "__main__":
##    help(MySimpleClass)

    obj = MySimpleClass(42)
    print obj.value
    print "M1(4)"
    obj.M1(4)
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

    print obj.RGB(1, 2, 3, 4)
    print obj.rgb(1, 2, 3, 4)

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
