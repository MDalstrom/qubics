import math
import numpy as np
from q_engine.application.render.mesh import Mesh, Transform, create
from q_engine.ecs.components import CommandBuffer, World, Component
from q_engine.application.render.camera import Camera
from q_engine.application.kinetic.velocity import AngularVelocity, rotation_system
from q_engine.application.kinetic.mover import CameraState, Mover, create_mover
from q_engine.metal import mk_library
from q_engine.persistent.metal import state as metal_state


def generate_uv_sphere_triangle_list_vertices(radius=1.0, segments=32, stacks=16):
    vertices = []

    for i in range(stacks):
        phi1 = np.pi / 2 - i * np.pi / stacks
        phi2 = np.pi / 2 - (i + 1) * np.pi / stacks

        for j in range(segments):
            theta1 = j * 2 * np.pi / segments
            theta2 = (j + 1) * 2 * np.pi / segments

            def to_cartesian(phi, theta):
                x = radius * np.cos(phi) * np.cos(theta)
                y = radius * np.sin(phi)
                z = radius * np.cos(phi) * np.sin(theta)
                return [x, y, z, 1.0]

            v1 = to_cartesian(phi1, theta1)
            v2 = to_cartesian(phi2, theta1)
            v3 = to_cartesian(phi2, theta2)
            v4 = to_cartesian(phi1, theta2)

            vertices.append(v1)
            vertices.append(v2)
            vertices.append(v4)

            vertices.append(v2)
            vertices.append(v3)
            vertices.append(v4)

    return np.array(vertices, dtype=np.float32)


def _configure_spinning_sphere_archetype(
    cb: CommandBuffer, sphere_vertices: np.ndarray
):
    archetype_handle = cb.create_entity()
    cb.add_component(archetype_handle, Mesh)
    cb.add_component(archetype_handle, Transform)
    cb.add_component(archetype_handle, AngularVelocity)

    @CommandBuffer.set_deferred(cb, archetype_handle, Mesh)
    def set_shared_sphere_mesh(e, mesh: Mesh):
        mesh.vertices = sphere_vertices


def _create_spinning_sphere_instance(cb: CommandBuffer, i: float):
    entity = cb.create_entity()
    cb.add_component(entity, Mesh)
    cb.add_component(entity, Transform)
    cb.add_component(entity, AngularVelocity)
    
    @CommandBuffer.set_deferred(cb, entity, Transform)
    def set_transform(e, transform: Transform):
        transform.matrices[e.index] = np.eye(4, dtype=np.float32, order="F")
        rads = i * 2 * math.pi
        transform.matrices[e.index, 3, 0] = math.sin(rads) * 10
        transform.matrices[e.index, 3, 2] = math.cos(rads) * 10

    @CommandBuffer.set_deferred(cb, entity, AngularVelocity)
    def set_angular_velocity(e, ang_vel: AngularVelocity):
        ang_vel.axes[e.index] = np.array([0, 1, 0, 0], dtype=np.float32)
        ang_vel.speeds[e.index] = np.pi / 2


def _create_camera(cb: CommandBuffer):
    camera_entity = cb.create_entity()
    cb.add_component(camera_entity, Transform)
    cb.add_component(camera_entity, Camera)
    cb.add_component(camera_entity, Mover)
    cb.add_component(camera_entity, CameraState)

    @CommandBuffer.set_deferred(cb, camera_entity, Transform)
    def set_camera_transform(e, transform: Transform):
        transform.matrices[e.index] = np.eye(4, dtype=np.float32, order="F")
        transform.matrices[e.index, 3, 2] = 0.0

    @CommandBuffer.set_deferred(cb, camera_entity, Camera)
    def set_camera_props(e, camera: Camera):
        camera.fov = np.pi / 180 * 80
        camera.near = 0.01
        camera.far = 1000.0

    @CommandBuffer.set_deferred(cb, camera_entity, CameraState)
    def set_camera_state(e, camera_state: CameraState):
        camera_state.yaw_angle = 0.0
        camera_state.pitch_angle = 0.0


def bake(world: World):
    cb = CommandBuffer()

    sphere_vertices = generate_uv_sphere_triangle_list_vertices(radius=1.0)

    _configure_spinning_sphere_archetype(cb, sphere_vertices)

    for _ in range(10):
        _create_spinning_sphere_instance(cb, _ / 10)

    _create_camera(cb)

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

