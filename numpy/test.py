import unittest
import numpy
from ctypes import *
import ctypes_array

class Test(unittest.TestCase):
    def test_np_to_ct(self):
        z = numpy.zeros(32)
        c = ctypes_array.as_ctypes(z)

        self.failUnless(type(c) is c_double * 32)

        self.failUnlessEqual(c[:], [0.0] * 32)
        z[:] = range(32)
        self.failUnlessEqual(c[:], list(range(32)))

    def test_ct_to_np(self):
        c = (c_int * 3 * 2)(*((1, 2, 3), (4, 5, 6)))
        n = ctypes_array.numpy_array(c)

        for i in range(2):
            for j in range(3):
                self.failUnlessEqual(c[i][j], n[i,j])

        
        
if __name__ == "__main__":
    unittest.main()
