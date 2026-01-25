import ctypes
import Metal
from q_engine.alt.ecs.components import Component, World, Archetype
import numpy as np
from q_engine.alt.ecs.systems import aggregate, query


class Point(Component):
    def __init__(self) -> None:
        self.vector = np.zeros([0, 5])
    def add(self, i, size=1):
        if i + size >= self.vector.shape[0]:
            self.vector = np.concat([
                self.vector, np.zeros([size, 5])
            ])

def create_system(view, device, library, alpha, command_buffer):
    pipeline_desc = Metal.MTLRenderPipelineDescriptor.alloc().init()

    vert_fn = library.newFunctionWithName_("vert_main")
    frag_fn = library.newFunctionWithName_("frag_main")

    pipeline_desc.setVertexFunction_(vert_fn)
    pipeline_desc.setFragmentFunction_(frag_fn)

    vert_desc = Metal.MTLVertexDescriptor.alloc().init()

    a0 = vert_desc.attributes().objectAtIndexedSubscript_(0)
    a0.setFormat_(Metal.MTLVertexFormatFloat2)
    a0.setOffset_(0)
    a0.setBufferIndex_(0)
    
    a1 = vert_desc.attributes().objectAtIndexedSubscript_(1)
    a1.setFormat_(Metal.MTLVertexFormatFloat3)
    a1.setOffset_(2 * 4)
    a1.setBufferIndex_(0)
    
    layout = vert_desc.layouts().objectAtIndexedSubscript_(0)
    layout.setStride_((2 + 3) * 4)
    layout.setStepRate_(1)
    layout.setStepFunction_(Metal.MTLVertexStepFunctionPerVertex)

    pipeline_desc.setVertexDescriptor_(vert_desc)

    color_attachment = pipeline_desc.colorAttachments().objectAtIndexedSubscript_(0)
    color_attachment.setPixelFormat_(Metal.MTLPixelFormatBGRA8Unorm)
    color_attachment.setBlendingEnabled_(True)
    color_attachment.setRgbBlendOperation_(Metal.MTLBlendOperationAdd)
    color_attachment.setAlphaBlendOperation_(Metal.MTLBlendOperationAdd)
    color_attachment.setSourceRGBBlendFactor_(Metal.MTLBlendFactorSourceAlpha)
    color_attachment.setSourceAlphaBlendFactor_(Metal.MTLBlendFactorSourceAlpha)
    color_attachment.setDestinationRGBBlendFactor_(Metal.MTLBlendFactorOneMinusSourceAlpha)
    color_attachment.setDestinationAlphaBlendFactor_(Metal.MTLBlendFactorOneMinusSourceAlpha)

    pipeline, error = device.newRenderPipelineStateWithDescriptor_error_(pipeline_desc, None)
    assert not error
    
    @query
    def system(point: Point):
        cnt = point.vector.shape[0]

        if cnt < 1:
            return

        rpd = view.currentRenderPassDescriptor()
        encoder = command_buffer.renderCommandEncoderWithDescriptor_(rpd)
        encoder.setRenderPipelineState_(pipeline)

        verts = point.vector.flatten()
        num_floats = len(verts)
        buffer = device.newBufferWithBytes_length_options_(
            (ctypes.c_float * num_floats)(*verts),
            ctypes.sizeof(ctypes.c_float) * num_floats,
            Metal.MTLResourceStorageModeShared
        )
        
        encoder.setVertexBuffer_offset_atIndex_(buffer, 0, 0)
        encoder.drawPrimitives_vertexStart_vertexCount_(Metal.MTLPrimitiveTypeTriangle, 0, 3)
        encoder.endEncoding()
    return system


def bake(world: World):
    e = world.create_entity()
    world.add_component(e, set([Point]))
    e.archetype.components[Point].vector[e.index] = np.array([0.5, 0, 1, 1, 1])
    
    e = world.create_entity()
    world.add_component(e, set([Point]))
    e.archetype.components[Point].vector[e.index] = np.array([-0.5, 0, 1, 1, 1])

    e = world.create_entity()
    world.add_component(e, set([Point]))
    e.archetype.components[Point].vector[e.index] = np.array([0, 0.5, 1, 1, 1])

def simulate_fc(*args, **kwargs):
    def simulate(*a, **kw): ...
    return simulate

render_fc = aggregate([
    create_system
])
