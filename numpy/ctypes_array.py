import sys
from ctypes import *
import numpy.core.multiarray

__all__ = ["numpy_array"]

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

simple_types = [
    ((c_byte, c_short, c_int, c_long, c_longlong), "i"),
    ((c_ubyte, c_ushort, c_uint, c_ulong, c_ulonglong), "u"),
    ((c_float, c_double), "f"),
]

if sys.byteorder == "little":
    TYPESTR = "<%c%d"
else:
    TYPESTR = ">%c%d"

for types, code in simple_types:
    for tp in types:
        prep_simple(tp, TYPESTR % (code, sizeof(tp)))

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

def numpy_array(obj):
    """Create a numpy array from a ctypes array.  The numpy array
    shares the memory with the ctypes object."""
    prep_array(type(obj))
    return numpy.core.multiarray.array(obj)

################################################################

if __name__ == "__main__":

    a = c_short(3)
    b = c_float(21.703)
    c = (c_float * 3 * 2)(*((1, 2, 3), (4, 5, 6)))

    a = numpy_array(a)
    b = numpy_array(b)
    c = numpy_array(c)

    import gc; gc.collect(); gc.collect()

    print (a, b, c)
    print typecodes
