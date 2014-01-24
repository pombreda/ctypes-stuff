py2exe for Python 3
===================

`py2exe` is a distutils extension which allows to build standalone
Windows executable programs from Python scripts.

`py2exe` for ``Python 2`` is available at http://sourceforge.net/project/showfiles.php?group_id=15583

.. contents::


News
----

In addition to you beloved setup.py scripts, there is now a
command-line utility which allows to build the exe without any effort:

::

   py -3.3 -m py2exe myscript.py

will create an executable in the `dist` subdirectory.

Adding the `-W <setup-script.py>` switch to the command line will
write a *commented* ``setup.py`` script for you, which can be
customized to your hearts content:

::

   py -3.3 -m py2exe myscript.py -W mysetup.py
   # edit myssetup.py
   py -3.3 mysetup.py py2exe

Installation
------------

::

    py -3.3 -m pip install py2exe

or

::

    pip install py2exe


Using the builder
-----------------

Build runtime archive for a script:

::

        build_exe.py [-h] [-i modname] [-x modname] [-p package_name] [-O] [-s]
                     [-r] [-f modname] [-v] [-c] [-d DESTDIR] [-l LIBNAME]
                     [-b {0,1,2,3}] [-W setup_path]
		     [-svc service]
                     [script [script ...]]


positional arguments:
  script

optional arguments:
  -h, --help            show this help message and exit
  -i modname, --include modname
                        module to include
  -x modname, --exclude modname
                        module to exclude
  -p package_name, --package package_name
                        module to exclude
  -O, --optimize        use optimized bytecode
  -s, --summary         print a single line listing how many modules were
                        found and how many modules are missing
  -r, --report          print a detailed report listing all found modules, the
                        missing modules, and which module imported them.
  -f modname, --from modname
                        print where the module <modname> is imported.
  -v                    verbose output
  -c, --compress        create a compressed library
  -d DESTDIR, --dest DESTDIR
                        destination directory
  -l LIBNAME, --library LIBNAME
                        relative pathname of the python archive

  -b option, --bundle-files option
                        How to bundle the files. 3 - create an .exe, a zip-
                        archive, and .pyd files in the file system. 2 - create
                        .exe and a zip-archive that contains the pyd files.

  -W setup_path, --write-setup-script setup_path
                        Do not build the executables; instead write a setup
                        script that allows further customizations of the build
                        process.

  --service modname
                        The name of a module that contains a service

