import ctypes

from .c_bindings import mk_lib, TestComponent, ComponentId, World

class NetworkWorld(World):
    def __init__(self, world: World):
        self.wrapped = world

    def register_component(self, component_type: type):
        self.wrapped.register_component(component_type)


