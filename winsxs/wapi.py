# -*- coding: latin-1 -*-
"""Some windows api functions, data types, and constants."""
from __future__ import division, with_statement, absolute_import

from ctypes import *

_kernel32 = WinDLL("kernel32")
_version = WinDLL("version")

def nonnull(result, func, args):
    if result:
        return result
    raise WinError()

BOOL_errcheck = nonnull
HDC_errcheck = nonnull
HENHMETAFILE_errcheck = nonnull
HFONT_errcheck = nonnull

_WIN64 = (sizeof(c_void_p) == 8)

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
if _WIN64:
    ULONG_PTR = c_ulonglong
else:
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
GetModuleFileNameW = _kernel32.GetModuleFileNameW
GetModuleFileNameW.restype = DWORD
GetModuleFileNameW.argtypes = [HMODULE, LPWSTR, DWORD]
GetModuleFileName = GetModuleFileNameW # alias
LoadLibraryA = _kernel32.LoadLibraryA
LoadLibraryA.restype = c_void_p
LoadLibraryA.argtypes = [c_char_p]
STRING = c_char_p
CHAR = c_char
LPSTR = STRING
GetModuleFileNameA = _kernel32.GetModuleFileNameA
GetModuleFileNameA.restype = DWORD
GetModuleFileNameA.argtypes = [HMODULE, LPSTR, DWORD]
STRING = c_char_p
HRSRC = HANDLE
LPCSTR = STRING
FindResourceA = _kernel32.FindResourceA
FindResourceA.restype = HRSRC
FindResourceA.argtypes = [HMODULE, LPCSTR, LPCSTR]
HGLOBAL = HANDLE
LoadResource = _kernel32.LoadResource
LoadResource.restype = HGLOBAL
LoadResource.argtypes = [HMODULE, HRSRC]
LoadResource.errcheck = nonnull
LockResource = _kernel32.LockResource
LockResource.restype = LPVOID
LockResource.argtypes = [HGLOBAL]
LockResource.errcheck = nonnull
SizeofResource = _kernel32.SizeofResource
SizeofResource.restype = DWORD
SizeofResource.argtypes = [HMODULE, HRSRC]
# GetFileVersionInfoSize = GetFileVersionInfoSizeW # alias
LPDWORD = POINTER(DWORD)
GetFileVersionInfoSizeA = _version.GetFileVersionInfoSizeA
GetFileVersionInfoSizeA.restype = DWORD
GetFileVersionInfoSizeA.argtypes = [LPCSTR, LPDWORD]
GetFileVersionInfoA = _version.GetFileVersionInfoA
GetFileVersionInfoA.restype = BOOL
GetFileVersionInfoA.argtypes = [LPCSTR, DWORD, DWORD, LPVOID]
GetFileVersionInfoA.errcheck = BOOL_errcheck
class tagVS_FIXEDFILEINFO(Structure):
    pass
VS_FIXEDFILEINFO = tagVS_FIXEDFILEINFO
tagVS_FIXEDFILEINFO._fields_ = [
    ('dwSignature', DWORD),
    ('dwStrucVersion', DWORD),
    ('dwFileVersionMS', DWORD),
    ('dwFileVersionLS', DWORD),
    ('dwProductVersionMS', DWORD),
    ('dwProductVersionLS', DWORD),
    ('dwFileFlagsMask', DWORD),
    ('dwFileFlags', DWORD),
    ('dwFileOS', DWORD),
    ('dwFileType', DWORD),
    ('dwFileSubtype', DWORD),
    ('dwFileDateMS', DWORD),
    ('dwFileDateLS', DWORD),
]
PUINT = POINTER(c_uint)
VerQueryValueA = _version.VerQueryValueA
VerQueryValueA.restype = BOOL
VerQueryValueA.argtypes = [LPVOID, LPSTR, POINTER(POINTER(VS_FIXEDFILEINFO)), PUINT]
VerQueryValueA.errcheck = BOOL_errcheck
