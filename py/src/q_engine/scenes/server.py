from q_engine.scenes.shared import Position, Velocity
import threading
from q_engine.network.network import Network
from q_engine.bootstrap import get_config
from bridge.c_bindings import mk_world_factory
from bridge.types import World
import ctypes


def get_tick(config=get_config()):
    world_handle = mk_world_factory(config.ecslib)()
    world_handle.create_entity([Position, Velocity])

    network = Network(world_handle, host='127.0.0.1', listen_port=18488)
    threading.Thread(target=network.poll_new_connections, daemon=True).start()
    
    systems = []
    
    if config.render3dlib:
        render3d = ctypes.CDLL(config.render3dlib)
        render3d.render_3d_create.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        render3d.render_3d_create.restype = ctypes.c_void_p
        
        render_fn_ptr = render3d.render_3d_create(
            config.metalbootlib.encode('utf-8'),
            config.shaderslib.encode('utf-8'),
            b"vertex_main,fragment_main"
        )
        
        if render_fn_ptr:
            systems.append(ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)(render_fn_ptr))
    
    def tick(command_buffer):
        world_p = world_handle.handle
        world_ptr = ctypes.cast(world_p, ctypes.POINTER(World))
        
        network.send_world(world_ptr.contents)
        
        for system in systems:
            system(world_p, command_buffer)

    return tick


    network = Network(world_handle, host='127.0.0.1', listen_port=18488)
    polling_thread = threading.Thread(target=network.poll_new_connections, daemon=True)
    polling_thread.start()
    
    device = None
    view = None
    library = None
    pipeline = None
    
    if config.shaderslib and config.metalbootlib:
        metalboot = ctypes.CDLL(config.metalbootlib)
        metalboot.metal_get_device.argtypes = []
        metalboot.metal_get_device.restype = ctypes.c_void_p
        metalboot.metal_get_view.argtypes = []
        metalboot.metal_get_view.restype = ctypes.c_void_p
        metalboot.metal_load_library.argtypes = [ctypes.c_char_p]
        metalboot.metal_load_library.restype = ctypes.c_void_p
        
        device_ptr = metalboot.metal_get_device()
        view_ptr = metalboot.metal_get_view()
        
        if device_ptr and view_ptr:
            device = Metal.MTLDevice(c_void_p=device_ptr)
            view = Metal.MTKView(c_void_p=view_ptr)
            library_ptr = metalboot.metal_load_library(config.shaderslib.encode('utf-8'))
            if library_ptr:
                library = Metal.MTLLibrary(c_void_p=library_ptr)
                
                pipeline_desc = Metal.MTLRenderPipelineDescriptor.alloc().init()
                pipeline_desc.setVertexFunction_(library.newFunctionWithName_("vertex_main"))
                pipeline_desc.setFragmentFunction_(library.newFunctionWithName_("fragment_main"))
                color_attachment = pipeline_desc.colorAttachments().objectAtIndexedSubscript_(0)
                color_attachment.setPixelFormat_(view.colorPixelFormat())
                pipeline, error = device.newRenderPipelineStateWithDescriptor_error_(pipeline_desc, None)
                assert pipeline, error

    from q_engine.application.render.mesh import cube, cube_colors
    vertices = cube()
    colors = cube_colors()
    
    camera_pos = np.array([0.0, 0.0, -8.0, 1.0], dtype=np.float32)
    view_matrix = np.eye(4, dtype=np.float32)
    view_matrix[3, :] = camera_pos
    view_matrix = np.linalg.inv(view_matrix)
    
    aspect = 1.0
    fov = 65.0 * np.pi / 180.0
    near = 0.1
    far = 100.0
    f = 1.0 / np.tan(fov * 0.5)
    projection = np.array([
        [f / aspect, 0, 0, 0],
        [0, f, 0, 0],
        [0, 0, far / (far - near), 1],
        [0, 0, -near * far / (far - near), 0]
    ], dtype=np.float32)
    
    vp_matrix = view_matrix @ projection
    
    rotation = 0.0
    
    def tick(command_buffer):
        nonlocal rotation
        
        world_p = world_handle.handle
        world_ptr = ctypes.cast(world_p, ctypes.POINTER(World))
        world = world_ptr.contents
        
        network.send_world(world)
        
        if device and view and pipeline:
            cb = Metal.MTLCommandBuffer(c_void_p=command_buffer)
            rpd = view.currentRenderPassDescriptor()
            encoder = cb.renderCommandEncoderWithDescriptor_(rpd)
            encoder.setRenderPipelineState_(pipeline)
            
            view_proj_buffer = device.newBufferWithBytes_length_options_(
                vp_matrix.tobytes(), vp_matrix.nbytes, Metal.MTLResourceStorageModeManaged
            )
            encoder.setVertexBuffer_offset_atIndex_(view_proj_buffer, 0, 3)
            
            vertex_buffer = device.newBufferWithBytes_length_options_(
                vertices.tobytes(), vertices.nbytes, Metal.MTLResourceStorageModeManaged
            )
            encoder.setVertexBuffer_offset_atIndex_(vertex_buffer, 0, 0)
            
            color_buffer = device.newBufferWithBytes_length_options_(
                colors.tobytes(), colors.nbytes, Metal.MTLResourceStorageModeManaged
            )
            encoder.setVertexBuffer_offset_atIndex_(color_buffer, 0, 1)
            
            axis = np.array([1.0, 1.0, 0.0])
            axis = axis / np.linalg.norm(axis)
            c = np.cos(rotation)
            s = np.sin(rotation)
            t = 1 - c
            x, y, z = axis
            model_matrix = np.array([
                [t*x*x + c, t*x*y + z*s, t*x*z - y*s, 0],
                [t*x*y - z*s, t*y*y + c, t*y*z + x*s, 0],
                [t*x*z + y*s, t*y*z - x*s, t*z*z + c, 0],
                [0, 0, 0, 1]
            ], dtype=np.float32)
            
            instance_buffer = device.newBufferWithBytes_length_options_(
                model_matrix.tobytes(), model_matrix.nbytes, Metal.MTLResourceStorageModeManaged
            )
            encoder.setVertexBuffer_offset_atIndex_(instance_buffer, 0, 2)
            
            encoder.drawPrimitives_vertexStart_vertexCount_instanceCount_(
                Metal.MTLPrimitiveTypeTriangle, 0, len(vertices), 1
            )
            
            encoder.endEncoding()
            rotation += 0.01

    return tick
