import ctypes
from q_ecs.types import Component


class TestComponent(Component):
    _fields_ = [
        ("value", ctypes.c_int32)
    ]

class TestComponent2(Component):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
    ]


registry = [
    TestComponent,
    TestComponent2
]
