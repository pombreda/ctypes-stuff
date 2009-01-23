from cpptypes import *

mydll = CPPDLL("mydll.dll")

################################################################
if __debug__:
    from ctypeslib.dynamic_module import include
    include('''
    #include "mydll.h"
    ''',
            compilerflags=["-I."],
            persist=True)

################################################################
# everything below this line is autogenerated on demand, by the
# ctypeslib code generator (you need the ctypeslib-cpp branch for
# that):
STRING = c_char_p
class CSimpleClass(Class):
    pass
CSimpleClass._methods_ = [
    method('__cpp_constructor__', 'CSimpleClass::CSimpleClass(CSimpleClass const&)', argtypes=[POINTER(CSimpleClass)]),
    method('__cpp_constructor__', 'CSimpleClass::CSimpleClass(int)', argtypes=[c_int]),
    method('__cpp_destructor__', 'CSimpleClass::~CSimpleClass()'),
    method('M1', 'CSimpleClass::M1()'),
    method('M1', 'CSimpleClass::M1(int)', argtypes=[c_int]),
    method('V0', 'CSimpleClass::V0()', virtual=True),
    method('V1', 'CSimpleClass::V1(int)', argtypes=[c_int], virtual=True),
    method('V1', 'CSimpleClass::V1()', virtual=True),
    method('V1', 'CSimpleClass::V1(char*)', argtypes=[STRING], virtual=True),
    method('V1', 'CSimpleClass::V1(int, char*)', argtypes=[c_int, STRING], virtual=True),
    method('V1', 'CSimpleClass::V1(char*, int)', argtypes=[STRING, c_int], virtual=True),
    method('V2', 'CSimpleClass::V2()', virtual=True),
]
CSimpleClass._cpp_fields_ = [
    ('vtable', c_void_p),
    ('value', c_int),
]
CSimpleClass._finish(mydll)
assert sizeof(CSimpleClass) == 8, sizeof(CSimpleClass)
assert alignment(CSimpleClass) == 4, alignment(CSimpleClass)