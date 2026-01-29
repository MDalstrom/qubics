from functools import wraps
import numpy as np
from q_engine.application.render.mesh import Mesh, Transform, create
from q_engine.ecs.components import CommandBuffer, World
from q_engine.application.render.camera import Camera
from q_engine.application.kinetic.velocity import AngularVelocity, rotation_system
from q_engine.application.kinetic.mover import CameraState, Mover, create_mover
import q_engine.keys as keys
from q_engine.metal import mk_library
from q_engine.persistent.metal import state as metal_state


def bake(world: World):
    cb = CommandBuffer()

    rng = np.random.default_rng()
    for _ in range(10):
        entity = cb.create_entity()
        cb.add_component(entity, Mesh)
        cb.add_component(entity, Transform)
        cb.add_component(entity, AngularVelocity)

        @CommandBuffer.set_deferred(cb, entity, Mesh)
        def set_mesh(e, mesh: Mesh):
            mesh.vertices = np.array([
                    [-1, -1, 0, 1],
                    [1,  -1, 0, 1],
                    [0,   1, 0, 1],
                ],
                dtype=np.float32,
            )

        @CommandBuffer.set_deferred(cb, entity, Transform)
        def set_transform(e, transform: Transform):
            i = rng.random() * 10
            transform.matrices[e.index] = np.eye(4, dtype=np.float32, order="F")
            transform.matrices[e.index, 3, 0] = ((i % 4) / 4) * 10
            transform.matrices[e.index, 3, 1] = ((i // 4) / 5) * 10
            transform.matrices[e.index, 3, 2] = 10.0

        @CommandBuffer.set_deferred(cb, entity, AngularVelocity)
        def set_angular_velocity(e, ang_vel: AngularVelocity):
            ang_vel.axes[e.index] = [0, 1, 0]
            ang_vel.speeds[e.index] = np.pi / 2

    camera_entity = cb.create_entity()
    cb.add_component(camera_entity, Transform)
    cb.add_component(camera_entity, Camera)
    cb.add_component(camera_entity, Mover)
    cb.add_component(camera_entity, CameraState)

    @CommandBuffer.set_deferred(cb, camera_entity, Transform)
    def set_camera_transform(e, transform: Transform):
        transform.matrices[e.index] = np.eye(4, dtype=np.float32, order="F")
        transform.matrices[e.index, 3, 2] = 0.0

    cb.playback(world)


def get_tick(state=metal_state):
    world = World()
    bake(world)

    render_system = create(state.device, state.view, mk_library(state.device))

    def game_tick(command_buffer):
        dt = 1.0 / 60.0
        create_mover()(world)
        rotation_system(world, dt)
        render_system(world=world, command_buffer=command_buffer)

    return game_tick

