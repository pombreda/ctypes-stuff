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

def parse_args(args):
    from optparse import OptionParser

    def terminate(option, opt_str, value, parser):
        # optparser callback for an argument that terminates the options
        # list. Remaining arguments will appear in 'args'.
        setattr(parser.values, option.dest, value)
        parser.largs.extend(parser.rargs[:])
        del parser.rargs[:]

    parser = OptionParser()
    parser.disable_interspersed_args()
    parser.add_option("-c", action="callback", callback=terminate, dest="command",
                      type="string",
                      help="program passed in as string (terminates option list)")
    parser.add_option("-i", action="store_true", default=False, dest="interactive",
                      help="inspect interactively after running script")
    parser.add_option("-m", action="callback", callback=terminate, dest="module",
                      type="string",
                      help="run library module as script (terminates option list)")
    parser.add_option("-u", action="store_true", default=False, dest="unbuffered",
                      help="unbuffered binary stdout and stderr (a tad)")
    parser.add_option("-v", dest = "target_version", default="2.5",
                      help="specify Python version to use, default is 2.5")

    options, args = parser.parse_args(args)
    return options, args

REMOTE_EXE = ur'\Program Files\Python%s%s\python.exe'
    
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
    opts, args = parse_args(args)

    version = opts.target_version.split(".")
    remote_exe = REMOTE_EXE % tuple(version)

    if opts.module is None and opts.command is None and args:
        raise NotImplementedError

    if opts.module is not None:
        opts.command = "import runpy;" + \
                       "runpy.run_module('%s', run_name='__main__', alter_sys=True)" % opts.module

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

    cmdline = ur"/new %s %s %s" % (client_script, own_ip, port)
    if opts.command is not None:
        cmdline = cmdline + " -c %r" % opts.command

    # Run script on the PDA, and run the console
    try:
        rapi.CreateProcess(remote_exe, cmdline)
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
