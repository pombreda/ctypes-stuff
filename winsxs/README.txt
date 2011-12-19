This directory contains scripts and modules that allow to embed
addional, totally separated, Python interpreters into a program.

The 'create_assembly.py' script creates a WinSxS private assembly
containing the python dll plus the standard Python extension modules.

The 'embed.py' script then creates a second Python interpreter by
activating a WinSxS context and loading the second interpreter.  It
displays the sys.path, sys.dllhandle; also loads the _socket extension
from the assembly.

The scripts are currently hardcoded to embed Python 2.6.