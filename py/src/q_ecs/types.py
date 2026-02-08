import ctypes
from typing import Protocol

Component = ctypes.Structure

World_p = ctypes.c_void_p
Chunk_p = ctypes.c_void_p

class ComponentDescriptor(ctypes.Structure):
    _fields_ = [("stride", ctypes.c_size_t)]

ComponentDescriptor_p = ctypes.POINTER(ComponentDescriptor)

class Archetype(ctypes.Structure):
    _fields_ = [
        ("descriptors", ctypes.POINTER(ComponentDescriptor_p)),
        ("length", ctypes.c_size_t),
    ]

class Entity(ctypes.Structure):
    _fields_ = [
        ("chunk", Chunk_p),
        ("idx", ctypes.c_size_t)
    ]

class ChunkContainer(ctypes.Structure):
    pass

ChunkContainer_p = ctypes.POINTER(ChunkContainer)

class Query(ctypes.Structure):
    _fields_ = [
        ("containers", ctypes.POINTER(ChunkContainer_p)),
        ("count", ctypes.c_size_t),
    ]

ChunkContainer._fields_ = [
    ("chunks", ctypes.c_void_p),
    ("chunks_count", ctypes.c_size_t),
    ("archetype", Archetype),
]

class World(Protocol):
    def create_entity(self, components: list[type[Component]]) -> Entity: ...
    def remove_entity(self, entity: Entity): ...
    def query(self, components: list[type[Component]]) -> Query: ...
