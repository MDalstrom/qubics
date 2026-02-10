import ctypes
from typing import Protocol


Component = ctypes.Structure

class ComponentDescriptor(ctypes.Structure):
    _fields_ = [("stride", ctypes.c_size_t)]
ComponentDescriptor_p = ctypes.POINTER(ComponentDescriptor)

class Archetype(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_size_t),
        ("descriptors", ctypes.POINTER(ComponentDescriptor_p)),
    ]

class ChunkContainer(ctypes.Structure): ...
ChunkContainer_p = ctypes.POINTER(ChunkContainer)

class Chunk(ctypes.Structure): ...
Chunk_p = ctypes.POINTER(Chunk)

Chunk._fields_ = [
    ("entities_count", ctypes.c_size_t),
    ("container", ChunkContainer_p),
    ("buffers", ctypes.POINTER(ctypes.c_void_p)),
]
ChunkContainer._fields_ = [
    ("archetype", Archetype),
    ("chunks_count", ctypes.c_size_t),
    ("chunks", Chunk_p),
]

class World(ctypes.Structure):
    _fields_ = [
        ("containers_count", ctypes.c_size_t),
        ("containers", ChunkContainer_p),
    ]
World_p = ctypes.c_void_p

class Entity(ctypes.Structure):
    _fields_ = [
        ("chunk", Chunk_p),
        ("idx", ctypes.c_size_t)
    ]

class Query(ctypes.Structure):
    _fields_ = [
        ("containers", ctypes.POINTER(ChunkContainer_p)),
        ("count", ctypes.c_size_t),
    ]

class WorldMethods(Protocol):
    handle: int
    descriptors_authority: dict[type, int]
    def create_entity(self, components: list[type[Component]]) -> Entity: ...
    def remove_entity(self, entity: Entity): ...
    def query(self, components: list[type[Component]]) -> Query: ...
