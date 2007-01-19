import os, sys, socket, struct, getopt, time, random
import ctypes
from client import make_packet, read_packets
import rapi

def console(host, port):

    inp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    inp.bind((host, port))
    inp.listen(1)

    # wait for connection
    conn, addr = inp.accept()

    for packet in read_packets(conn):
        # empty packet: remote interpreter needs input
        if not packet:
            try:
                data = raw_input()
            except EOFError:
                conn.close()
                return
            conn.sendall(make_packet(data))
        # nonempty packet: display it
        else:
            sys.stderr.write(packet)

################################################################

REMOTE_EXE = ur'\Program Files\Python%s%s\python.exe'
    
def usage():
    print """\
usage: %s [option] ... [-c cmd | -m mod | file | -] [arg] ..
Options and arguments (and corresponding environment variables):
-c cmd : program passed in as string (terminates option list)
-h     : print this help message and exit (also --help)
-i     : inspect interactively after running script, (also PYTHONINSPECT=x)
         and force prompts, even if stdin does not appear to be a terminal
-m mod : run library module as a script (terminates option list)
-v ver : use Python version <ver> on the PDA, default is 2.5
file   : program read from script file
-      : program read from stdin (default; interactive mode if a tty)
arg ...: arguments passed to program in sys.argv[1:]
""" % sys.argv[0]

def get_client_data():
    if hasattr(sys, "frozen"):
        kernel32 = ctypes.windll.kernel32
        hrsrc = kernel32.FindResourceA(None, 1, 1000)
        hglob = kernel32.LoadResource(None, hrsrc)
        kernel32.LockResource.restype = ctypes.c_char_p
        return kernel32.LockResource(hglob)
    else:
        path = os.path.join(os.path.dirname(__file__), "client.py")
        return open(path).read()

def main(args=sys.argv[1:]):
    # Parse arguments
    opts, args = getopt.getopt(args, "c:him:v:")
    remote_exe = REMOTE_EXE % (2, 5)
    for o, a in opts:
        if o == "-h":
            usage()
            raise SystemExit
        elif o == "-v":
            remote_exe = REMOTE_EXE % tuple(a.split("."))
        else:
            raise SystemExit("Error: option %s not (yet) implemented" % o)

    # Prepare script on the PDA
    own_ip = socket.gethostbyname(socket.gethostname())
    # Select a random port, so we could start several consoles at the same time
    port = random.choice(xrange(20000, 20999))
    client_script = ur"\Temp\_script%s.py" % port
    try:
        rapi.Init()
    except rapi.ConnectError, details:
        raise SystemExit("Error: %s" % details)
    rapi.WriteFile(client_script, get_client_data())

    # Run script on the PDA, and run the console
    try:
        rapi.CreateProcess(remote_exe,
                           ur"/new %s -h %s -p %s" % (client_script, own_ip, port))
        console("localhost", port)
    # Now cleanup.
    finally:
        # It may not be possible immediately to delete the client
        # script file on the pocket PC, it remains open until the
        # Python process has finished; so try several times.
        for _ in range(10):
            try:
                rapi.DeleteFile(client_script)
            except WindowsError:
                time.sleep(0.2)
                continue
            else:
                break

if __name__ == "__main__":
    main()
