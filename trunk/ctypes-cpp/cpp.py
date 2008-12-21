import sys
import get_exports
import undecorate
from ctypes import *

# XXX This should be in Lib\ctypes\__init__.py
_cpp_methodtype_cache = {}
def CPPMETHODTYPE(restype, *argtypes):
    from _ctypes import CFuncPtr, FUNCFLAG_THIS
    try:
        return _cpp_methodtype_cache[(restype, argtypes)]
    except KeyError:
        class CppMethodType(CFuncPtr):
            _argtypes_ = argtypes
            _restype_ = restype
            _flags_ = FUNCFLAG_THIS
        _cpp_methodtype_cache[(restype, argtypes)] = CppMethodType
        return CppMethodType


# XXX make a registry of names keyed by the dll...
member_names = {}
flags = undecorate.UNDNAME_NO_MS_KEYWORDS | undecorate.UNDNAME_NO_ACCESS_SPECIFIERS
for name in get_exports.read_export_table("mydll.dll"):
    name_with_args = undecorate.symbol_name(name, flags).strip()
##    print name, "=>\n\t", undecorate.symbol_name(name)
    member_names[name_with_args] = name

class bound_method(object):
    def __init__(self, instance, func):
        self.im_func = func
        self.im_self = instance

    def __call__(self, *args):
        return self.im_func(byref(self.im_self), *args)

class method(object):
    def __init__(self, dll, name,
                 restype, argtypes):
        self.func = getattr(dll, member_names[name])
        self.func.restype = restype
        self.func.argtypes = [c_void_p] + list(argtypes)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return bound_method(instance, self.func)

dll = CPPDLL("mydll.dll")

class CSimpleClass(Structure):
    # non-virtual methods
    __init__ = method(dll, "CSimpleClass::CSimpleClass(int)",
                      None, [c_int])

    __del__ = method(dll, "CSimpleClass::~CSimpleClass(void)",
                     None, [])

    M1 = method(dll, "void CSimpleClass::M1(void)",
                None, [])

    # virtual methods
    def V0(self):
        return self._vtable[0].V0(self)

    def V1(self, *args):
        return self._vtable[0].V1(self, *args)

    def V2(self):
        return self._vtable[0].V2(self)

class vtable(Structure):
    _fields_ = [("V0", CPPMETHODTYPE(None, POINTER(CSimpleClass))),
                ("V1", CPPMETHODTYPE(None, POINTER(CSimpleClass), c_int)),
                ("V2", CPPMETHODTYPE(None, POINTER(CSimpleClass)))]

CSimpleClass. _fields_ = [("_vtable", POINTER(vtable)),
                          ("value", c_int)]

def main():
    obj = CSimpleClass(42)
    print "obj.value:", obj.value
    print "----- call M1 -----"
    obj.M1()
    print "----- call V1(99) -----"
    obj.V0()
    obj.V1(99)
    obj.V2()
    print "-----  done   -----"

if __name__ == "__main__":
    main()
