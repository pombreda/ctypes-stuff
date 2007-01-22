import socket, sys, struct
import code

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

def interact(host, port, command):
    # If command is None, start an interactive interpreter.
    # If command is != None, execute it, then return.
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
        sys.stderr = Output(sys.stderr)
        sys.stdout = Output(sys.stdout)

        if command is None:
            code.interact(banner=banner, readfunc=readfunc)
        else:
            if sys.argv[1] == '-c':
                sys.argv = ['-c']
            try:
                exec command in globals()
            except SystemExit:
                raise
            except Exception:
                import traceback; traceback.print_exc()
    finally:
        sys.stderr = sys.__stderr__
        sys.stdout = sys.__stderr__

################################################################

import getopt

def main():
    # First two command line args are how to connect to the console:
    host = sys.argv[1]
    port = int(sys.argv[2])
    sys.argv = [''] + sys.argv[3:]
    opts, args = getopt.getopt(sys.argv[1:], "c:")
    command = None
    for o, a in opts:
        if o == "-c":
            command = a
    interact(host, port, command)
    
if __name__ == "__main__":
    main()
