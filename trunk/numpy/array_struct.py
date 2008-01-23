import sys

from _array_struct import prep_simple , prep_array as _prep_array
from ctypes import *
from numpy.core.multiarray import array as multi_array

_typecodes = {}

if sys.byteorder == "little":
    TYPESTR = "<%c%d"
else:
    TYPESTR = ">%c%d"

simple_types = [
    ((c_byte, c_short, c_int, c_long, c_longlong), "i"),
    ((c_ubyte, c_ushort, c_uint, c_ulong, c_ulonglong), "u"),
    ((c_float, c_double), "f"),
]

# Prep the numerical ctypes types:
for types, code in simple_types:
    for tp in types:
        _typecodes[TYPESTR % (code, sizeof(tp))] = tp
        prep_simple(tp, ord(code), sizeof(tp))

################################################################
# array types

_ARRAY_TYPE = type(c_int * 1)

def prep_array(array_type):
    # We do the fancy stuff in Python, and leave the construction
    # of the __array_struct__ property to C code.
    try: array_type.__array_struct__
    except AttributeError: pass
    else: return

    shape = []
    ob = array_type
    while type(ob) == _ARRAY_TYPE:
        shape.append(ob._length_)
        ob = ob._type_
    shape = tuple(shape)
    _prep_array(array_type, ob.__array_struct__, tuple(shape))


################################################################
# public functions

def as_array(obj):
    """Create a numpy array from a ctypes array.  The numpy array
    shares the memory with the ctypes object."""
    tp = type(obj)
    try: tp.__array_struct__
    except AttributeError: prep_array(tp)
    return multi_array(obj, copy=False)

from _array_struct import as_ctypes
