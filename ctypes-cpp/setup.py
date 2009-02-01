#!/usr/bin/env python
#
# $Id: setup.py 65219 2008-07-24 11:29:08Z thomas.heller $
#
#

"""cpptypes is a Python package...
"""

__version__ = "0.0.1dev"

################################################################

import sys, os
from distutils.core import setup, Extension, Command
from distutils.errors import DistutilsOptionError
from distutils.command import build_py, build_ext, clean
from distutils.command import install_data
from distutils.dir_util import mkpath
from distutils.util import get_platform
from distutils.cygwinccompiler import Mingw32CCompiler

################################################################
# Additional and overridden distutils commands
#
class test(Command):
    # Original version of this class posted
    # by Berthold Hoellmann to distutils-sig@python.org
    description = "run tests"

    user_options = [
        ('tests=', 't',
         "comma-separated list of packages that contain test modules"),
        ('use-resources=', 'u',
         "resources to use - resource names are defined by tests"),
        ('refcounts', 'r',
         "repeat tests to search for refcount leaks (requires 'sys.gettotalrefcount')"),
        ]

    boolean_options = ["refcounts"]

    def initialize_options(self):
        self.build_base = 'build'
        self.use_resources = ""
        self.refcounts = False
        self.tests = "cpptypes.test"

    # initialize_options()

    def finalize_options(self):
        if self.refcounts and not hasattr(sys, "gettotalrefcount"):
            raise DistutilsOptionError("refcount option requires Python debug build")
        self.tests = self.tests.split(",")
        self.use_resources = self.use_resources.split(",")

    # finalize_options()

    def run(self):
        self.run_command('build')

        import cpptypes.test
        cpptypes.test.use_resources.extend(self.use_resources)

        for name in self.tests:
            package = __import__(name, globals(), locals(), ['*'])
            print "Testing package", name, (sys.version, sys.platform, os.name)
            cpptypes.test.run_tests(package,
                                  "test_*.py",
                                  self.verbose,
                                  self.refcounts,
                                  [])

    # run()

# class test


################################################################
# the cpptypes package
#
packages = ["cpptypes",
            "cpptypes.test",
            "cpptypes.samples",
            "cpptypes.samples.mydll"]

################################################################
# pypi classifiers
#
classifiers = [
    'Development Status :: 4 - Beta',
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Programming Language :: C',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    ]

################################################################
# main section
#
##from ce import ce_install_lib

if __name__ == '__main__':
    setup(name="cpptypes",
          packages = packages,

          classifiers = classifiers,

          version=__version__,
          description="cpptypes - XXX",
          long_description = __doc__,
          author="Thomas Heller",
          author_email="theller@ctypes.org",
          license="MIT License",
##          url="http://starship.python.net/crew/theller/ctypes/",
###          platforms=["windows", "Linux", "MacOS X", "Solaris", "FreeBSD"],
##          download_url="http://sourceforge.net/project/showfiles.php?group_id=71702",

          cmdclass = {'test': test},
          )

## Local Variables:
## compile-command: "python setup.py build"
## End:
