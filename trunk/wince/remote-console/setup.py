# Run 'setup.py py2exe' to create a single-file executable.  The
# executable may further be compressed with upx.  When using Python
# 2.3, this results in a single file executable with a size of less
# than 700 kB.

from distutils.core import setup
import py2exe
import ctypes

NAME = "PythonConsole"
VERSION = "1.0"

# The client.py script is embedded as resource into the exe.
client_data = open("client.py").read()

console = dict(script = "console.py",
              other_resources = [(1000, 1, client_data + "\0")],
              dest_base = "%s-%s" % (NAME, VERSION),
              )

setup(
    name = NAME,
    version = VERSION,
    description = "blah",
    long_description = "foo " * 32,
    url = "blahblah",
    author = "theller@ctypes.org",
    author_email = "theller@ctypes.org",
    license = "MIT",
    platforms = ["Windows"],

##    scripts = ["server.py", "client.py", "rapi.py"],
    py_modules = ["console", "client", "rapi"],
    options = {"py2exe":
               {"excludes":"_ssl inspect calendar datetime".split(),
                "compressed": 1,
                "bundle_files": 1,
##                "ascii": 1,
                },
               "sdist":
               {"force_manifest": 1},
               },
    zipfile=None,
    console = [console],
)
