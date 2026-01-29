import Metal
import numpy as np

from q_engine.application.render.camera import Camera
from q_engine.application.render.view import mk_ortho, mk_view, mk_perspective
from q_engine.ecs.components import Component, World
from q_engine.ecs.systems import query


class Mesh(Component):
    def __init__(self):
        self.vertices = np.zeros([1, 4], dtype=np.float32, order="F")

    def add(self, i, size=1):
        if i + size > self.vertices.shape[0]:
            self.vertices = np.concat([self.vertices, self.vertices])


class Transform(Component):
    def __init__(self):
        self.matrices = np.zeros([0, 4, 4], order="F")

    def add(self, i: int, size: int = 1):
        current_size = self.matrices.shape[0]
        required_size = i + size
        if required_size > current_size:
            to_add = required_size - current_size
            new_matrices = np.array(
                [np.identity(4, dtype=np.float32) for _ in range(to_add)]
            )
            if current_size > 0:
                self.matrices = np.concatenate([self.matrices, new_matrices])
            else:
                self.matrices = new_matrices


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

        @query
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

            @query
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

            mesh_system(world)

        camera_system(world)

        encoder.endEncoding()

    return call
