from ctypes import *

class CPPDLL(CPPDLL):
    """This class represents a dll exporting functions using the
    Windows __thiscall calling convention.

    Functions can be accessed as attributes, using the mangled or the
    demangled name.
    """
    # XXX Should we allow unnormalized, demangled name?  Should we try
    # to read function addresses from a map file?

    def __init__(self, path, *args, **kw):
        import get_exports
        function_names = get_exports.read_export_table(path)
        self._names_map = {}
        for mangled in function_names:
            demangled = self.normalize(self.undecorate(mangled))
            self._names_map[demangled] = mangled
        super(CPPDLL, self).__init__(path, *args, **kw)

    def undecorate(self, name):
        import undecorate
        flags = undecorate.UNDNAME_NO_MS_KEYWORDS \
                | undecorate.UNDNAME_NO_ACCESS_SPECIFIERS
        return undecorate.symbol_name(name, flags)

    def normalize(self, name):
        # Remove the return type from function prototypes.  Types from
        # variable declaration are not removed.
        #
        # Does not work for templates, the regexp would be much more
        # complicated.
        name = name.strip()
        if name.endswith("const"):
            name = name[:-len("const")]
        name = name.replace(", ", ",")
        name = name.replace("(void)", "()")
        name = name.replace(" &", "&")
        name = name.replace(" *", "*")
        name = name.replace("class ", "")
        name = name.replace("struct ", "")
        name = name.strip()
        if "(" in name:
            import re
            m = re.search(r"([a-zA-Z]\w*::)?~?[a-zA-Z]\w*\(.*\)$", name)
            if m:
                return m.group(0)
        return name

    def __getattr__(self, name):
        """This method allows to access functions by mangled name
        and by unmangled normalized name."""
        try:
            # try mangled name
            result = super(CPPDLL, self).__getattr__(name)
            # XXX Should also try to find and cache with the demangled
            # name, but this is only for performance...
        except AttributeError:
            # try demangled name
            try:
                demangled = self._names_map[name]
            except KeyError:
                name = self.normalize(name)
                demangled = self._names_map[name]
            result = super(CPPDLL, self).__getattr__(demangled)
            setattr(self, demangled, result)
        setattr(self, name, result)
        return result

if __name__ == "__main__":
    dll = CPPDLL("mydll.dll")
    print dll
    print getattr(dll, "??0CSimpleClass@@QAE@ABV0@@Z")
    print getattr(dll, "??0CSimpleClass@@QAE@H@Z")
    print getattr(dll, "CSimpleClass::CSimpleClass(int)")
    print getattr(dll, "CSimpleClass::CSimpleClass(int)")
    print getattr(dll, "CSimpleClass::~CSimpleClass()")

    class X(Structure):
        _fields_ = [("allocate some space", c_int * 32)]
        def __init__(self, value):
            func = getattr(dll, "CSimpleClass::CSimpleClass(int)")
            func(byref(self), value)

        def __del__(self):
            func = getattr(dll, "CSimpleClass::~CSimpleClass()")
            func(byref(self))
            
    x = X(42)
    del x
