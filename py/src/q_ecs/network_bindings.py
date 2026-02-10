import ctypes
from typing import Callable

from q_ecs.types import World_p, ComponentDescriptor_p


class Buffer(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.POINTER(ctypes.c_uint8)),
        ("size", ctypes.c_size_t),
        ("capacity", ctypes.c_size_t),
    ]


ComponentPathResolver = ctypes.CFUNCTYPE(ctypes.c_char_p, ComponentDescriptor_p)
ComponentPathLookup = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_char_p)


def mk_network_factory(lib_path: str):
    lib = ctypes.CDLL(lib_path)
    
    lib.buffer_create.argtypes = [ctypes.c_size_t]
    lib.buffer_create.restype = ctypes.POINTER(Buffer)
    
    lib.buffer_destroy.argtypes = [ctypes.POINTER(Buffer)]
    lib.buffer_destroy.restype = None
    
    lib.world_serialize.argtypes = [World_p, ctypes.POINTER(Buffer), ComponentPathResolver]
    lib.world_serialize.restype = None
    
    lib.network_create_server.argtypes = [ctypes.c_char_p, ctypes.c_int]
    lib.network_create_server.restype = ctypes.c_int
    
    lib.network_accept_client.argtypes = [ctypes.c_int]
    lib.network_accept_client.restype = ctypes.c_int
    
    lib.network_send_world.argtypes = [ctypes.c_int, World_p, ComponentPathResolver]
    lib.network_send_world.restype = ctypes.c_int
    
    lib.network_connect_client.argtypes = [ctypes.c_char_p, ctypes.c_int]
    lib.network_connect_client.restype = ctypes.c_int
    
    lib.network_receive_data.argtypes = [ctypes.c_int, ctypes.POINTER(Buffer)]
    lib.network_receive_data.restype = ctypes.c_int
    
    lib.world_deserialize.argtypes = [ctypes.POINTER(Buffer), ComponentPathLookup]
    lib.world_deserialize.restype = World_p
    
    lib.network_close.argtypes = [ctypes.c_int]
    lib.network_close.restype = None
    
    class NetworkHandle:
        def __init__(self, host: str, port: int):
            self.lib = lib
            self.server_fd = lib.network_create_server(host.encode('utf-8'), port)
            if self.server_fd < 0:
                raise RuntimeError(f"Failed to create server on {host}:{port}")
            self.clients = []
        
        def __del__(self):
            for client_fd in self.clients:
                self.lib.network_close(client_fd)
            if hasattr(self, 'server_fd') and self.server_fd >= 0:
                self.lib.network_close(self.server_fd)
        
        def accept_client(self) -> int:
            client_fd = self.lib.network_accept_client(self.server_fd)
            if client_fd >= 0:
                self.clients.append(client_fd)
            return client_fd
        
        def send_world(self, client_fd: int, world_handle: World_p, path_resolver: ComponentPathResolver) -> bool:
            result = self.lib.network_send_world(client_fd, world_handle, path_resolver)
            return result == 0
        
        def serialize_world(self, world_handle: World_p, path_resolver: ComponentPathResolver) -> bytes:
            buf = self.lib.buffer_create(4096)
            try:
                # Keep references to prevent GC during C function execution
                self._active_resolver = path_resolver
                self.lib.world_serialize(world_handle, buf, path_resolver)
                data = ctypes.string_at(buf.contents.data, buf.contents.size)
                return data
            finally:
                self._active_resolver = None
                self.lib.buffer_destroy(buf)
        
        def close_client(self, client_fd: int):
            if client_fd in self.clients:
                self.clients.remove(client_fd)
            self.lib.network_close(client_fd)
    
    class NetworkClient:
        def __init__(self, host: str, port: int):
            self.lib = lib
            self.client_fd = lib.network_connect_client(host.encode('utf-8'), port)
            if self.client_fd < 0:
                raise RuntimeError(f"Failed to connect to {host}:{port}")
        
        def __del__(self):
            if hasattr(self, 'client_fd') and self.client_fd >= 0:
                self.lib.network_close(self.client_fd)
        
        def receive_world(self, path_lookup: ComponentPathLookup) -> World_p:
            buf = self.lib.buffer_create(4096)
            try:
                result = self.lib.network_receive_data(self.client_fd, buf)
                if result != 0:
                    return None
                
                world_handle = self.lib.world_deserialize(buf, path_lookup)
                return world_handle
            finally:
                self.lib.buffer_destroy(buf)
        
        def close(self):
            if self.client_fd >= 0:
                self.lib.network_close(self.client_fd)
                self.client_fd = -1
    
    return NetworkHandle, NetworkClient
