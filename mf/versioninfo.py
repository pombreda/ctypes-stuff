#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
import struct
import _wapi

WORD = struct.Struct("<H").pack
DWORD = struct.Struct("<I").pack

def pad32(text):
    """Pad to a 32-bit boundary"""
    delta = len(text) % 4
    if delta == 0:
        return text
    padding = b'\0' * (4 - delta)
    return text + padding

def pad32_2(text):
    """Pad to a 32-bit boundary + 16 bit"""
    delta = len(text) % 4
    if delta == 2:
        return text
    padding = b'\0' * ((2 - delta)%4)
    return text + padding

class VS_STRUCT(object):
    # 0: WORD length
    # 2: WORD valuelength - always 0
    # 4: WORD type = 1 (text data) or 0 (binary data)
    # 6: WCHAR[] key
    # WORD padding1
    # Value[] array of structures.
    def tobytes(self):
        result = pad32_2(WORD(self.valuelength) + WORD(self.valuetype) + self.key) + pad32(self.value)
        return pad32(WORD(len(result)+2) + result)

class VS_String(VS_STRUCT):
    valuetype = 1 # text data
    def __init__(self, key, text):
        self.key = (key + '\0').encode("utf-16-le")
        self.value = (text + '\0').encode("utf-16-le")
        self.valuelength = len(self.value)//2

class VS_StringTable(VS_STRUCT):
    valuelength = 0
    valuetype = 1 # text data
    def __init__(self, langid, *strings):
        self.key = langid.encode("utf-16-le")
        self.value = b''.join(strings)

class VS_StringFileInfo(VS_STRUCT):
    valuelength = 0
    valuetype = 1 # text data
    key = "StringFileInfo\0".encode("utf-16-le")
    def __init__(self, *stringtables):
        self.value = b''.join(stringtables)

class VS_VarFileInfo(VS_STRUCT):
    valuelength = 0
    valuetype = 1
    key = "VarFileInfo\0".encode("utf-16-le")
    def __init__(self, var):
        self.value = pad32(var)

class VS_Var(VS_STRUCT):
    valuetype = 0
    key = "Translation\0".encode("utf-16-le")
    def __init__(self, *langids):
        self.value = pad32(b''.join(DWORD(id) for id in langids))
        self.valuelength = len(self.value)

################################################################

def String(key, text):
    return VS_String(key, text).tobytes()

def StringTable(langid, *strings):
    return VS_StringTable(langid, *strings).tobytes()

def StringFileInfo(*stringtables):
    return VS_StringFileInfo(*stringtables)

def VarFileInfo(var):
    return VS_VarFileInfo(var)

def Var(*langids):
    return VS_Var(*langids).tobytes()

## class VS_VersionInfo(VS_STRUCT):
##     valuetype = 0
##     key = "VS_VERSION_INFO\0".encode("utf-16-le")
##     def __init__(self, ffi, *items):
##         item_bytes = b''.join(item.tobytes() for item in items)
##         self.value = pad32(memoryview(ffi).tobytes()) + item_bytes
##         self.valuelength = len(self.value)

## def VS_VERSIONINFO(ffi, *items):
##     return VS_VersionInfo(ffi, *items).tobytes()

def VS_VERSIONINFO(ffi, *items):
    # 0: WORD length
    # 2: WORD valuelength - length if VS_FIXEDFILEINFO
    # 4: WORD type = 0 (binary data)
    # 6: WCHAR[] key - "VS_VERSION_INFO"
    # WORD padding1
    # VS_FIXEDFILEINFO value
    # WORD padding2
    # WORD[] Children - array of StringFileInfo and/or VaFileInfo structures
    key = "VS_VERSION_INFO\0".encode("utf-16-le")
    vs_fixedfileinfo = memoryview(ffi).tobytes()
    value = pad32(vs_fixedfileinfo)

    result = pad32_2(WORD(len(value)) + WORD(0) + key) + value

    children = b''.join(x.tobytes() for x in items)

    result = pad32_2(result) + children
    result = WORD(len(result) + 2) + result
    return pad32(result)


################################################################

# testing

vs = VS_VERSIONINFO(
    _wapi.VS_FIXEDFILEINFO(
        dwSignature = 0xFEEF04BD,
        dwStrucVersion = 0x00010000,
        dwFileVersionMS = 0x00030003,
        dwFileVersionLS = 0x046103f5,
        dwProductVersionMS = 0x00030003,
        dwProductVersionLS = 0x046103f5,
        dwFileFlagsMask = 0x3F,
        dwFileFlags = 0,
        dwFileOS = _wapi.VOS_NT_WINDOWS32,
        dwFileType = _wapi.VFT_APP,
        dwFileSubtype = 0,
        dwFileDateMS = 0,
        dwFileDateLS = 0,
        ),
    StringFileInfo(StringTable("000004b0",
                               String("CompanyName", "Python Software Foundation"),
                               String("FileDescription", "Python Core"),
                               String("FileVersion", "3.3.1rc1"),
                               String("InternalName", "Python DLL"),
                               String("LegalCopyright",
                                      "Copyright © 2001-2012 Python Software Foundation. "
                                      "Copyright © 2000 BeOpen.com. Copyright © 1995-2001 CNRI. "
                                      "Copyright © 1991-1995 SMC."),
                               String("OriginalFilename", "python33.dll"),
                               String("ProductName", "Python"),
                               String("ProductVersion", "3.3.1rc1"),
                               )),
    VarFileInfo(Var(0x04b00000)),
                    )

##vs = VS_VERSIONINFO()

# DOES IT WORK NOW?

# This is still not correct:
# VrFileInfo does nor work
# see tooltip in explorer window
# or Open version resource a binary and compare with that in Python33.dll...
