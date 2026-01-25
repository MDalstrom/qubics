from q_engine.alt.metal.deps import RenderingContext
from time import time
import Metal
from q_engine.alt.ecs.components import Component, World, Archetype
from q_engine.alt.ecs.systems import SystemDesc, build_batches, query, schedule
import mlx.core as mx
import math


class SoftBodyPoint(Component):
    def __init__(self):
        self.position = mx.zeros([0, 3])  # [x, y, z]
    
    def add(self, i, size=1):
        if i + size >= self.position.shape[0]:
            self.position = mx.concat([self.position, mx.zeros([size, 3])])


class Velocity(Component):
    def __init__(self):
        self.velocity = mx.zeros([0, 3])  # [vx, vy, vz]
    
    def add(self, i, size=1):
        if i + size >= self.velocity.shape[0]:
            self.velocity = mx.concat([self.velocity, mx.zeros([size, 3])])


class CollisionContacts(Component):
    """Stores collision contact points for visualization"""
    def __init__(self):
        self.contacts = mx.zeros([0, 3])  # [x, y, z] positions of contact points
    
    def add(self, i, size=1):
        if i + size >= self.contacts.shape[0]:
            self.contacts = mx.concat([self.contacts, mx.zeros([size, 3])])


def create_circle_body(arch: Archetype, center: tuple, radius: float, num_points: int, color: tuple = (1.0, 0.0, 0.0, 1.0)):
    point_component: SoftBodyPoint = arch.components[SoftBodyPoint]
    velocity_component: Velocity = arch.components[Velocity]
    entities = []
    
    for i in range(num_points):
        e = arch.create_entity()
        angle = (2 * math.pi * i) / num_points
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        z = center[2]
        
        point_component.position[e] = mx.array([x, y, z], dtype=mx.float32)
        velocity_component.velocity[e] = mx.array([0, 0, 0])
        entities.append(e)
    
    return entities, color


def render_soft_bodies(context: RenderingContext, bodies_info: list):
    @query
    def inner(soft_body_point: SoftBodyPoint):
        if soft_body_point.position.size == 0:
            return
        
        # Get aspect ratio correction
        aspect_ratio = context.viewport_width / context.viewport_height
        
        for entity_indices, color in bodies_info:
            if len(entity_indices) < 3:
                continue
            
            # Get positions for all points in this body
            positions_list = [soft_body_point.position[e] for e in entity_indices]
            positions = mx.stack(positions_list)
            
            # Apply aspect ratio correction to X coordinate
            positions_corrected = mx.concatenate([
                positions[:, 0:1] / aspect_ratio,  # Divide X by aspect ratio
                positions[:, 1:3]  # Keep Y and Z
            ], axis=1)
            
            # Compute centroid from corrected positions
            centroid = mx.mean(positions_corrected, axis=0)
            
            # Build triangle fan from centroid
            # For N points: (centroid, p0, p1), (centroid, p1, p2), ..., (centroid, pN-1, p0)
            num_points = len(entity_indices)
            num_triangles = num_points
            
            vertices_list = []
            colors_list = []
            
            for i in range(num_triangles):
                next_i = (i + 1) % num_points
                
                # Triangle: centroid, current point, next point
                tri_vertices = mx.stack([
                    centroid,
                    positions_corrected[i],
                    positions_corrected[next_i]
                ])
                
                vertices_list.append(tri_vertices)
                
                # Same color for all vertices of this triangle
                tri_colors = mx.array([color, color, color], dtype=mx.float32)
                colors_list.append(tri_colors)
            
            # Stack all triangles
            all_vertices = mx.concatenate(vertices_list, axis=0)
            all_colors = mx.concatenate(colors_list, axis=0)
            
            # Convert to homogeneous coordinates (add w=1)
            ones = mx.ones([all_vertices.shape[0], 1], dtype=mx.float32)
            vertices_homo = mx.concatenate([all_vertices, ones], axis=1)
            
            # Flatten for Metal buffer
            vertices_flat = vertices_homo.flatten()
            colors_flat = all_colors.flatten()
            
            # Create Metal buffers
            vertex_buf = context.device.newBufferWithBytes_length_options_(
                memoryview(vertices_flat), vertices_flat.nbytes, 0
            )
            
            color_buf = context.device.newBufferWithBytes_length_options_(
                memoryview(colors_flat), colors_flat.nbytes, 0
            )
            
            # Draw
            context.encoder.setVertexBuffer_offset_atIndex_(vertex_buf, 0, 0)
            context.encoder.setVertexBuffer_offset_atIndex_(color_buf, 0, 1)
            context.encoder.drawPrimitives_vertexStart_vertexCount_(
                Metal.MTLPrimitiveTypeTriangle, 0, vertices_flat.size // 4
            )
    
    return inner


