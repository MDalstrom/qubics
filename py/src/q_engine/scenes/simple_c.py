import ctypes
from q_engine.persistent.ecslib import mk_world
from q_engine.bootstrap import get_config
from q_engine.persistent.metal import state as metal_state

class TestComponent(ctypes.Structure):
    _fields_ = [
        ("value", ctypes.c_int32)
    ]

def get_tick(state = metal_state, config = get_config()):
    world = mk_world()
    e = world.create_entity([TestComponent])
    
    def tick(**kwargs):
        ...     
    return tick
