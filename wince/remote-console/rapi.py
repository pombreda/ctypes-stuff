import ctypes, ctypes.wintypes

################################################################
class RAPIINIT(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.wintypes.DWORD),
                ("heRapiInit", ctypes.wintypes.HANDLE),
                ("hrRapiInit", ctypes.HRESULT)]
    def __init__(self):
        self.cbSize = ctypes.sizeof(self)

def errcheck(result, func, arguments):
    if result == 0:
        raise ctypes.WinError(ctypes.windll.rapi.CeRapiGetError() or \
                              ctypes.windll.rapi.CeGetLastError())
    return result

ctypes.windll.rapi.CeCreateFile.errcheck = errcheck
ctypes.windll.rapi.CeWriteFile.errcheck = errcheck
ctypes.windll.rapi.CeCloseHandle.errcheck = errcheck
ctypes.windll.rapi.CeDeleteFile.errcheck = errcheck
ctypes.windll.rapi.CeCreateProcess.errcheck = errcheck

class ConnectError(Exception):
    pass

# Windows api constants (instead of including win32con)
WAIT_TIMEOUT = 258
WAIT_ABANDONED = 128
GENERIC_WRITE = 1073741824
CREATE_ALWAYS = 2

def WFSO_errcheck(result, func, arguments):
    if result == WAIT_TIMEOUT:
        raise ConnectError("connection timeout")
    elif result == WAIT_ABANDONED:
        raise ConnectError("connection abandoned")
    
ctypes.windll.kernel32.WaitForSingleObject.errcheck = WFSO_errcheck

################################################################

def Init(timeout=5000):
    rapiinit = RAPIINIT()
    ctypes.oledll.rapi.CeRapiInitEx(ctypes.byref(rapiinit))
    # Wait for connection (with timeout)
    ctypes.windll.kernel32.WaitForSingleObject(rapiinit.heRapiInit, timeout)

Shutdown = ctypes.oledll.rapi.CeRapiUninit

def CopyFile(src, dst):
    data = open(src, "rb").read()
    # copy local file to remote system via rapi calls
    handle = ctypes.windll.rapi.CeCreateFile(unicode(dst),
                                             GENERIC_WRITE,
                                             0,
                                             None,
                                             CREATE_ALWAYS,
                                             0,
                                             None)
    written = ctypes.wintypes.DWORD()
    ctypes.windll.rapi.CeWriteFile(handle,
                                   data,
                                   len(data),
                                   ctypes.byref(written),
                                   None)
    ctypes.windll.rapi.CeCloseHandle(handle)
    assert written.value == len(data)

def CreateProcess(exepath, args):
    # start the a remote process
    ctypes.windll.rapi.CeCreateProcess(unicode(exepath),
                                       unicode(args),
                                       None, None,
                                       False, 0, None, None,
                                       None, None)

def DeleteFile(path):
    ctypes.windll.rapi.CeDeleteFile(path)
