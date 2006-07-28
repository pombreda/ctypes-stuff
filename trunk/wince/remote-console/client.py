# Thomas Heller 20060109
# client.py - runs on the Pocket_PC.
import sys, socket, code, time

PS1 = "PocketPC>>> "
PS2 = "PocketPC... "

def client():
    try:
        HOST, PORT = sys.argv[1], int(sys.argv[2])
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))

        def readfunc(prompt=""):
            if prompt:
                sys.stderr.write(prompt)
            try:
                data = s.recv(1024)
            except EOFError:
                s.close()
            sys.stderr._output.write(data[:-1])
            sys.stderr._output.write("\n")
            return data[:-1]

        class Output(object):
            def __init__(self, output):
                self._output = output

            def write(self, text):
                self._output.write(text)
                s.send(text)

            def flush(self): pass

        sys.stdout = Output(sys.stdout)
        sys.stderr = Output(sys.stderr)
        sys.ps1 = PS1
        sys.ps2 = PS2

        banner = "Python %s on %s\n(Remote Console on %s)" % (sys.version, sys.platform, (HOST, PORT))

        # Replace the builtin raw_input (which doesn't work on CE anyway),
        # to make pdb work.
        import __builtin__
        __builtin__.raw_input = readfunc

        code.interact(banner=banner, readfunc=readfunc)

        if hasattr(__builtin__, "_"):
            del __builtin__._
        globals().clear()

        # The console sets these attributes on errors. Prevent they
        # survive the thread.
        try: del sys.last_type
        except AttributeError: pass
        try: del sys.last_value
        except AttributeError: pass
        try: del sys.last_traceback
        except AttributeError: pass

    except SystemExit:
        raise
    except:
        import traceback
        traceback.print_exc()
        time.sleep(5)

if __name__ == "__main__":
    client()
