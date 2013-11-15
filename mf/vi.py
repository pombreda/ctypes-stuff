#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
import struct

def WORD(i):
    return struct.pack("<H", i)

def DWORD(i):
    return struct.pack("<L", i)

def pad32(text):
    """Pad to a 32-bit boundary"""
    delta = len(text) % 4
    if not delta:
        return text
    print("DELTA", delta, text.decode("utf-16-le"))
    padding = b'\0' * (4 - delta)
    result = text + padding
    assert len(result)%4 == 0
    return result

def pad32_2(text):
    """Pad to a 32-bit boundary + 16 bit"""
    delta = len(text) % 4
    if delta == 2:
        return text
    padding = b'\0' * ((2 - delta)%4)
    result = text + padding
    assert len(result)%4 == 2
    return result

def String(key, text):
    # 0: WORD length
    # 2: WORD valuelength
    # 4: WORD type = 1 (text data)
    # 6: WCHAR[] key
    # WORD padding1
    # WCHAR[] value - zero terminated string
    # WORD padding2
    key = (key + '\0').encode("utf-16-le")
    text = (text + '\0').encode("utf-16-le")
    text = pad32(text)
    result = pad32_2(WORD(len(text)) + WORD(1) + key) + text
    result = WORD(len(result)) + result
    return pad32(result)

def StringTable(langid, *strings):
    # 0: WORD length
    # 2: WORD valuelength - always 0
    # 4: WORD type = 1 (text data)
    # 6: WCHAR[] key - 8-digit hex number, the language ID
    # WORD padding1
    # String[] Children array of String structures.
    key = langid.encode("utf-16-le")
    padding = b"\0" * ((6 + len(key)) % 4) # align to 32-bit boundary
    result = WORD(0) + WORD(1) + key + padding + b''.join(strings)
    return WORD(len(result)) + result

def StringFileInfo(*stringtables):
    # 0: WORD length
    # 2: WORD valuelength - always 0
    # 4: WORD type = 1 (text data)
    # 6: WCHAR[] key - "StringFileInfo"
    # WORD padding1
    # StringTable[] Children
    key = "StringFileInfo".encode("utf-16-le")
    padding = b"\0" * ((6 + len(key)) % 4) # align to 32-bit boundary
    result = WORD(0) + WORD(1) + key + padding + b''.join(stringtables)
    return WORD(len(result)) + result

def VarFileInfo(var):
    # 0: WORD length
    # 2: WORD valuelength - always 0
    # 4: WORD type = 1 (text data)
    # 6: WCHAR[] key - "VarFileInfo"
    # WORD padding1
    # Var[] Children
    key = "VarFileInfo\0".encode("utf-16-le")
    padding = b"\0" * ((6 + len(key)) % 4) # align to 32-bit boundary
    result = WORD(0) + WORD(1) + key + padding + var
    return WORD(len(result)) + result

def Var(*langids):
    # 0: WORD length
    # 2: WORD valuelength - length in bytes of Value member
    # 4: WORD type = 0 (binary data)
    # 6: WCHAR[] key - "Translation"
    # WORD padding1
    # DWORD[] Value - array of langid/codepage identifiers
    key = "Translation\0".encode("utf-16-le")
    padding = b"\0" * ((6 + len(key)) % 4) # align to 32-bit boundary
    values = b''.join([DWORD(id) for id in langids])
    result = WORD(len(values)) + WORD(0) + key + padding + values
    return WORD(len(result)) + result
    

def VS_VERSIONINFO(*items):
    # 0: WORD length
    # 2: WORD valuelength - length if VS_FIXEDFILEINFO
    # 4: WORD type = 0 (binary data)
    # 6: WCHAR[] key - "VS_VERSION_INFO"
    # WORD padding1
    # VS_FIXEDFILEINFO value
    # WORD padding2
    # WORD[] Children - array of StringFileInfo and/or VaFileInfo structures
    # StringTable[] Children
    key = "VS_VERSION_INFO\0".encode("utf-16-le")
    padding1 = b"\0" * ((6 + len(key)) % 4) # align to 32-bit boundary
    import _wapi
    ffi = _wapi.VS_FIXEDFILEINFO(
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
        )
    vs_fixedfileinfo = memoryview(ffi).tobytes()
    part1 = WORD(len(vs_fixedfileinfo)) + WORD(0) + key + padding1 + vs_fixedfileinfo
    padding2 = b"\0" * ((6 + len(part1)) % 4) # align to 32-bit boundary
    result = part1 + padding2 + b''.join(items)
    return WORD(len(result)) + result

# XXX NEED VarFileInfo with 0x000004b0

vs = VS_VERSIONINFO(StringFileInfo(StringTable("000004b0",
                                               String("CompanyName", "Python Software Foundation"),
                                               String("FileDescription", "Python Core"),
                                               String("FileVersion", "3.3.1rc1"),
                                               String("InternalName", "Python DLL"),
                                               String("LegalCopyright",
                                                      "Copyright © 2001-2012 Python Software Foundation. Copyright © 2000 BeOpen.com. Copyright © 1995-2001 CNRI. Copyright © 1991-1995 SMC."),
                                               String("OriginalFilename", "python33.dll"),
                                               String("ProductName", "Python"),
                                               String("ProductVersion", "3.3.1rc1"),
                                               )),
##                    VarFileInfo(Var(0x04b00000)),
                    )

##vs = VS_VERSIONINFO()

# This is still not correct:
# VrFileInfo does nor work
# see tooltip in explorer window
# or Open version resource a binary and compare with that in Python33.dll...
