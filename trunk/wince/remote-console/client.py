import socket, sys, struct
import code

PS1 = "Remote>>> "
PS2 = "Remote... "

################################################################

def make_packet(data):
    return struct.pack("<i", len(data)) + data

def read_packets(conn):
    # Decode packets, and yield them.
    data = ""
    while 1:
        if not data:
            data += conn.recv(1024)
            if not data:
                raise StopIteration
        size = struct.unpack("<i", data[:4])[0]
        data = data[4:]
        while len(data) < size:
            data += conn.recv(1024)
        yield data[:size]
        data = data[size:]

################################################################

def client(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    reader = read_packets(s)

    def readfunc(prompt=""):
        sys.stderr.write(prompt)
        s.sendall(make_packet(""))
        try:
            data = reader.next()
        except StopIteration:
            raise EOFError
        sys.stderr._output.write(data)
        sys.stderr._output.write("\n")
        return data

    class Output(object):
        def __init__(self, output):
            self._output = output

        def write(self, text):
            self._output.write(text)
            s.sendall(make_packet(text))

        def flush(self):
            pass

    banner = "Python %s\n(Remote Console on %s)" % \
             (sys.version, (host, port))

##    import __builtin__
##    __builtin__.raw_input = readfunc
##    __builtin__.input = lambda: eval(readfunc())

    try:
        sys.ps1, sys.ps2 = PS1, PS2

        sys.stderr = Output(sys.stderr)
        sys.stdout = Output(sys.stdout)

        code.interact(banner=banner, readfunc=readfunc)
    finally:
        sys.stderr = sys.__stderr__
        sys.stdout = sys.__stderr__

################################################################

import getopt

def main(args=sys.argv[1:]):
    opts, args = getopt.getopt(args, "h:p:")
    host, port = ("localhost", 10000)
    for o, a in opts:
        if o == "-h":
            host = a
        elif o == "-p":
            port = int(a)
    client(host, port)

if __name__ == "__main__":
    main()
