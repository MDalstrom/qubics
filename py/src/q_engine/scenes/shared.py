import ctypes


class Position(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float), ("z", ctypes.c_float)]
class Velocity(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_float), ("dy", ctypes.c_float), ("dz", ctypes.c_float)]

