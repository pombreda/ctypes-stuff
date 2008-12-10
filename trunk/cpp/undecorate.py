import ctypes
_UnDecorateSymbolName = ctypes.windll.dbghelp.UnDecorateSymbolName
_UnDecorateSymbolName.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint]

UNDNAME_COMPLETE = 0
UNDNAME_NO_LEADING_UNDERSCORES = 1
UNDNAME_NO_MS_KEYWORDS = 2
UNDNAME_NO_FUNCTION_RETURNS = 4
UNDNAME_NO_ALLOCATION_MODEL = 8
UNDNAME_NO_ALLOCATION_LANGUAGE = 16
UNDNAME_NO_MS_THISTYPE = 32
UNDNAME_NO_CV_THISTYPE = 64
UNDNAME_NO_THISTYPE = 96
UNDNAME_NO_ACCESS_SPECIFIERS = 128
UNDNAME_NO_THROW_SIGNATURES = 256
UNDNAME_NO_MEMBER_TYPE = 512
UNDNAME_NO_RETURN_UDT_MODEL = 1024
UNDNAME_32_BIT_DECODE = 2048
UNDNAME_NAME_ONLY = 4096
UNDNAME_NO_ARGUMENTS = 8192
UNDNAME_NO_SPECIAL_SYMS = 16384


def symbol_name(name, flags=UNDNAME_COMPLETE):
    """
    Undecorates a decorated C++ symbol name.
    
    >>> symbol_name('?AfxGetResourceHandle@@YGPAUHINSTANCE__@@XZ')
    'struct HINSTANCE__ * __stdcall AfxGetResourceHandle(void)'
    >>>
    >>> symbol_name('?DEREncode@AsymmetricAlgorithm@CryptoPP@@QBEXAAVBufferedTransformation@2@@Z')
    'public: void __thiscall CryptoPP::AsymmetricAlgorithm::DEREncode(class CryptoPP::BufferedTransformation &)const '
    >>>
    """
    buf = ctypes.create_string_buffer(1000)
    res = _UnDecorateSymbolName(name,
                                buf,
                                ctypes.sizeof(buf),
                                flags)
    if res:
        return buf[:res]
    raise ctypes.WinError()

if __name__ == "__main__":
    import doctest; doctest.testmod()
