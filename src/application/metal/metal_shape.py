from dataclasses import dataclass
from application.collisions.n import Shape
from application.metal.display_metal import MetalViewport
from application.transform import Transform
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World
import Metal
import array


@dataclass
class ShapeRenderer:
    color: tuple[float, float, float, float]


# Shader source for filled colored shapes
SHADER_SOURCE = """
#include <metal_stdlib>
using namespace metal;

struct Vertex {
    float2 position [[attribute(0)]];
};

struct VertexOut {
    float4 position [[position]];
};

vertex VertexOut vertex_main(uint vertexID [[vertex_id]],
                             constant Vertex *vertices [[buffer(0)]]) {
    VertexOut out;
    out.position = float4(vertices[vertexID].position, 0.0, 1.0);
    return out;
}

fragment float4 fragment_main(constant float4 &color [[buffer(0)]]) {
    return color;
}
"""


_pipeline_cache = {}


def _get_or_create_pipeline(device):
    """Create or retrieve cached render pipeline."""
    if device in _pipeline_cache:
        return _pipeline_cache[device]
    
    library = device.newLibraryWithSource_options_error_(SHADER_SOURCE, None, None)[0]
    if library is None:
        raise RuntimeError("Failed to compile shader library")
    
    vertex_function = library.newFunctionWithName_("vertex_main")
    fragment_function = library.newFunctionWithName_("fragment_main")
    
    pipeline_descriptor = Metal.MTLRenderPipelineDescriptor.alloc().init()
    pipeline_descriptor.setVertexFunction_(vertex_function)
    pipeline_descriptor.setFragmentFunction_(fragment_function)
    color_attachment = pipeline_descriptor.colorAttachments().objectAtIndexedSubscript_(0)
    color_attachment.setPixelFormat_(Metal.MTLPixelFormatBGRA8Unorm)
    color_attachment.setBlendingEnabled_(True)
    color_attachment.setRgbBlendOperation_(Metal.MTLBlendOperationAdd)
    color_attachment.setAlphaBlendOperation_(Metal.MTLBlendOperationAdd)
    color_attachment.setSourceRGBBlendFactor_(Metal.MTLBlendFactorSourceAlpha)
    color_attachment.setSourceAlphaBlendFactor_(Metal.MTLBlendFactorSourceAlpha)
    color_attachment.setDestinationRGBBlendFactor_(Metal.MTLBlendFactorOneMinusSourceAlpha)
    color_attachment.setDestinationAlphaBlendFactor_(Metal.MTLBlendFactorOneMinusSourceAlpha)
    
    pipeline_state = device.newRenderPipelineStateWithDescriptor_error_(pipeline_descriptor, None)[0]
    if pipeline_state is None:
        raise RuntimeError("Failed to create render pipeline state")
    
    _pipeline_cache[device] = pipeline_state
    return pipeline_state


@for_each
def draw_shape_system(world: World, __: Entity, viewport: MetalViewport, viewport_transform: Transform):
    """System that draws shapes in the Metal viewport."""
    
    drawable = viewport.view.currentDrawable()
    if drawable is None:
        return
    
    descriptor = viewport.view.currentRenderPassDescriptor()
    if descriptor is None:
        return
    
    device = viewport.view.device()
    command_queue = device.newCommandQueue()
    command_buffer = command_queue.commandBuffer()
    encoder = command_buffer.renderCommandEncoderWithDescriptor_(descriptor)
    
    pipeline_state = _get_or_create_pipeline(device)
    encoder.setRenderPipelineState_(pipeline_state)
    
    # Get viewport's world transform for camera/origin offset
    viewport_world_matrix = viewport_transform.get_world_matrix()
    viewport_position = Transform.get_position(viewport_world_matrix)
    
    @for_each
    def draw_shapes(_: World, __: Entity, shape: Shape, shape_transform: Transform, renderer: ShapeRenderer):
        world_matrix = shape_transform.get_world_matrix()
        
        # Convert edges to ordered vertices
        vertices = []
        for p1, _ in shape.edges:
            world_p = world_matrix @ p1
            
            # Apply viewport transform (camera offset)
            relative_x = world_p.x - viewport_position.x
            relative_y = world_p.y - viewport_position.y
            
            # Normalize to Metal's coordinate system using virtual size
            width, height = viewport.size
            x = (relative_x / width) * 2.0
            y = (relative_y / height) * 2.0  # Flipped Y-axis for bottom-left origin
            
            vertices.extend([x, y])
        
        if len(vertices) < 6:  # Need at least 3 vertices for a triangle
            return
        
        # Convert polygon to triangle fan manually (center + vertices)
        # Calculate center point
        num_verts = len(vertices) // 2
        center_x = sum(vertices[i] for i in range(0, len(vertices), 2)) / num_verts
        center_y = sum(vertices[i] for i in range(1, len(vertices), 2)) / num_verts
        
        # Build triangles: center -> v[i] -> v[i+1]
        triangles = []
        for i in range(num_verts):
            triangles.extend([center_x, center_y])
            triangles.extend([vertices[i*2], vertices[i*2+1]])
            next_i = (i + 1) % num_verts
            triangles.extend([vertices[next_i*2], vertices[next_i*2+1]])
        
        vertex_data = array.array('f', triangles)
        vertex_buffer = device.newBufferWithBytes_length_options_(
            vertex_data.tobytes(),
            len(vertex_data) * 4,
            Metal.MTLResourceStorageModeShared
        )
        
        color_data = array.array('f', renderer.color)
        color_buffer = device.newBufferWithBytes_length_options_(
            color_data.tobytes(),
            len(color_data) * 4,
            Metal.MTLResourceStorageModeShared
        )
        
        encoder.setVertexBuffer_offset_atIndex_(vertex_buffer, 0, 0)
        encoder.setFragmentBuffer_offset_atIndex_(color_buffer, 0, 0)
        encoder.drawPrimitives_vertexStart_vertexCount_(
            Metal.MTLPrimitiveTypeTriangle,
            0,
            len(triangles) // 2
        )
    
    draw_shapes(world)
    
    encoder.endEncoding()
    command_buffer.presentDrawable_(drawable)
    command_buffer.commit()
