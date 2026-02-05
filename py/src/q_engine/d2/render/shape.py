from q_generated.components.Shape import Shape
from q_generated.components.Transform2D import Transform2D
from q_generated.components.CameraCache import CameraCache
from q_engine.ecs.world import World
from q_generated.units.Vector4 import Vector4
import Metal
import numpy as np


def mk_shape_system(device, view, library):
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
    color_attachment.setDestinationRGBBlendFactor_(Metal.MTLBlendFactorOneMinusSourceAlpha)
    color_attachment.setDestinationAlphaBlendFactor_(Metal.MTLBlendFactorOneMinusSourceAlpha)

    pipeline, error = device.newRenderPipelineStateWithDescriptor_error_(pipeline_desc, None)
    assert pipeline, error

    def system(world: World, command_buffer):
        rpd = view.currentRenderPassDescriptor()
        encoder = command_buffer.renderCommandEncoderWithDescriptor_(rpd)
        encoder.setRenderPipelineState_(pipeline)

        camera_comp_id = world.register_component_type(CameraCache)
        vp_matrix = np.eye(4, dtype=np.float32)
        
        for chunk in world.query_chunks([camera_comp_id]):
            camera_data = chunk.get_component_buffer_bytes(camera_comp_id)
            if camera_data:
                camera = CameraCache.GetRootAs(camera_data, 0)
                if camera.ViewProjectionLength() > 0:
                    mat = camera.ViewProjection(0)
                    vec3 = Vector4()
                    m0 = mat.M0(vec3)
                    m1 = mat.M1(vec3)
                    m2 = mat.M2(vec3)
                    m3 = mat.M3(vec3)
                    vp_matrix = np.array([
                        [m0.X(), m0.Y(), m0.Z(), m0.W()],
                        [m1.X(), m1.Y(), m1.Z(), m1.W()],
                        [m2.X(), m2.Y(), m2.Z(), m2.W()],
                        [m3.X(), m3.Y(), m3.Z(), m3.W()]
                    ], dtype=np.float32)
                break
        
        view_proj_buffer = device.newBufferWithBytes_length_options_(
            vp_matrix.tobytes(),
            vp_matrix.nbytes,
            Metal.MTLResourceStorageModeManaged,
        )
        encoder.setVertexBuffer_offset_atIndex_(view_proj_buffer, 0, 3)

        # Query for shapes with transforms
        shape_comp_id = world.register_component_type(Shape)
        transform_comp_id = world.register_component_type(Transform2D)
        
        for chunk in world.query_chunks([shape_comp_id, transform_comp_id]):
            shape_data = chunk.get_component_buffer_bytes(shape_comp_id)
            transform_data = chunk.get_component_buffer_bytes(transform_comp_id)
            
            if not shape_data or not transform_data:
                continue
            
            shape = Shape.GetRootAs(shape_data, 0)
            transform = Transform2D.GetRootAs(transform_data, 0)
            
            vertex_count = shape.VerticesLength()
            if vertex_count == 0:
                continue
            
            vertices = np.zeros((vertex_count, 2), dtype=np.float32)
            colors = np.zeros((vertex_count, 4), dtype=np.float32)
            
            for i in range(vertex_count):
                v = shape.Vertices(i)
                vertices[i] = [v.X(), v.Y()]
                
                c = shape.Colors(i)
                colors[i] = [c.R(), c.G(), c.B(), c.A()]
            
            vertex_buffer = device.newBufferWithBytes_length_options_(
                vertices.tobytes(),
                vertices.nbytes,
                Metal.MTLResourceStorageModeManaged,
            )
            encoder.setVertexBuffer_offset_atIndex_(vertex_buffer, 0, 0)

            color_buffers = device.newBufferWithBytes_length_options_(
                colors.tobytes(),
                colors.nbytes,
                Metal.MTLResourceStorageModeManaged,
            )
            encoder.setVertexBuffer_offset_atIndex_(color_buffers, 0, 1)

            # Get transform matrices
            matrix_count = transform.MatricesLength()
            for mat_idx in range(max(1, matrix_count)):
                if matrix_count > 0:
                    mat = transform.Matrices(mat_idx)
                    m0 = mat.M0(vec3)
                    m1 = mat.M1(vec3)
                    m2 = mat.M2(vec3)
                    transform_mat = np.array([
                        [m0.X(), m0.Y(), m0.Z(), 0.0],
                        [m1.X(), m1.Y(), m1.Z(), 0.0],
                        [m2.X(), m2.Y(), m2.Z(), 0.0],
                        [0.0, 0.0, 0.0, 1.0]
                    ], dtype=np.float32)
                else:
                    transform_mat = np.eye(4, dtype=np.float32)
                
                instance_buffer = device.newBufferWithBytes_length_options_(
                    transform_mat.tobytes(),
                    transform_mat.nbytes,
                    Metal.MTLResourceStorageModeManaged,
                )
                encoder.setVertexBuffer_offset_atIndex_(instance_buffer, 0, 2)

                encoder.drawPrimitives_vertexStart_vertexCount_instanceCount_(
                    Metal.MTLPrimitiveTypeTriangle,
                    0,
                    vertex_count,
                    1,
                )

        encoder.endEncoding()

    return system
