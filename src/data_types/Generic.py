#
# 
# 
# 
#  Source: https://community.bistudio.com/wiki/Generic_FileFormat_Data_Types?useskin=darkvector

import numpy as np

def fmt_float(num):
    # More, probably meaningless, formatting only to make the output match Mikero's
    if abs(num) >  19000000:
        return np.format_float_scientific(num).replace(".e", "e")
    return str(np.float32(num))

class RGBA:
    def __init__(self, r = 0, g = 0, b = 0, a = 0):
        if type(r) == np.ndarray:
            self.r = r[0]
            self.g = r[1]
            self.b = r[2]
            self.a = r[3]
        else:
            self.r = r
            self.g = g
            self.b = b
            self.a = a

class XYZTriplet:
    def __init__(self, x=0, y=0, z=0):
        if type(x) == np.ndarray:
            self.x = x[0]
            self.y = x[2]
            self.z = x[1]
        else:
            self.x = x
            self.y = y
            self.z = z
    def __str__(self):
        return f"({self.x},{self.y},{self.z})"

class XYPair:
    def __init__(self, x=0, y=None):
        self.x = int(x)  # ulong // normally associated with cell sizes
        if y is None:
            self.y = self.x
        else:
            self.y = int(y)
    
    def __str__(self):
        return f"({self.x},{self.y})"

    def __div__(self, divisor):
        return XYPair(self.x / divisor, self.y / divisor)

    def __eq__ (self, a):
        self.x = a
        self.y = a


class IndexedString(str):
    def __new__(self, string, index=0):
        obj = super().__new__(self, string)
        obj.idx = index
        return obj
    def get_index(self):
        return self.idx