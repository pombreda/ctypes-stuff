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
