import ctypes
from pathlib import Path


class MetalRenderSystem:
    def __init__(self, metalboot_lib, shader_lib_path):
        self.metalboot = ctypes.CDLL(metalboot_lib)
        
        self.metalboot.metal_get_device.argtypes = []
        self.metalboot.metal_get_device.restype = ctypes.c_void_p
        
        self.metalboot.metal_load_library.argtypes = [ctypes.c_char_p]
        self.metalboot.metal_load_library.restype = ctypes.c_void_p
        
        self.device = None
        self.library = None
        self.shader_lib_path = shader_lib_path
    
    def initialize(self):
        self.device = self.metalboot.metal_get_device()
        if self.device and self.shader_lib_path:
            path_bytes = str(Path(self.shader_lib_path).resolve()).encode('utf-8')
            self.library = self.metalboot.metal_load_library(path_bytes)
    
    def get_device(self):
        return self.device

    def get_library(self):
        return self.library