@query
def integrate_velocity(soft_body_point: SoftBodyPoint, velocity: Velocity):
    dt = 1 / 120.0
    soft_body_point.position += velocity.velocity * dt


@query
def detect_collisions(soft_body_point: SoftBodyPoint, velocity: Velocity, collision_contacts: CollisionContacts):
    collision_distance = 0.005
    num_points = soft_body_point.position.shape[0]
    
    if num_points < 2:
        return
    
    positions = soft_body_point.position
    
    # Grid-based spatial partitioning for fast collision detection
    grid_size = collision_distance * 2.0
    contacts = []
    
    # Build spatial grid
    grid = {}
    for i in range(num_points):
        pos = positions[i]
        # Quantize to grid cell
        cell = (
            int(pos[0] / grid_size),
            int(pos[1] / grid_size),
            int(pos[2] / grid_size)
        )
        if cell not in grid:
            grid[cell] = []
        grid[cell].append(i)
    
    # Check collisions only within neighboring cells
    checked_pairs = set()
    for cell, point_indices in grid.items():
        # Check points in this cell and neighboring cells
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    neighbor_cell = (cell[0] + dx, cell[1] + dy, cell[2] + dz)
                    if neighbor_cell not in grid:
                        continue
                    
                    neighbor_indices = grid[neighbor_cell]
                    
                    for i in point_indices:
                        for j in neighbor_indices:
                            if i >= j:  # Skip self and duplicates
                                continue
                            
                            pair = (min(i, j), max(i, j))
                            if pair in checked_pairs:
                                continue
                            checked_pairs.add(pair)
                            
                            # Check distance
                            diff = positions[i] - positions[j]
                            dist_sq = mx.sum(diff * diff)
                            if dist_sq < collision_distance * collision_distance and dist_sq > 1e-12:
                                contact = (positions[i] + positions[j]) * 0.5
                                contacts.append(contact)
    
    # Store contacts in component
    if contacts:
        collision_contacts.contacts = mx.stack(contacts)
    else:
        collision_contacts.contacts = mx.zeros([0, 3])
    
    mx.eval(collision_contacts.contacts)
    


