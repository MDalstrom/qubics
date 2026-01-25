from functools import wraps
from time import time
import Metal
from q_engine.alt.ecs import Component, World, Archetype, SystemDesc, build_batches, query, schedule, RenderingContext
import mlx.core as mx

class Transform(Component):
    def __init__(self):
        self.world = mx.zeros([0, 4, 4])
        self.local = mx.zeros([0, 4, 4])

    def add(self, i, size=1):
        if i + size >= self.world.shape[0]:
            self.world = mx.concat([self.world, mx.zeros([size, 4, 4])])
            self.local = mx.concat([self.local, mx.zeros([size, 4, 4])])

class Shape(Component):
    def __init__(self) -> None:
        self.vertices = mx.zeros([0, 4])
        self.colors = mx.zeros([0, 4])

    def add(self, i, size=1):
        if i + size >= self.vertices.shape[0]:
            self.vertices = mx.concat([self.vertices, mx.zeros([size, 4])])
            self.colors = mx.concat([self.colors, mx.zeros([size, 4])])

class AngularVelocity(Component):
    def __init__(self) -> None:
        self.velocity = mx.zeros([0, 4])

    def add(self, i, size=1):
        if i + size >= self.velocity.shape[0]:
            self.velocity = mx.concat([self.velocity, mx.zeros([size, 4])])

@query
def rotate(transform: Transform, angular_velocity: AngularVelocity):
    dt = 1 / 120.0
    num_entities = transform.world.shape[0]
    
    # Process all entities
    new_locals = []
    for e in range(num_entities):
        # Get angular velocity (rotation axis and magnitude)
        av = angular_velocity.velocity[e]  # [x, y, z]
        angle_mag = mx.linalg.norm(av)
        
        if angle_mag < 1e-6:
            new_locals.append(transform.local[e])
            continue
        
        # Scale by delta time
        angle = angle_mag * dt
        
        # Normalize to get rotation axis
        axis = av / angle_mag
        
        # Create rotation matrix using Rodrigues' formula
        K = mx.array([
            [0, -axis[2], axis[1]],
            [axis[2], 0, -axis[0]],
            [-axis[1], axis[0], 0]
        ], dtype=mx.float32)
        
        R = mx.eye(3) + mx.sin(angle) * K + (1 - mx.cos(angle)) * (K @ K)
        
        # Convert to 4x4 rotation matrix
        rot_mat = mx.eye(4, dtype=mx.float32)
        rot_mat[:3, :3] = R
        
        # Apply rotation to local matrix
        new_local = rot_mat @ transform.local[e]
        new_locals.append(new_local)
    
    if new_locals:
        transform.local = mx.stack(new_locals)
        transform.world = transform.local


def render(context: RenderingContext):
    @query
    def inner(transform: Transform, shape: Shape):
        l_vertices = shape.vertices
        if l_vertices.size == 0:
            return

        num_entities = transform.world.shape[0]
        for e in range(num_entities):
            world_pos = l_vertices @ transform.world[e].T
            
            vertices = world_pos.flatten()
            rgba = shape.colors.flatten()

            if vertices.size == 0:
                return
            
            
            vertex_buf = context.device.newBufferWithBytes_length_options_(
                memoryview(vertices), vertices.nbytes, 0
            )

            color_buf = context.device.newBufferWithBytes_length_options_(
                memoryview(rgba), rgba.nbytes, 0
            )

            context.encoder.setVertexBuffer_offset_atIndex_(vertex_buf, 0, 0)
            context.encoder.setVertexBuffer_offset_atIndex_(color_buf, 0, 1)
            context.encoder.drawPrimitives_vertexStart_vertexCount_(
                Metal.MTLPrimitiveTypeTriangle, 0, vertices.size // 4
            )
    
    return inner

def get_tick():
    arch = Archetype([Transform, Shape, AngularVelocity])
    world = World([arch])

    e = arch.create_entity()
    transform: Transform = arch.chunks[Transform]
    # Initialize local transform with translation
    identity = mx.eye(4)
    identity[2, 3] = 0.5
    transform.local[e, :, :] = identity
    transform.world[e, :, :] = identity
    
    angular_vel: AngularVelocity = arch.chunks[AngularVelocity]
    angular_vel.velocity[e] = mx.array([0.0, 1.0, 0.0, 0.0], dtype=mx.float32)

    shape: Shape = arch.chunks[Shape]
    shape.vertices = mx.array([
        [ 0.0,  0.5,  0.0, 1.0],
        [-0.5, -0.5,  0.0, 1.0],
        [ 0.5, -0.5,  0.0, 1.0],
    ], dtype=mx.float32)
    shape.colors = mx.array([
        [ 1.0,  0.0,  0.0, 1.0],
        [ 0.0,  1.0,  0.0, 1.0],
        [ 0.0,  0.0,  1.0, 1.0],
    ])

    batches = build_batches([
        SystemDesc.from_fn(rotate)
    ], SystemDesc.resolve)
    sim_tick = schedule(batches)

    render_tick_fc = [render]

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

        while accumulator > fixed_dt:
            sim_tick(world)
            accumulator -= fixed_dt

        for render_fc in render_tick_fc:
            render_fc(context)(world)

    return call


def wrap_python_errors(fn):
    @wraps(fn)
    def _(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            import traceback
            traceback.print_exception(e)
            raise
    return _

tick = get_tick()
tick = wrap_python_errors(tick)
