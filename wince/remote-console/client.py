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

def interact(host, port, encoding, command):
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
        def __init__(self, output, encoding):
            self._output = output
            self.encoding = encoding

        def write(self, text):
            if isinstance(text, unicode):
                text = text.encode(self.encoding, "replace")
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
        sys.stderr = Output(sys.stderr, encoding)
        sys.stdout = Output(sys.stdout, encoding)

        if command is None:
            code.interact(banner=banner, readfunc=readfunc)
        else:
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

def parse_args(args):
    from optparse import OptionParser

    def command(option, opt_str, value, parser):
        # optparser callback for an argument that terminates the options
        # list. Remaining arguments will appear in 'args'.
        setattr(parser.values, option.dest, value)
        parser.largs.append("-c")
        parser.largs.extend(parser.rargs[:])
        del parser.rargs[:]

    parser = OptionParser()
    parser.disable_interspersed_args()
    parser.add_option("-c", action="callback", callback=command, dest="command",
                      type="string",
                      help="program passed in as string (terminates option list)")

    return parser.parse_args(args)

def main():
    # First two command line args are how to connect to the console:
    host = sys.argv[1]
    port = int(sys.argv[2])
    encoding = sys.argv[3]
    opts, args = parse_args(sys.argv[4:])
    sys.argv = args

    interact(host, port, encoding, opts.command)
    
if __name__ == "__main__":
    main()
