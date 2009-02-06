from cpptypes import _imagehlp

from _imagehlp import (UNDNAME_COMPLETE,
                       UNDNAME_NO_LEADING_UNDERSCORES,
                       UNDNAME_NO_MS_KEYWORDS,
                       UNDNAME_NO_FUNCTION_RETURNS,
                       UNDNAME_NO_ALLOCATION_MODEL,
                       UNDNAME_NO_ALLOCATION_LANGUAGE,
                       UNDNAME_NO_MS_THISTYPE,
                       UNDNAME_NO_CV_THISTYPE,
                       UNDNAME_NO_THISTYPE,
                       UNDNAME_NO_ACCESS_SPECIFIERS,
                       UNDNAME_NO_THROW_SIGNATURES,
                       UNDNAME_NO_MEMBER_TYPE,
                       UNDNAME_NO_RETURN_UDT_MODEL,
                       UNDNAME_32_BIT_DECODE,
                       UNDNAME_NAME_ONLY,
                       UNDNAME_NO_ARGUMENTS,
                       UNDNAME_NO_SPECIAL_SYMS)


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
    buf = _imagehlp.create_string_buffer(1000)
    res = _imagehlp.UnDecorateSymbolName(name,
                                         buf,
                                         _imagehlp.sizeof(buf),
                                         flags)
    if res:
        return buf[:res]
    raise _imagehlp.WinError()

def read_export_table(base):
    """An image file is mapped into memory at address 'base'.
    Read the export table and return a list of exported symbols.

    This example prints the first exported function names of the python dll:
    
    >>> import sys, pprint
    >>> read_export_table(sys.dllhandle)[:4]
    ['PyArg_Parse', 'PyArg_ParseTuple', 'PyArg_ParseTupleAndKeywords', 'PyArg_UnpackTuple']
    >>>
    """
    size = _imagehlp.c_ulong()
    ptr = _imagehlp.ImageDirectoryEntryToData(base,
                                              True, # MappedAsImage
                                              _imagehlp.IMAGE_DIRECTORY_ENTRY_EXPORT, # Index into Directory Entry
                                              size
                                              )
    export_dir = _imagehlp.IMAGE_EXPORT_DIRECTORY.from_address(ptr)
    pnt_headers = _imagehlp.ImageNtHeader(base)

    def rva2va(rva):
        # The image contains Relative Virtual Addresses, while we must
        # use Virtual Addresses in the mapped file.  This function
        # converts RVA to VA.
        return _imagehlp.ImageRvaToVa(pnt_headers, base, rva, None)

##    def dump(s):
##        print s
##        for name, typ in s._fields_:
##            print name, getattr(s, name)

##    dump(export_dir)
##    dump(pnt_headers[0])
    # export_dir.AddressOfNames is the RVA of an array. Each entry in the
    # array is an RVA pointing to an ASCIIZ string containing the export
    # name.  The array is lexically sorted to allow binary search.
    va_ptr = rva2va(export_dir.AddressOfNames)
    result = []
    for i in range(export_dir.NumberOfNames):
        rva = _imagehlp.c_int.from_address(va_ptr + _imagehlp.sizeof(_imagehlp.c_void_p) * i).value
        va = rva2va(rva)
        result.append(_imagehlp.string_at(va))
    return result

def get_exports(path):
    """Load an image file (exe or dll) into memory and return a list
    of exported symbols.

    >>> import _ctypes
    >>> get_exports(_ctypes.__file__)
    ['DllCanUnloadNow', 'DllGetClassObject', 'init_ctypes']
    >>>
    """
    loaded = _imagehlp.LOADED_IMAGE()
    _imagehlp.MapAndLoad(path, # ImageName
                         None, # DllPath
                         loaded,
                         False, # DotDll
                         True # ReadOnly
                         )
    try:
        return read_export_table(loaded.MappedAddress)
    finally:
        _imagehlp.UnMapAndLoad(loaded)

if __name__ == "__main__":
    import doctest
    doctest.testmod()

