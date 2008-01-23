@echo off

rem
rem ctypes_array is the pure Python implementation which uses the '__array_interface__' property.
rem

rem 7.04 us
echo as_ctypes (__array_interface__)
python -m timeit -s "import numpy; n = numpy.zeros(32); from ctypes_array import as_ctypes" "as_ctypes(n)" 
rem 7.91 us
echo as_array (__array_interface__)
python -m timeit -s "from ctypes import c_double; from ctypes_array import as_array; n = (c_double * 3 * 2)()" "as_array(n)" 

REM How fast is the property access?
REM 2.34 us
REM python -m timeit -s "from ctypes import c_double; import ctypes_array; x = c_double()" "x.__array_interface__" 
REM 0.45 us
REM python -m timeit -s "from ctypes import c_double; import array_struct; x = c_double()" "x.__array_struct__" 


rem
rem array_struct is the mixed Python/C implementation which uses the '__array_struct__' property.
rem faster by a factor of 2 (implementation time was more than double the time for the Python version)
rem

rem 3.23
echo as_ctypes (__array_struct__)
python -m timeit -s "import numpy; n = numpy.zeros(32); from array_struct import as_ctypes" "as_ctypes(n)" 
rem 3.77
echo as_array (__array_struct__)
python -m timeit -s "from ctypes import c_double; from array_struct import as_array; n = (c_double * 32)()" "as_array(n)" 
