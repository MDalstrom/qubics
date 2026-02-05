import ctypes
from ctypes import c_void_p, c_uint32, c_size_t, c_char_p, c_bool, POINTER
from pathlib import Path
from typing import Optional

_lib_path = Path(__file__).parent.parent.parent.parent.parent / "build" / "libecs_core.dylib"
_lib = ctypes.CDLL(str(_lib_path))

Entity = c_uint32
ComponentTypeId = c_uint32
class World_p(c_void_p):
    pass

class Chunk_p(c_void_p):
    pass

class ChunkIterator(ctypes.Structure):
    _fields_ = [
        ("chunks", POINTER(Chunk_p)),
        ("count", c_uint32)
    ]
_lib.world_create.argtypes = [c_uint32]
_lib.world_create.restype = World_p

_lib.world_destroy.argtypes = [World_p]
_lib.world_destroy.restype = None

_lib.world_register_component_type.argtypes = [World_p, c_char_p]
_lib.world_register_component_type.restype = ComponentTypeId

_lib.world_create_entity.argtypes = [World_p, POINTER(ComponentTypeId), c_uint32]
_lib.world_create_entity.restype = Entity

_lib.world_destroy_entity.argtypes = [World_p, Entity]
_lib.world_destroy_entity.restype = None

_lib.world_entity_exists.argtypes = [World_p, Entity]
_lib.world_entity_exists.restype = c_bool

_lib.world_query_chunks.argtypes = [World_p, POINTER(ComponentTypeId), c_uint32]
_lib.world_query_chunks.restype = ChunkIterator

_lib.chunk_iterator_free.argtypes = [POINTER(ChunkIterator)]
_lib.chunk_iterator_free.restype = None

_lib.chunk_get_component_buffer.argtypes = [Chunk_p, ComponentTypeId]
_lib.chunk_get_component_buffer.restype = c_void_p

_lib.chunk_set_component_buffer.argtypes = [Chunk_p, ComponentTypeId, c_void_p, c_size_t]
_lib.chunk_set_component_buffer.restype = c_bool

_lib.chunk_get_component_buffer_size.argtypes = [Chunk_p, ComponentTypeId]
_lib.chunk_get_component_buffer_size.restype = c_size_t

_lib.chunk_get_count.argtypes = [Chunk_p]
_lib.chunk_get_count.restype = c_uint32

_lib.chunk_add_entity.argtypes = [Chunk_p, Entity]
_lib.chunk_add_entity.restype = c_bool

_lib.chunk_remove_entity.argtypes = [Chunk_p, c_uint32]
_lib.chunk_remove_entity.restype = None

_lib.chunk_get_component_buffer_size.argtypes = [Chunk_p, ComponentTypeId]
_lib.chunk_get_component_buffer_size.restype = c_size_t

class WorldHandle:
    
    def __init__(self, chunk_capacity: int = 1000):
        self._handle = _lib.world_create(chunk_capacity)
        if not self._handle:
            raise RuntimeError("Failed to create ECS world")
        self._component_types = {}
    
    def __del__(self):
        if hasattr(self, '_handle') and self._handle:
            _lib.world_destroy(self._handle)
    
    def register_component_type(self, t: type) -> ComponentTypeId:
        if t in self._component_types:
            return self._component_types[t]
        name = t.__name__
        id = _lib.world_register_component_type(self._handle, name.encode('utf-8'))
        self._component_types[t] = id
        return id
    
    def create_entity(self, component_types: list[ComponentTypeId]) -> Entity:
        count = len(component_types)
        if count == 0:
            return _lib.world_create_entity(self._handle, None, 0)
        
        array_type = ComponentTypeId * count
        types_array = array_type(*component_types)
        return _lib.world_create_entity(self._handle, types_array, count)
    
    def destroy_entity(self, entity: Entity):
        _lib.world_destroy_entity(self._handle, entity)
    
    def entity_exists(self, entity: Entity) -> bool:
        return _lib.world_entity_exists(self._handle, entity)
    
    def query_chunks(self, component_types: list[ComponentTypeId]) -> 'ChunkIteratorHandle':
        count = len(component_types)
        array_type = ComponentTypeId * count
        types_array = array_type(*component_types)
        iterator = _lib.world_query_chunks(self._handle, types_array, count)
        return ChunkIteratorHandle(iterator)
    
    @property
    def handle(self) -> World_p:
        return self._handle


class ChunkIteratorHandle:
    
    def __init__(self, iterator: ChunkIterator):
        self._iterator = iterator
    
    def __del__(self):
        if hasattr(self, '_iterator'):
            _lib.chunk_iterator_free(ctypes.byref(self._iterator))
    
    def __len__(self) -> int:
        return self._iterator.count
    
    def __iter__(self):
        for i in range(self._iterator.count):
            yield ChunkHandle(self._iterator.chunks[i])
    
    def get_chunk(self, index: int) -> 'ChunkHandle':
        if index >= self._iterator.count:
            raise IndexError(f"Chunk index {index} out of range (count: {self._iterator.count})")
        return ChunkHandle(self._iterator.chunks[index])


class ChunkHandle:
    
    def __init__(self, chunk: Chunk_p):
        self._handle = chunk
    
    def get_component_buffer(self, component_type: ComponentTypeId) -> Optional[int]:
        ptr = _lib.chunk_get_component_buffer(self._handle, component_type)
        return ptr if ptr else None

    def get_component_buffer_size(self, component_type: ComponentTypeId) -> int:
        return _lib.chunk_get_component_buffer_size(self._handle, component_type)
    
    def get_component_buffer_bytes(self, component_type: ComponentTypeId) -> Optional[bytes]:
        ptr = _lib.chunk_get_component_buffer(self._handle, component_type)
        if not ptr:
            return None
        size = _lib.chunk_get_component_buffer_size(self._handle, component_type)
        return ctypes.string_at(ptr, size)

    def get_component_buffer_view(self, component_type: ComponentTypeId) -> Optional[memoryview]:
        ptr = _lib.chunk_get_component_buffer(self._handle, component_type)
        if not ptr:
            return None
        size = _lib.chunk_get_component_buffer_size(self._handle, component_type)
        addr = ctypes.cast(ptr, c_void_p).value
        buf_type = ctypes.c_char * size
        buf = buf_type.from_address(addr)
        return memoryview(buf)

    def set_component_buffer(self, component_type: ComponentTypeId, data: bytes) -> bool:
        size = len(data)
        c_buffer = ctypes.create_string_buffer(data, size)
        ptr = ctypes.cast(c_buffer, c_void_p)
        result = _lib.chunk_set_component_buffer(
            self._handle, 
            component_type, 
            ptr, 
            size
        )
        if not hasattr(self, '_buffers'):
            self._buffers = {}
        self._buffers[component_type] = c_buffer
        return result
    
    def add_entity(self, entity: Entity) -> bool:
        return _lib.chunk_add_entity(self._handle, entity)
    
    def remove_entity(self, index: int):
        _lib.chunk_remove_entity(self._handle, index)
    
    @property
    def count(self) -> int:
        return _lib.chunk_get_count(self._handle)
    
    @property
    def handle(self) -> Chunk_p:
        return self._handle
def create_world(chunk_capacity: int = 1000) -> WorldHandle:
    return WorldHandle(chunk_capacity)