def render_gizmo_contacts(context: RenderingContext):
    """Render collision contact points as small magenta dots"""
    @query
    def inner(collision_contacts: CollisionContacts):
        if collision_contacts.contacts.size == 0:
            return
        
        # Get aspect ratio correction
        aspect_ratio = context.viewport_width / context.viewport_height
        contacts = collision_contacts.contacts
        
        # Create small points around each contact (tiny spheres made from triangles)
        gizmo_radius = 0.02
        num_subdivisions = 4  # Low poly for speed
        
        vertices_list = []
        colors_list = []
        
        for contact in contacts:
            # Create a small icosphere at contact point
            for i in range(num_subdivisions):
                angle = (2 * math.pi * i) / num_subdivisions
                for k in range(2):
                    z_offset = -gizmo_radius + k * (2 * gizmo_radius)
                    x = contact[0] + gizmo_radius * math.cos(angle)
                    y = contact[1] + gizmo_radius * math.sin(angle)
                    z = contact[2] + z_offset
                    
                    next_angle = (2 * math.pi * (i + 1)) / num_subdivisions
                    x_next = contact[0] + gizmo_radius * math.cos(next_angle)
                    y_next = contact[1] + gizmo_radius * math.sin(next_angle)
                    
                    # Triangle
                    tri_vertices = mx.array([
                        [x / aspect_ratio, y, z, 1.0],
                        [x_next / aspect_ratio, y_next, z, 1.0],
                        [contact[0] / aspect_ratio, contact[1], contact[2], 1.0]
                    ], dtype=mx.float32)
                    vertices_list.append(tri_vertices)
                    
                    # Magenta color for all vertices
                    tri_colors = mx.array([
                        [1.0, 0.0, 1.0, 1.0],
                        [1.0, 0.0, 1.0, 1.0],
                        [1.0, 0.0, 1.0, 1.0]
                    ], dtype=mx.float32)
                    colors_list.append(tri_colors)
        
        if not vertices_list:
            return
        
        all_vertices = mx.concatenate(vertices_list, axis=0)
        all_colors = mx.concatenate(colors_list, axis=0)
        
        vertices_flat = all_vertices.flatten()
        colors_flat = all_colors.flatten()
        
        vertex_buf = context.device.newBufferWithBytes_length_options_(
            memoryview(vertices_flat), vertices_flat.nbytes, 0
        )
        
        color_buf = context.device.newBufferWithBytes_length_options_(
            memoryview(colors_flat), colors_flat.nbytes, 0
        )
        
        context.encoder.setVertexBuffer_offset_atIndex_(vertex_buf, 0, 0)
        context.encoder.setVertexBuffer_offset_atIndex_(color_buf, 0, 1)
        context.encoder.drawPrimitives_vertexStart_vertexCount_(
            Metal.MTLPrimitiveTypeTriangle, 0, vertices_flat.size // 4
        )
    
    return inner

# create_sim_fn(handle: Deps):
#   handle.add()
#   def inner(): ...
#   return inner

# create_render_fn(device: MetalDevice):
#   device.create_encoder()
#   def inner(): ...
#   return inner

# def loop(fn) <> def run(fn)

# def tick_fc():
#   world = World()
#   


def get_tick():
    arch = Archetype([SoftBodyPoint, Velocity, CollisionContacts])
    world = World([arch])
    
    # Create a circular soft body
    bodies_info = []
    body1_entities, body1_color = create_circle_body(
        arch, 
        center=(0.0, 0.0, 0.0),
        radius=0.1,
        num_points=16,
        color=(1.0, 0.5, 0.2, 1.0)
    )
    bodies_info.append((body1_entities, body1_color))
    
    # Create another smaller circle
    body2_entities, body2_color = create_circle_body(
        arch,
        center=(0.2, 0.2, 0.0),
        radius=0.2,
        num_points=32,
        color=(0.2, 0.7, 1.0, 1.0)
    )
    bodies_info.append((body2_entities, body2_color))
    
    # Build simulation systems with velocity integration and collision detection
    batches = build_batches([
        SystemDesc.from_fn(integrate_velocity),
        SystemDesc.from_fn(detect_collisions)
    ], SystemDesc.resolve)
    sim_tick = schedule(batches)
    
    last_time = None
    accumulator = 0.0
    fixed_dt = 1 / 120
    
    def call(context: RenderingContext):
        nonlocal last_time
        nonlocal accumulator
        
        current = time()
        if last_time:
            accumulator += current - last_time
        last_time = current
        
        limit = 5
        while accumulator > fixed_dt and limit > 0:
            sim_tick(world)
            accumulator -= fixed_dt
            limit -= 1
        
        # Render soft bodies
        render_soft_bodies(context, bodies_info)(world)
        # # Render collision contact gizmos
        render_gizmo_contacts(context)(world)
    
    return call


get_tick()
