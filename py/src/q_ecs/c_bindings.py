import ctypes
from typing import Callable

from q_ecs.types import World, World_p, ComponentDescriptor_p, Archetype, Entity, Query, Component, ComponentDescriptor


def mk_world_factory(lib_path: str) -> Callable[[], World]:
    lib = ctypes.CDLL(lib_path)
    
    lib.world_create.argtypes = []
    lib.world_create.restype = World_p

    lib.world_destroy.argtypes = [World_p]
    lib.world_destroy.restype = None

    lib.component_describe.argtypes = [ctypes.c_size_t]
    lib.component_describe.restype = ComponentDescriptor_p
    
    lib.entity_create.argtypes = [World_p, Archetype]
    lib.entity_create.restype = Entity
    
    lib.entity_remove.argtypes = [Entity]
    lib.entity_remove.restype = None

    lib.query_create.argtypes = [World_p, Archetype]
    lib.query_create.restype = Query

    lib.component_destroy.argtypes = [ComponentDescriptor_p]
    lib.component_destroy.restype = None

    class WorldHandle:
        def __init__(self):
            self._handle = lib.world_create()
            self._component_descriptors = {}

        def __del__(self):
            for descriptor in self._component_descriptors.values():
                lib.component_destroy(descriptor)
            lib.world_destroy(self._handle)

        def _get_descriptor(self, component_type: type[Component]) -> ComponentDescriptor:
            if component_type not in self._component_descriptors:
                stride = ctypes.sizeof(component_type)
                descriptor = lib.component_describe(stride)
                self._component_descriptors[component_type] = descriptor
            return self._component_descriptors[component_type]

        def create_entity(self, components: list[type[Component]]) -> Entity:
            descriptors = [self._get_descriptor(c) for c in components]
            descriptor_array = (ComponentDescriptor_p * len(descriptors))(*descriptors)
            archetype = Archetype(descriptors=descriptor_array, length=len(descriptors))
            return lib.entity_create(self._handle, archetype)

        def remove_entity(self, entity: Entity):
            lib.entity_remove(entity)
        
        def query(self, components: list[type[Component]]) -> Query:
            descriptors = [self._get_descriptor(c) for c in components]
            descriptor_array = (ComponentDescriptor_p * len(descriptors))(*descriptors)
            archetype = Archetype(descriptors=descriptor_array, length=len(descriptors))
            
            return lib.query_create(self._handle, archetype)

    return WorldHandle
