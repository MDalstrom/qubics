import Metal
import numpy as np

from q_engine.application.render.camera import Camera
from q_engine.application.render.view import mk_perspective
from q_engine.ecs.components import Component, World, component
from q_engine.ecs.systems import query
from q_engine.ecs.types import Float32x4x4, Float32x4

@component
class Mesh(Component):
    vertices: Float32x4

@component
class Transform(Component):
    matrices: Float32x4x4

def create(device, view, library):
    pipeline_desc = Metal.MTLRenderPipelineDescriptor.alloc().init()
    pipeline_desc.setVertexFunction_(library.newFunctionWithName_("vertex_main"))
    pipeline_desc.setFragmentFunction_(library.newFunctionWithName_("fragment_main"))

    color_attachment = pipeline_desc.colorAttachments().objectAtIndexedSubscript_(0)
    color_attachment.setPixelFormat_(view.colorPixelFormat())
    color_attachment.setBlendingEnabled_(True)
    color_attachment.setRgbBlendOperation_(Metal.MTLBlendOperationAdd)
    color_attachment.setAlphaBlendOperation_(Metal.MTLBlendOperationAdd)
    color_attachment.setSourceRGBBlendFactor_(Metal.MTLBlendFactorSourceAlpha)
    color_attachment.setSourceAlphaBlendFactor_(Metal.MTLBlendFactorSourceAlpha)
    color_attachment.setDestinationRGBBlendFactor_(
        Metal.MTLBlendFactorOneMinusSourceAlpha
    )
    color_attachment.setDestinationAlphaBlendFactor_(
        Metal.MTLBlendFactorOneMinusSourceAlpha
    )

    pipeline, error = device.newRenderPipelineStateWithDescriptor_error_(
        pipeline_desc, None
    )
    assert pipeline, error

    def call(world: World, command_buffer):
        rpd = view.currentRenderPassDescriptor()
        encoder = command_buffer.renderCommandEncoderWithDescriptor_(rpd)
        encoder.setRenderPipelineState_(pipeline)

        def camera_system(camera: Camera, transform: Transform):
            view_matrix = np.linalg.inv(transform.matrices[0])
            x, y = view.drawableSize()
            proj_matrix = mk_perspective(camera.fov, x / y, camera.near, camera.far)
            vp_matrix = view_matrix @ proj_matrix
            view_proj_buffer = device.newBufferWithBytes_length_options_(
                vp_matrix.tobytes(),
                vp_matrix.nbytes,
                Metal.MTLResourceStorageModeManaged,
            )
            encoder.setVertexBuffer_offset_atIndex_(view_proj_buffer, 0, 2)

            def mesh_system(transform: Transform, mesh: Mesh):
                vertex_buffer = device.newBufferWithBytes_length_options_(
                    mesh.vertices.tobytes(),
                    mesh.vertices.nbytes,
                    Metal.MTLResourceStorageModeManaged,
                )
                encoder.setVertexBuffer_offset_atIndex_(vertex_buffer, 0, 0)

                instance_buffer = device.newBufferWithBytes_length_options_(
                    transform.matrices.tobytes(),
                    transform.matrices.nbytes,
                    Metal.MTLResourceStorageModeManaged,
                )
                encoder.setVertexBuffer_offset_atIndex_(instance_buffer, 0, 1)

                encoder.drawPrimitives_vertexStart_vertexCount_instanceCount_(
                    Metal.MTLPrimitiveTypeTriangle,
                    0,
                    mesh.vertices.shape[0],
                    transform.matrices.shape[0],
                )
            query(mesh_system)(world)
        query(camera_system)(world)
        encoder.endEncoding()

    return call
