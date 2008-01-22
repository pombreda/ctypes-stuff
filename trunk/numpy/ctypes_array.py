"""This module implements the public functions 'numpy_array' and
'as_ctypes', which can construct numpy arrays from ctypes instances,
and ctypes instances from numpy arrays.

It uses the __array_interface__ version 3, see
http://numpy.scipy.org/array_interface.shtml

ctypes does not support the __array_interface__, so this module
attaches __array_interface__ properties to the ctypes types when
needed.  This module could/should also be implemented in C using the
__array_struct__ description, which would probably be a lot faster.
"""
import sys
from ctypes import *
import numpy.core.multiarray

__all__ = ["numpy_array"]

################################################################
# simple types

# maps the numpy typecodes like '<f8' to simple ctypes types like
# c_double. Filled in by prep_simple.
_typecodes = {}

def prep_simple(simple_type, typestr):
    """Given a ctypes simple type, construct and attach an
    __array_interface__ property to it if it does not yet have one.
    """
    try: simple_type.__array_interface__
    except AttributeError: pass
    else: return

    _typecodes[typestr] = simple_type

    @property
    def __array_interface__(self):
        return {'descr': [('', typestr)],
                '__ref': self,
                'strides': None,
                'shape': (),
                'version': 3,
                'typestr': typestr,
                'data': (addressof(self), False),
                }

    simple_type.__array_interface__ = __array_interface__

if sys.byteorder == "little":
    TYPESTR = "<%c%d"
else:
    TYPESTR = ">%c%d"

simple_types = [
    ((c_byte, c_short, c_int, c_long, c_longlong), "i"),
    ((c_ubyte, c_ushort, c_uint, c_ulong, c_ulonglong), "u"),
    ((c_float, c_double), "f"),
]

# Prep that numerical ctypes types:
for types, code in simple_types:
    for tp in types:
        prep_simple(tp, TYPESTR % (code, sizeof(tp)))

################################################################
# array types

_ARRAY_TYPE = type(c_int * 1)

def prep_array(array_type):
    """Given a ctypes array type, construct and attach an
    __array_interface__ property to it if it does not yet have one.
    """
    try: array_type.__array_interface__
    except AttributeError: pass
    else: return

    shape = []
    ob = array_type
    while type(ob) == _ARRAY_TYPE:
        shape.append(ob._length_)
        ob = ob._type_
    shape = tuple(shape)
    ai = ob().__array_interface__
    descr = ai['descr']
    typestr = ai['typestr']
    
    @property
    def __array_interface__(self):
        return {'descr': descr,
                '__ref': self,
                'strides': None,
                'shape': shape,
                'version': 3,
                'typestr': typestr,
                'data': (addressof(self), False),
                }
        
    array_type.__array_interface__ = __array_interface__

################################################################
# public functions

def numpy_array(obj):
    """Create a numpy array from a ctypes array.  The numpy array
    shares the memory with the ctypes object."""
    prep_array(type(obj))
    return numpy.core.multiarray.array(obj)

def as_ctypes(obj):
    """Create and return a ctypes object from a numpy array.  Actually
    anything that exposes the __array_interface__ is accepted."""
    ai = obj.__array_interface__
    tp = _typecodes[ai["typestr"]]
    for dim in reversed(ai["shape"]):
        tp = tp * dim
    addr = ai["data"][0]
    result = tp.from_address(addr)
    result.__keep = ai
    return result

################################################################

if __name__ == "__main__":

    a = c_short(3)
    b = c_float(21.703)
    c = (c_float * 3 * 2)(*((1, 2, 3), (4, 5, 6)))
##    print c

    a = numpy_array(a)
    b = numpy_array(b)
    nc = numpy_array(c)

##    import gc; gc.collect(); gc.collect()

##    print (a, b, nc)
##    print typecodes

    c2 = as_ctypes(nc)

    print c, nc, c2
    print c == c2

    print as_ctypes(a)
