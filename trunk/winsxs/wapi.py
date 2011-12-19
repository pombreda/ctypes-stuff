# -*- coding: latin-1 -*-
"""Some windows api functions, data types, and constants."""
from __future__ import division, with_statement, absolute_import

from ctypes import *

_kernel32 = WinDLL("kernel32")

def nonnull(result, func, args):
    if result:
        return result
    raise WinError()

BOOL_errcheck = nonnull
HDC_errcheck = nonnull
HENHMETAFILE_errcheck = nonnull
HFONT_errcheck = nonnull

WSTRING = c_wchar_p
class tagACTCTXW(Structure):
    pass
ACTCTXW = tagACTCTXW
ULONG = c_ulong
DWORD = c_ulong
WCHAR = c_wchar
LPCWSTR = WSTRING
USHORT = c_ushort
WORD = c_ushort
LANGID = WORD
PVOID = c_void_p
HANDLE = PVOID
HINSTANCE = HANDLE
HMODULE = HINSTANCE
tagACTCTXW._fields_ = [
    ('cbSize', ULONG),
    ('dwFlags', DWORD),
    ('lpSource', LPCWSTR),
    ('wProcessorArchitecture', USHORT),
    ('wLangId', LANGID),
    ('lpAssemblyDirectory', LPCWSTR),
    ('lpResourceName', LPCWSTR),
    ('lpApplicationName', LPCWSTR),
    ('hModule', HMODULE),
]
PCACTCTXW = POINTER(ACTCTXW)
CreateActCtxW = _kernel32.CreateActCtxW
CreateActCtxW.restype = HANDLE
CreateActCtxW.argtypes = [PCACTCTXW]
ULONG_PTR = c_ulong
BOOL = c_int
ActivateActCtx = _kernel32.ActivateActCtx
ActivateActCtx.restype = BOOL
ActivateActCtx.argtypes = [HANDLE, POINTER(ULONG_PTR)]
ActivateActCtx.errcheck = BOOL_errcheck
DeactivateActCtx = _kernel32.DeactivateActCtx
DeactivateActCtx.restype = BOOL
DeactivateActCtx.argtypes = [DWORD, ULONG_PTR]
DeactivateActCtx.errcheck = BOOL_errcheck
BeginUpdateResourceW = _kernel32.BeginUpdateResourceW
BeginUpdateResourceW.restype = HANDLE
BeginUpdateResourceW.argtypes = [LPCWSTR, BOOL]
BeginUpdateResource = BeginUpdateResourceW # alias
EndUpdateResourceW = _kernel32.EndUpdateResourceW
EndUpdateResourceW.restype = BOOL
EndUpdateResourceW.argtypes = [HANDLE, BOOL]
EndUpdateResourceW.errcheck = BOOL_errcheck
EndUpdateResource = EndUpdateResourceW # alias
LPVOID = c_void_p
UpdateResourceW = _kernel32.UpdateResourceW
UpdateResourceW.restype = BOOL
UpdateResourceW.argtypes = [HANDLE, LPCWSTR, LPCWSTR, WORD, LPVOID, DWORD]
UpdateResourceW.errcheck = BOOL_errcheck
UpdateResource = UpdateResourceW # alias
RT_MANIFEST = 24 # Variable WSTRING
def MAKEINTRESOURCEW(i): return LPWSTR(i)
MAKEINTRESOURCE = MAKEINTRESOURCEW # alias
WSTRING = c_wchar_p
LPWSTR = WSTRING
def MAKELANGID(p,s): return (s << 10) | p
LANG_ENGLISH = 9 # Variable c_int
SUBLANG_ENGLISH_US = 1 # Variable c_int
ACTCTX_FLAG_RESOURCE_NAME_VALID = 8
