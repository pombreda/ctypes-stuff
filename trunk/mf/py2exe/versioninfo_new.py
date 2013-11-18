#!/usr/bin/python3.3
# -*- coding: utf-8 -*-
import struct
from . import _wapi

raise RuntimeError("XXX This does not work correctly...")

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

# See the Microsoft documentation about 'Version Information Reference'.

class VS_STRUCT(object):
    valuelength = 0
    valuetype = 1 # text data
    # 0: WORD length
    # 2: WORD valuelength - length of data field or zero.
    # 4: WORD type = 1 (text data) or 0 (binary data)
    # 6: WCHAR[] key
    # WORD padding1
    # Value[] array of structures.
    # optional:
    # WORD padding2
    # Data[] array of other structures (only for VS_VersionInfo
    def tobytes(self):
        result = pad32_2(WORD(self.valuelength)
                         + WORD(self.valuetype)
                         + self.key
                         ) + pad32(self.value)
        return pad32(WORD(len(result)+2) + result)

class VS_String(VS_STRUCT):
    def __init__(self, key, text):
        self.key = (key + '\0').encode("utf-16-le")
        self.value = (text + '\0').encode("utf-16-le")
        self.valuelength = len(self.value)//2 # this length is in WORDS!

class VS_StringTable(VS_STRUCT):
    def __init__(self, langid, *strings):
        self.key = langid.encode("utf-16-le")
        self.value = b''.join(s.tobytes() for s in strings)

class VS_StringFileInfo(VS_STRUCT):
    key = "StringFileInfo\0".encode("utf-16-le")
    def __init__(self, *stringtables):
        self.value = b''.join(t.tobytes() for t in stringtables)

class VS_VarFileInfo(VS_STRUCT):
    key = "VarFileInfo\0".encode("utf-16-le")
    def __init__(self, var):
        self.value = pad32(var.tobytes())

class VS_Var(VS_STRUCT):
    valuetype = 0
    key = "Translation\0".encode("utf-16-le")
    def __init__(self, *langids):
        self.value = pad32(b''.join(DWORD(id) for id in langids))
        self.valuelength = len(self.value)

class VS_VersionInfo(VS_STRUCT):
    valuetype = 0
    key = "VS_VERSION_INFO\0".encode("utf-16-le")
    def __init__(self, ffi, *items):
        item_bytes = b''.join(item.tobytes() for item in items)
        value = pad32(memoryview(ffi).tobytes())
        self.valuelength = len(value)
        self.value = value + item_bytes

class Version(object):
    def __init__(self,
                 version,
                 comments = None,
                 company_name = None,
                 file_description = None,
                 internal_name = None,
                 legal_copyright = None,
                 legal_trademarks = None,
                 original_filename = None,
                 private_build = None,
                 product_name = None,
                 product_version = None,
                 special_build = None):
        self.version = version
        self.product_version = version or product_version
        strings = []
        strings.append(("FileVersion", version))
        if comments is not None:
            strings.append(("Comments", comments))
        if company_name is not None:
            strings.append(("CompanyName", company_name))
        if file_description is not None:
            strings.append(("FileDescription", file_description))
        strings.append(("FileVersion", version))
        if internal_name is not None:
            strings.append(("InternalName", internal_name))
        if legal_copyright is not None:
            strings.append(("LegalCopyright", legal_copyright))
        if legal_trademarks is not None:
            strings.append(("LegalTrademarks", legal_trademarks))
        if original_filename is not None:
            strings.append(("OriginalFilename", original_filename))
        if private_build is not None:
            strings.append(("PrivateBuild", private_build))
        if product_name is not None:
            strings.append(("ProductName", product_name))
        strings.append(("ProductVersion", product_version or version))
        if special_build is not None:
            strings.append(("SpecialBuild", special_build))
        self.strings = strings
        
    def _parse_version(self, version):
        version = version.replace(",", ".")
        fields = [f.strip()
                  for f in (version + '.0.0.0.0').split(".")[:4]]
        try:
            MS = int(fields[0]) * 65536 + int(fields[1])
            LS = int(fields[2]) * 65536 + int(fields[3])
            return MS, LS
        except ValueError:
            raise VersionError("could not parse version number '%s'" % version)

    def tobytes(self):
        dwFileVersionMS, dwFileVersionLS = self._parse_version(self.version)
        dwProductVersionMS, dwProductVersionLS = self._parse_version(self.product_version)
        vs = VS_VersionInfo(
            _wapi.VS_FIXEDFILEINFO(
                dwSignature = 0xFEEF04BD,
                dwStrucVersion = 0x00010000,
                dwFileVersionMS = dwFileVersionMS,
                dwFileVersionLS = dwFileVersionLS,
                dwProductVersionMS = dwProductVersionMS,
                dwProductVersionLS = dwProductVersionLS,
                dwFileFlagsMask = 0x3F,
                dwFileOS = _wapi.VOS_NT_WINDOWS32,
                dwFileType = _wapi.VFT_APP,
                ),
            VS_StringFileInfo(
                VS_StringTable("000004b0",
                               *[VS_String(name, value) for (name, value) in self.strings]),
                VS_VarFileInfo(VS_Var(0x04b00000))))
        
        return vs.tobytes()

################################################################

# testing

if __name__ == "__main__":
    vs = VS_VersionInfo(
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
        VS_StringFileInfo(VS_StringTable("000004b0",
                                         VS_String("CompanyName", "Python Software Foundation"),
                                         VS_String("FileDescription", "Python Core"),
                                         VS_String("FileVersion", "3.3.1rc1"),
                                         VS_String("InternalName", "Python DLL"),
                                         VS_String("LegalCopyright",
                                                   "Copyright © 2001-2012 Python Software Foundation. "
                                                   "Copyright © 2000 BeOpen.com. Copyright © 1995-2001 CNRI. "
                                                   "Copyright © 1991-1995 SMC."),
                                         VS_String("OriginalFilename", "python33.dll"),
                                         VS_String("ProductName", "Python"),
                                         VS_String("ProductVersion", "3.3.1rc1"),
                                         )),
        VS_VarFileInfo(VS_Var(0x04b00000))).tobytes()
