import sys
import ctypes, ctypes.util

DWORD = ctypes.c_uint32
HANDLE = ctypes.c_uint32
HRESULT = ctypes.c_int32
BOOL = ctypes.c_short

################################################################

def errcheck(result, func, arguments):
    if result == 0:
        raise OSError(rapi.CeRapiGetError() or \
                      rapi.CeGetLastError())
    return result

if sys.platform == "win32":
    rapi = ctypes.windll.rapi

    class RAPIINIT(ctypes.Structure):
        _fields_ = [("cbSize", DWORD),
                    ("heRapiInit", HANDLE),
                    ("hrRapiInit", HRESULT)]
        def __init__(self):
            self.cbSize = ctypes.sizeof(self)

    def Init(timeout=5000):
        rapiinit = RAPIINIT()
        ctypes.oledll.rapi.CeRapiInitEx(ctypes.byref(rapiinit))
        # Wait for connection (with timeout)
        result = ctypes.windll.kernel32.WaitForSingleObject(rapiinit.heRapiInit, timeout)
        if result == WAIT_TIMEOUT:
            raise ConnectError("connection timeout")
        elif result == WAIT_ABANDONED:
            raise ConnectError("connection abandoned")
else:
    rapi_lib = ctypes.util.find_library("rapi")
    rapi = ctypes.CDLL(rapi_lib)
    rapi.synce_log_set_level(0)
    rapi.synce_strerror.restype = ctypes.c_char_p
    def WinError(hr):
        raise OSError(hr, rapi.synce_strerror(hr))

    def Init(timeout=5000):
        hr = rapi.CeRapiInit()
        if hr & 0x80000000:
            raise WinError(hr)


class widestring(object):
    @classmethod
    def from_param(cls, value):
        if value is None:
            return None
        return value.encode("utf-16")[2:] + "\0\0"

rapi.CeCreateFile.errcheck = errcheck
rapi.CeCreateFile.argtypes = widestring, DWORD, DWORD, ctypes.c_void_p, DWORD, DWORD, HANDLE

rapi.CeWriteFile.errcheck = errcheck

rapi.CeCloseHandle.errcheck = errcheck

rapi.CeDeleteFile.errcheck = errcheck
rapi.CeDeleteFile.argtypes = widestring,

rapi.CeCreateProcess.errcheck = errcheck
rapi.CeCreateProcess.argtypes = (widestring, widestring,
                                 ctypes.c_void_p, ctypes.c_void_p,
                                 BOOL, DWORD,
                                 ctypes.c_void_p, ctypes.c_void_p,
                                 ctypes.c_void_p, ctypes.c_void_p)

rapi.CeRapiInit.restype = HRESULT

class ConnectError(Exception):
    pass

# Windows api constants (instead of including win32con)
WAIT_TIMEOUT = 258
WAIT_ABANDONED = 128
GENERIC_WRITE = 1073741824
CREATE_ALWAYS = 2

################################################################

#####################################################################
# getSpecialFolderPath

rapi.CeGetSpecialFolderPath.errcheck = errcheck
rapi.CeGetSpecialFolderPath.argtypes = (ctypes.c_int, DWORD, ctypes.c_void_p);

def GetSpecialFolderPath(folderid):
    # We pass a CHAR buffer, but CeGetSpecialFolderPath expects a
    # WCHAR buffer.
    buf = ctypes.create_string_buffer(128*2)
    size = rapi.CeGetSpecialFolderPath(folderid, 128, buf)
    return buf[:2*size].decode('utf-16')

CSIDL_PROGRAMS=           0x0002
CSIDL_PERSONAL=           0x0005
CSIDL_FAVORITES_GRYPHON=  0x0006
CSIDL_STARTUP=            0x0007
CSIDL_RECENT=             0x0008
CSIDL_STARTMENU  =        0x000b
CSIDL_DESKTOPDIRECTORY=   0x0010
CSIDL_FONTS=              0x0014
CSIDL_FAVORITES=          0x0016

CSIDL_PROGRAM_FILES=      0x0026

################################################################
# Error codes from Synce project (librapi2/src/rapi_types.h)

ERROR_SUCCESS = 0
ERROR_FILE_NOT_FOUND = 2
ERROR_NOT_ENOUGH_MEMORY = 8
ERROR_SEEK = 25
ERROR_INVALID_PARAMETER = 87
ERROR_INSUFFICIENT_BUFFER    = 122
ERROR_NO_DATA = 232
ERROR_NO_MORE_ITEMS = 259
ERROR_KEY_DELETED    = 1018

################################################################

def WriteFile(pathname, data):
    # copy a local file to remote system via rapi calls
    handle = rapi.CeCreateFile(pathname,
                               GENERIC_WRITE,
                               0,
                               0,
                               CREATE_ALWAYS,
                               0,
                               0)
    written = DWORD()
    rapi.CeWriteFile(handle,
                     data,
                     len(data),
                     ctypes.byref(written),
                     None)
    rapi.CeCloseHandle(handle)
    assert written.value == len(data)

def CreateProcess(exepath, args):
    # start the a remote process
    rapi.CeCreateProcess(exepath,
                         args,
                         0, 0,
                         False, 0, 0, 0,
                         0, 0)

def DeleteFile(path):
    rapi.CeDeleteFile(path)
