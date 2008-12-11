import re
from ctypes import *
import get_exports
import undecorate

class public(object):
    """A decorator that loads member functions from a dll.

    Must be called with the C++ member signature.  The decorated
    function itself is ignored completely."""
    def __init__(self, dll, name):
        classname = re.search(r"\w+::", name).group()[:-2]
        decorated_name = member_names[name]
        self.func = getattr(dll, decorated_name)
        # XXX We should parse the member name, and determine restype and
        # argtypes from it somehow. gccxml?
        #
        # Detect member functions returning void or nothing (like
        # constructor), and set restype to None at least.
        if name.startswith("void") or name.startswith("%s::" % classname):
            self.func.restype = None

    def __call__(self, f):
        # XXX What should be the role of 'f'?
        member = self.func
        def wrapper(self, *args):
            return member(byref(self), *args)
        return wrapper

# XXX make a registry of names keyed by the dll...
member_names = {}
flags = undecorate.UNDNAME_NO_MS_KEYWORDS | undecorate.UNDNAME_NO_ACCESS_SPECIFIERS
for name in get_exports.read_export_table("mydll.dll"):
    name_with_args = undecorate.symbol_name(name, flags).strip()
##    print name, "=>\n\t", undecorate.symbol_name(name)
    member_names[name_with_args] = name


dll = CPPDLL("mydll.dll")


class CSimpleClass(Structure):
    _fields_ = [("_vtable", POINTER(c_void_p)),
                ("value", c_int)]

    @public(dll, "CSimpleClass::CSimpleClass(int)")
    def __init__(self, value):
        pass
    # Since the decorated functions itself have NO purpose at all
    # except that they provide the name, would it be better to write
    # something like this instead:
    # __init__ = public(dll,"CSimpleClass::CSimpleClass(int)")(None)
    #
    # Anyway: all this code should ideally be autogenerated.

    @public(dll, "void CSimpleClass::M1(void)")
    def M1(self):
        pass

    @public(dll, "virtual void CSimpleClass::V1(int)")
    def V1(self):
        pass

    @public(dll, "virtual void CSimpleClass::V0(void)")
    def V0(self):
        pass

    @public(dll, "CSimpleClass::~CSimpleClass(void)")
    def __del__(self):
        pass

def main():
    obj = CSimpleClass(42)
    print obj.value
    print hex(obj._vtable[0])
    obj.M1()
    obj.V1(99)

if __name__ == "__main__":
    main()
