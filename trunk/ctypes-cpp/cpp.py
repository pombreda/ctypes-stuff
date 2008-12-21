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

dll = CPPDLL("mydll.dll")

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

class bound_virtual(object):
    def __init__(self, instance, proto, offset):
        self.im_proto = proto
        self.im_self = instance
        self.offset = offset

    def __call__(self, *args):
        addr = self.im_self._vtable[self.offset]
        return self.im_proto(addr)(byref(self.im_self), *args)

class virtual(object):
    def __init__(self, dll, vtbl_offset, name,
                 restype, argtypes):
        self.proto = CPPMETHODTYPE(restype, c_void_p, *argtypes)
        self.vtbl_offset = vtbl_offset

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return bound_virtual(instance, self.proto, self.vtbl_offset)

class CSimpleClass(Structure):
    _fields_ = [("_vtable", POINTER(c_void_p)),
                ("value", c_int)]

    __init__ = method(dll, "CSimpleClass::CSimpleClass(int)",
                      None, [c_int])

    __del__ = method(dll, "CSimpleClass::~CSimpleClass(void)",
                     None, [])

    M1 = method(dll, "void CSimpleClass::M1(void)",
                None, [])

    V0 = virtual(dll, 0, "virtual void CSimpleClass::V0(void)",
                 None, [])
    V1 = virtual(dll, 1, "virtual void CSimpleClass::V1(int)",
                 None, [c_int])
    V2 = virtual(dll, 2, "virtual void CSimpleClass::V2(void)",
                 None, [])

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
