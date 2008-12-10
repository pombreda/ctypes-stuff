from ctypes import *

import get_exports
import undecorate

for name in get_exports.read_export_table("mydll.dll"):
    print name, "=>", undecorate.symbol_name(name)

dll = CPPDLL("mydll.dll")

class CSimpleClass(Structure):
    _fields_ = [("_vtable", POINTER(c_void_p)),
                ("value", c_int)]

    def __init__(self, value):
        constructor(self, value)

    def M1(self):
        M1(self)

    def __del__(self):
        destructor(self)

    def getit(self):
        return getit(self)

constructor = getattr(dll, "??0CSimpleClass@@QAE@H@Z") # public: __thiscall CSimpleClass::CSimpleClass(int)
constructor.argtypes = [POINTER(CSimpleClass), c_int]

destructor = getattr(dll, "??1CSimpleClass@@QAE@XZ") # public: __thiscall CSimpleClass::~CSimpleClass(void)
destructor.argtypes = [POINTER(CSimpleClass)]

M1 = getattr(dll, "?M1@CSimpleClass@@QAEXXZ") # public: void __thiscall CSimpleClass::M1(void)
M1.argtypes = [POINTER(CSimpleClass)]

if __name__ == "__main__":
    obj = CSimpleClass(42)
    print obj.value
    print hex(obj._vtable[0])
    obj.M1()
