py2exeimporter - an importer which can import extension modules
from zipfiles without unpacking them to the file system.

This file and ``_memimporter.pyd`` is also part of the ``py2exe`` package.

Overview
========

py2exeimporter.py contains the ZipExtImporter class which allows to
load Python binary extension modules contained in a zip.archive,
*without unpacking them to the file system*.

Call the ``py2exeimporter.install()`` function to install the import
hook, add a zip-file containing .pyd or .dll extension modules to
sys.path, and import them.

It uses the _memimporter extension which uses code from Joachim
Bauch's MemoryModule library.  This library emulates the win32 api
function LoadLibrary.

Usage example
=============

You have to prepare a zip-archive ``lib.zip`` containing
your Python's _socket.pyd for this example to work.

>>> import py2exeimporter
>>> py2exeimporter.install()
>>> import sys
>>> sys.path.insert(0, "lib.zip")
>>> import _socket
>>> print(_socket)
<module '_socket' from 'lib.zip\_socket.pyd'>
>>> _socket.__file__
'lib.zip\\_socket.pyd'
>>> _socket.__loader__
<ZipExtensionImporter object 'lib.zip'>
>>> # Reloading also works correctly:
>>> _socket is reload(_socket)
True
>>>

