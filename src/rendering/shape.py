from .metal_shape import ShapeRenderer
from application.collisions.n import Shape
from .factory import RenderingState
from application.transform import Transform
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World
import Metal
import array

@for_each
def draw_shape_system(world: World, __: Entity, state: RenderingState, viewport_transform: Transform):
    viewport_world_matrix = viewport_transform.get_world_matrix()
    viewport_position = Transform.get_position(viewport_world_matrix)
    viewport_scale = Transform.get_scale(viewport_world_matrix)  

    @for_each
    def draw_shapes(_: World, __: Entity, shape: Shape, shape_transform: Transform, renderer: ShapeRenderer):
        world_matrix = shape_transform.get_world_matrix()
        
        # Convert edges to ordered vertices
        vertices = []
        for p1, ___ in shape.edges:
            world_p = world_matrix @ p1
            
            # Apply viewport transform (camera offset)
            relative_x = world_p.x - viewport_position.x
            relative_y = world_p.y - viewport_position.y
            
            # Normalize to Metal's coordinate system using virtual size
            width, height = viewport_scale
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
        vertex_buffer = state.device.newBufferWithBytes_length_options_(
            vertex_data.tobytes(),
            len(vertex_data) * 4,
            Metal.MTLResourceStorageModeShared
        )
        
        color_data = array.array('f', renderer.color)
        color_buffer = state.device.newBufferWithBytes_length_options_(
            color_data.tobytes(),
            len(color_data) * 4,
            Metal.MTLResourceStorageModeShared
        )
        
        state.encoder.setVertexBuffer_offset_atIndex_(vertex_buffer, 0, 0)
        state.encoder.setFragmentBuffer_offset_atIndex_(color_buffer, 0, 0)
        state.encoder.drawPrimitives_vertexStart_vertexCount_(
            Metal.MTLPrimitiveTypeTriangle,
            0,
            len(triangles) // 2
        )
    
    draw_shapes(world)
    
