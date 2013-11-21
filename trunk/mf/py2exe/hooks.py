# -*- coding: utf-8 -*-
#
# Hooks module for py2exe.
# Inspired by cx_freeze's hooks.py, which is:
#
#    Copyright © 2007-2013, Anthony Tuininga.
#    Copyright © 2001-2006, Computronix (Canada) Ltd., Edmonton, Alberta, Canada.
#    All rights reserved.
#
import os, sys

def hook_pyreadline(finder, module):
    """
    """
    finder.excludes.append("IronPythonConsole")
    finder.excludes.append("StringIO") # in pyreadline.py3k_compat
    finder.excludes.append("System")
    finder.excludes.append("sets")
    finder.excludes.append("startup")

def hook_xml_etree_ElementTree(finder, module):
    """ElementC14N is an optional extension. Ignore if it is not
    found.
    """
    finder.excludes.append("ElementC14N")

def hook_urllib_request(finder, module):
    """urllib.request imports _scproxy on darwin
    """
    finder.excludes.append("_scproxy")

def hook_pythoncom(finder, module):
    """pythoncom is a Python extension module with .dll extension,
    usually in the windows system directory as pythoncom3X.dll.
    """
    import pythoncom
    finder.add_dll(pythoncom.__file__)

def hook_pywintypes(finder, module):
    """pywintypes is a Python extension module with .dll extension,
    usually in the windows system directory as pywintypes3X.dll.
    """
    import pywintypes
    finder.add_dll(pywintypes.__file__)

def hook_tkinter(finder, module):
    """Recusively copy tcl and tk directories.
    """
    # It probably doesn't make sense to exclude tix from the tcl distribution,
    # and only copy it when tkinter.tix is imported...
    tcl_dir = os.path.join(sys.prefix, "tcl")
    finder.add_datadirectory("tcl", tcl_dir, recursive=True)

def hook_six(finder, module):
    """six.py is a python2/python3 compaibility library.  Exclude the
    python2 modules.
    """
    finder.excludes.append("StringIO")

def hook_matplotlib(finder, module):
    """matplotlib requires data files in a 'mpl-data' subdirectory in
    the same directory as the executable.
    """
    # c:\Python33\lib\site-packages\matplotlib
    mpl_data_path = os.path.join(os.path.dirname(module.__loader__.path),
                                 "mpl-data")
    finder.add_datadirectory("mpl-data", mpl_data_path, recursive=True)
    finder.excludes.append("wx")

def hook_numpy_distutils(finder, module):
    """In a 'if sys.version_info[0] < 3:' block numpy.distutils does
    an implicit relative import: 'import __config__'.  This will not
    work in Python3 so ignore it.
    """
    finder.excludes.append("__config__")

def hook_numpy_f2py(finder, module):
    """ numpy.f2py tries to import __svn_version__.  Ignore when his fails.
    """
    finder.excludes.append("__svn_version__")

def hook_numpy_core_umath(finder, module):
    """the numpy.core.umath module is an extension module and the numpy module
       imports * from this module; define the list of global names available
       to this module in order to avoid spurious errors about missing
       modules"""
    module.__globalnames__.add("add")
    module.__globalnames__.add("absolute")
    module.__globalnames__.add("arccos")
    module.__globalnames__.add("arccosh")
    module.__globalnames__.add("arcsin")
    module.__globalnames__.add("arcsinh")
    module.__globalnames__.add("arctan")
    module.__globalnames__.add("arctanh")
    module.__globalnames__.add("bitwise_and")
    module.__globalnames__.add("bitwise_or")
    module.__globalnames__.add("bitwise_xor")
    module.__globalnames__.add("ceil")
    module.__globalnames__.add("conjugate")
    module.__globalnames__.add("cosh")
    module.__globalnames__.add("divide")
    module.__globalnames__.add("exp")
    module.__globalnames__.add("e")
    module.__globalnames__.add("fabs")
    module.__globalnames__.add("floor")
    module.__globalnames__.add("floor_divide")
    module.__globalnames__.add("fmod")
    module.__globalnames__.add("greater")
    module.__globalnames__.add("hypot")
    module.__globalnames__.add("invert")
    module.__globalnames__.add("isfinite")
    module.__globalnames__.add("isinf")
    module.__globalnames__.add("isnan")
    module.__globalnames__.add("less")
    module.__globalnames__.add("left_shift")
    module.__globalnames__.add("log")
    module.__globalnames__.add("logical_and")
    module.__globalnames__.add("logical_not")
    module.__globalnames__.add("logical_or")
    module.__globalnames__.add("logical_xor")
    module.__globalnames__.add("maximum")
    module.__globalnames__.add("minimum")
    module.__globalnames__.add("multiply")
    module.__globalnames__.add("negative")
    module.__globalnames__.add("not_equal")
    module.__globalnames__.add("power")
    module.__globalnames__.add("remainder")
    module.__globalnames__.add("right_shift")
    module.__globalnames__.add("sign")
    module.__globalnames__.add("signbit")
    module.__globalnames__.add("sinh")
    module.__globalnames__.add("sqrt")
    module.__globalnames__.add("tan")
    module.__globalnames__.add("tanh")
    module.__globalnames__.add("true_divide")

def hook_numpy_core_numerictypes(finder, module):
    """the numpy.core.numerictypes module adds a number of items to itself
       dynamically; define these to avoid spurious errors about missing
       modules"""
    module.__globalnames__.add("bool_")
    module.__globalnames__.add("cdouble")
    module.__globalnames__.add("complexfloating")
    module.__globalnames__.add("csingle")
    module.__globalnames__.add("double")
    module.__globalnames__.add("float64")
    module.__globalnames__.add("float_")
    module.__globalnames__.add("inexact")
    module.__globalnames__.add("integer")
    module.__globalnames__.add("intc")
    module.__globalnames__.add("int32")
    module.__globalnames__.add("number")
    module.__globalnames__.add("single")
