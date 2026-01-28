import Metal
import numpy as np

from q_engine.ecs.components import Component, World
from q_engine.ecs.systems import query
from q_engine.application.render.view import viewProj

class Mesh(Component):
    def __init__(self):
        self.vertices = np.zeros([0, 4], order='F')

    def add(self, i, size = 1): ...

class Transform(Component):
    def __init__(self):
        self.matrices = np.zeros([0, 4, 4], order='F')

    def add(self, i: int, size: int = 1):
        if i + size >= self.matrices.shape[0]:
            self.matrices = np.concatenate([self.matrices, self.matrices])

def create(device, view, library):
    pipeline_desc = Metal.MTLRenderPipelineDescriptor.alloc().init()
    pipeline_desc.setVertexFunction_(
        library.newFunctionWithName_("vertex_main")
    )
    pipeline_desc.setFragmentFunction_(
        library.newFunctionWithName_("fragment_main")
    )

    color_attachment = pipeline_desc.colorAttachments().objectAtIndexedSubscript_(0)
    color_attachment.setPixelFormat_(view.colorPixelFormat())
    color_attachment.setBlendingEnabled_(True)
    color_attachment.setRgbBlendOperation_(Metal.MTLBlendOperationAdd)
    color_attachment.setAlphaBlendOperation_(Metal.MTLBlendOperationAdd)
    color_attachment.setSourceRGBBlendFactor_(Metal.MTLBlendFactorSourceAlpha)
    color_attachment.setSourceAlphaBlendFactor_(Metal.MTLBlendFactorSourceAlpha)
    color_attachment.setDestinationRGBBlendFactor_(Metal.MTLBlendFactorOneMinusSourceAlpha)
    color_attachment.setDestinationAlphaBlendFactor_(Metal.MTLBlendFactorOneMinusSourceAlpha)

    pipeline_desc.setDepthAttachmentPixelFormat_(Metal.MTLPixelFormatInvalid)

    pipeline, error = device.newRenderPipelineStateWithDescriptor_error_(pipeline_desc, None)
    assert not error

    def call(world: World, command_buffer):
        rpd = view.currentRenderPassDescriptor()
        if not rpd:
            return

        encoder = command_buffer.renderCommandEncoderWithDescriptor_(rpd)
        encoder.setRenderPipelineState_(pipeline)
        encoder.setCullMode_(Metal.MTLCullModeNone)

        view_proj_buffer = device.newBufferWithBytes_length_options_(
            viewProj.tobytes(),
            viewProj.nbytes,
            Metal.MTLResourceStorageModeManaged
        )
        encoder.setVertexBuffer_offset_atIndex_(view_proj_buffer, 0, 2)

        @query
        def system(transform: Transform, mesh: Mesh):
            print(f"[Debug] System query triggered. Found {mesh.vertices.shape[0]} vertices and {transform.matrices.shape[0]} instances.")
            if not mesh.vertices.size or not transform.matrices.size:
                print("[Debug] -> Skipping render: mesh or transform data is empty.")
                return

            print(f"[Debug] -> Sample Vertex [0]: {mesh.vertices[0]}")
            print(f"[Debug] -> Sample Instance Matrix [0]:\n{transform.matrices[0]}")
            print(f"[Debug] -> View-Projection Matrix:\n{viewProj}")

            vertex_buffer = device.newBufferWithBytes_length_options_(
                mesh.vertices.tobytes(),
                mesh.vertices.nbytes,
                Metal.MTLResourceStorageModeManaged
            )
            instance_buffer = device.newBufferWithBytes_length_options_(
                transform.matrices.tobytes(),
                transform.matrices.nbytes,
                Metal.MTLResourceStorageModeManaged
            )

            encoder.setVertexBuffer_offset_atIndex_(vertex_buffer, 0, 0)
            encoder.setVertexBuffer_offset_atIndex_(instance_buffer, 0, 1)

            encoder.drawPrimitives_vertexStart_vertexCount_instanceCount_(
                Metal.MTLPrimitiveTypeTriangle,
                0,
                mesh.vertices.shape[0],
                transform.matrices.shape[0]
            )

        system(world)
        encoder.endEncoding()

    return call
