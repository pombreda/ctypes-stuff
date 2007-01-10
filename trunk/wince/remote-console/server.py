# Thomas Heller 20060109
# Remote Python console for PocketPC
#
import socket, sys, threading, random, time
import ctypes, ctypes.wintypes
import win32con

PORT = random.choice(xrange(20000, 20999))    # port used for communication

# full path to python executable on the pocket device
REMOTE_EXE = ur'\Program Files\Python%s\python.exe'

DEFAULT_VERSION = '25' # Default Python version to start on the PPC,
                       # can be overridden from the command line

# full path to temporary client.py script on the pocket device
REMOTE_CLIENT = ur'\Temp\_script%s.py' % PORT

TIMEOUT = 5000 # rapi init timeout in milliseconds

################################################################
# Some rapi definitions
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

##class ConnectError(Exception):
##    pass

ConnectError = SystemExit

def WFSO_errcheck(result, func, arguments):
    if result == win32con.WAIT_TIMEOUT:
        raise ConnectError("connection timeout")
    elif result == win32con.WAIT_ABANDONED:
        raise ConnectError("connection abandoned")
    
ctypes.windll.kernel32.WaitForSingleObject.errcheck = WFSO_errcheck

################################################################

def server(version):
    # Init rapi, then transfer the client script data to the pocket pc.
    rapiinit = RAPIINIT()
    ctypes.oledll.rapi.CeRapiInitEx(ctypes.byref(rapiinit))

    # Wait for connection (with timeout)
    ctypes.windll.kernel32.WaitForSingleObject(rapiinit.heRapiInit, TIMEOUT)
        
    # transfer the client script
    client_script_data = open("client.py", "rb").read()
    handle = ctypes.windll.rapi.CeCreateFile(REMOTE_CLIENT,
                                             win32con.GENERIC_WRITE,
                                             0,
                                             None,
                                             win32con.CREATE_ALWAYS,
                                             0,
                                             None)
    written = ctypes.wintypes.DWORD()
    ctypes.windll.rapi.CeWriteFile(handle,
                                   client_script_data,
                                   len(client_script_data),
                                   ctypes.byref(written),
                                   None)
    ctypes.windll.rapi.CeCloseHandle(handle)

    # set up the communication
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', PORT))
    s.listen(1)

    # start the client process on the PocketPC
    own_ip = socket.gethostbyname(socket.gethostname())
    args = u"/new %s %s %s" % (unicode(REMOTE_CLIENT), own_ip, PORT)
    ctypes.windll.rapi.CeCreateProcess(unicode(REMOTE_EXE % version),
                                       args,
                                       None, None,
                                       False, 0, None, None,
                                       None, None)

    # wait for connection
    conn, addr = s.accept()

    # get input and send it to the client
    def get_input():
        while 1:
            try:
                data = raw_input()
            except EOFError:
                conn.send("raise SystemExit\n")
                return
            except:
                import traceback
                traceback.print_exc()
            conn.send(data + '\n')

    t = threading.Thread(target=get_input)
    t.setDaemon(True)
    t.start()

    # receive data from the client and display it
    try:
        while 1:
            try:
                data = conn.recv(1024)
            except KeyboardInterrupt:
                print "KeyboardInterrupt"
                continue
            except socket.error:
                data = ""
            if not data:
                if t.isAlive(): # thread blocked in raw_input
                    print "SystemExit, hit return to end."
                raise SystemExit
            sys.stderr.write(data)

    finally:
        # Cleanup.  It may not be possible immediately to delete the
        # client script file on the pocket PC, it remains open until
        # the Python process has finished; so try several times.
        for i in range(10):
            try:
                ctypes.windll.rapi.CeDeleteFile(REMOTE_CLIENT)
            except WindowsError:
                time.sleep(0.2)
                continue
            else:
                break
        ctypes.oledll.rapi.CeRapiUninit()

if __name__ == "__main__":
    import getopt
    opts, args = getopt.getopt(sys.argv[1:], "v:")
    version = DEFAULT_VERSION
    for o, a in opts:
        if o == "-v":
            version = a
    server(version)
