from typing import Protocol, Callable
from functools import partial
import ctypes
from ctypes import Structure, c_void_p, c_size_t, c_int, c_uint64, c_char_p, POINTER
import numpy as np

ComponentId = c_size_t

class TestComponent(Structure):
    _fields_ = [
        ("value", c_int),
    ]

class World_p(c_void_p):
    pass

class Archetype_p(c_void_p):
    pass

class Chunk_p(c_void_p):
    pass

class ComponentMask(Structure):
    _fields_ = [
        ("bitmasks", POINTER(c_uint64)),
        ("length", c_size_t),
        ("popcount", c_size_t),
    ]

class Entity(Structure):
    _fields_ = [
        ("chunk", Chunk_p),
        ("idx", c_size_t)
    ]

class Chunk(Structure):
    pass

Chunk._fields_ = [
    ("data", POINTER(c_void_p)),
    ("entities_count", c_size_t),
    ("next", POINTER(Chunk)),
    ("archetype", c_void_p),
]

class World(Protocol):
    def __init__(self, capacity): ...
    def __del__(self): ...
    def register_component(self, component_type: type) -> int: ...
    def create_entity(self, components: list[type]) -> Entity: ...
    def get_component(self, entity: Entity, component_type: type[ctypes.Structure]): ...
    def get_component_array(self, component_type: type[ctypes.Structure], entities: list[Entity]) -> np.ndarray: ...
    @property
    def handle(self) -> World_p: ...

def mk_lib(path: str) -> Callable[[int], World]:
    _lib = ctypes.CDLL(path)

    _lib.world_create.argtypes = [c_size_t]
    _lib.world_create.restype = World_p

    _lib.world_destroy.argtypes = [World_p]
    _lib.world_destroy.restype = None

    _lib.world_register_component.argtypes = [World_p, c_char_p, c_size_t]
    _lib.world_register_component.restype = ComponentId

    _lib.world_get_or_create_archetype.argtypes = [World_p, POINTER(ComponentId), c_size_t]
    _lib.world_get_or_create_archetype.restype = Archetype_p

    _lib.archetype_create.argtypes = [ComponentMask]
    _lib.archetype_create.restype = Archetype_p

    _lib.archetype_destroy.argtypes = [Archetype_p]
    _lib.archetype_destroy.restype = None

    _lib.entity_create.argtypes = [World_p, Archetype_p]
    _lib.entity_create.restype = Entity

    _lib.entity_get_component_data_ptr.argtypes = [World_p, Entity, ComponentId]
    _lib.entity_get_component_data_ptr.restype = c_void_p

    _lib.entity_remove.argtypes = [World_p, Entity]
    _lib.entity_remove.restype = None

    _lib.entity_move.argtypes = [Entity, World_p, Archetype_p]
    _lib.entity_move.restype = Entity

    _lib.get_data_idx.argtypes = [ComponentMask, c_size_t]
    _lib.get_data_idx.restype = c_size_t


    class WorldHandle:
        def __init__(self, capacity):
            self._handle = _lib.world_create(capacity)
            if not self._handle:
                raise RuntimeError("Failed to create ECS world")
            self._component_types = {}

        def __del__(self):
            if hasattr(self, '_handle') and self._handle:
                _lib.world_destroy(self._handle)

        def register_component(self, component_type: type) -> int:
            if not issubclass(component_type, ctypes.Structure):
                raise TypeError("component_type must be a ctypes.Structure")

            if component_type in self._component_types:
                return self._component_types[component_type]
            
            name = component_type.__name__
            stride = ctypes.sizeof(component_type)
            comp_id = _lib.world_register_component(self._handle, name.encode('utf-8'), stride)
            self._component_types[component_type] = comp_id
            return comp_id

        def create_entity(self, components: list[type]) -> Entity:
            ids = [self._component_types.get(c) for c in components]
            if any(id is None for id in ids):
                missing = [c.__name__ for c, id in zip(components, ids) if id is None]
                raise ValueError(f"Component types not registered: {missing}")
            
            id_array = (ComponentId * len(ids))(*ids)
            archetype = _lib.world_get_or_create_archetype(self._handle, id_array, len(ids))
            
            if not archetype:
                raise RuntimeError("Failed to get or create archetype")
                
            return _lib.entity_create(self._handle, archetype)

        def get_component(self, entity: Entity, component_type: type[ctypes.Structure]):
            if component_type not in self._component_types:
                raise ValueError(f"Component type {component_type.__name__} not registered")

            comp_id = self._component_types[component_type]
            ptr = _lib.entity_get_component_data_ptr(self._handle, entity, comp_id)
            if not ptr:
                return None
            
            component_ptr = ctypes.cast(ptr, ctypes.POINTER(component_type))
            return component_ptr.contents

        def get_component_array(self, component_type: type[ctypes.Structure], entities: list[Entity]) -> np.ndarray:
            """Get component data for multiple entities as a numpy array.
            
            Args:
                component_type: The component type to retrieve
                entities: List of Entity objects to get components from
                
            Returns:
                NumPy array of component data (array of structures)
            """
            if component_type not in self._component_types:
                raise ValueError(f"Component type {component_type.__name__} not registered")
            
            if not entities:
                return np.array([], dtype=component_type)
            
            # Create array of the component type with appropriate size
            arr = (component_type * len(entities))()
            
            for i, entity in enumerate(entities):
                comp = self.get_component(entity, component_type)
                if comp:
                    arr[i] = comp
            
            # Convert to numpy array
            return np.ctypeslib.as_array(arr)

        @property
        def handle(self) -> World_p:
            return self._handle

    return partial(WorldHandle)
