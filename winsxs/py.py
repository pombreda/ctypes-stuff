from ctypes import CDLL, c_char_p, c_int, c_void_p

class Python(object):
    def __init__(self, name):
        self._dll = CDLL(name)
        self.Py_BytesWarningFlag = c_int.in_dll(self._dll, "Py_BytesWarningFlag")
        self.Py_DebugFlag = c_int.in_dll(self._dll, "Py_DebugFlag")
        self.Py_DivisionWarningFlag = c_int.in_dll(self._dll, "Py_DivisionWarningFlag")
        self.Py_DontWriteBytecodeFlag = c_int.in_dll(self._dll, "Py_DontWriteBytecodeFlag")
        self.Py_IgnoreEnvironmentFlag = c_int.in_dll(self._dll, "Py_IgnoreEnvironmentFlag")
        self.Py_FrozenFlag = c_int.in_dll(self._dll, "Py_FrozenFlag")
        self.Py_InspectFlag = c_int.in_dll(self._dll, "Py_InspectFlag")
        self.Py_InteractiveFlag = c_int.in_dll(self._dll, "Py_InteractiveFlag")
        self.Py_NoSiteFlag = c_int.in_dll(self._dll, "Py_NoSiteFlag")
        self.Py_OptimizeFlag = c_int.in_dll(self._dll, "Py_OptimizeFlag")
        self.Py_Py3kWarningFlag = c_int.in_dll(self._dll, "Py_Py3kWarningFlag")
        self.Py_UseClassExceptionsFlag = c_int.in_dll(self._dll, "Py_UseClassExceptionsFlag")
        self.Py_VerboseFlag = c_int.in_dll(self._dll, "Py_VerboseFlag")
        self.Py_TabcheckFlag = c_int.in_dll(self._dll, "Py_TabcheckFlag")
        self.Py_UnicodeFlag = c_int.in_dll(self._dll, "Py_UnicodeFlag")

        self.Py_SetProgramName = self._dll.Py_SetProgramName
        self.Py_SetProgramName.restype = None
        self.Py_SetProgramName.argtypes = [c_char_p]

        self.Py_SetPythonHome = self._dll.Py_SetPythonHome
        self.Py_SetPythonHome.restype = None
        self.Py_SetPythonHome.argtypes = [c_char_p]

        self.Py_GetPath = self._dll.Py_GetPath
        self.Py_GetPath.restype = c_char_p
        self.Py_GetPath.argtypes = []

        self.Py_Initialize = self._dll.Py_Initialize
        self.Py_Initialize.restype = None
        self.Py_Initialize.argtypes = []

        self.PyRun_SimpleStringFlags = self._dll.PyRun_SimpleStringFlags
        self.PyRun_SimpleStringFlags.restype = c_int
        self.PyRun_SimpleStringFlags.argtypes = [c_char_p, c_void_p]

    def PyRun_SimpleString(self, s):
        return self.PyRun_SimpleStringFlags(s, None)

