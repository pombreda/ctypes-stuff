@rem 6.84 us
python -m timeit -s "import numpy; n = numpy.zeros(32); from ctypes_array import as_ctypes" "as_ctypes(n)" 
@rem 8.53 us
python -m timeit -s "from ctypes import c_int; from ctypes_array import as_array; n = (c_int * 3 * 2)()" "as_array(n)" 
