import unittest
import numpy
from ctypes import *
import ctypes_array
import array_struct

class Test_Python(unittest.TestCase):
    mod = ctypes_array
    def test_np_to_ct(self):
        z = numpy.zeros(32)
        c = self.mod.as_ctypes(z)

        self.failUnless(type(c) is c_double * 32)

        self.failUnlessEqual(c[:], [0.0] * 32)
        z[:] = range(32)
        self.failUnlessEqual(c[:], list(range(32)))

    def test_ct_to_np(self):
        c = (c_int * 3 * 2)(*((1, 2, 3), (4, 5, 6)))
        n = self.mod.as_array(c)

        self.failUnless(n.base is c)

        for i in range(2):
            for j in range(3):
                self.failUnlessEqual(c[i][j], n[i,j])
                c[i][j] = 0
                self.failUnlessEqual(c[i][j], n[i,j])

class Test_C(Test_Python):
    # same test, but uses the faster C version
    mod = array_struct
        
        
if __name__ == "__main__":
    unittest.main()
