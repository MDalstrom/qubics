import numpy as np
from q_engine.application.kinetic.velocity import q_from_axis_angle, q_mult, q_to_mat4
from q_engine.application.render.mesh import Transform
from q_engine.ecs.components import World, component, Component
from q_engine.ecs.systems import query
from q_engine.keys import get_mouse_delta, is_key_down
from q_engine.application.render.camera import Camera


@component
class Mover():
    pass

@component
class CameraState(Component):
    yaw_angle: float
    pitch_angle: float


dt = 1 / 120

def create_mover(speed: float = 100.0):
    def outer(world: World):
        raw_direction = np.zeros(3, dtype=np.float32)

        KEY_W = 13
        KEY_S = 1
        KEY_A = 0
        KEY_D = 2
        KEY_SPACE = 49
        KEY_SHIFT = 56

        if is_key_down(KEY_W):
            raw_direction[2] += 1
        if is_key_down(KEY_S):
            raw_direction[2] -= 1
        if is_key_down(KEY_A):
            raw_direction[0] -= 1
        if is_key_down(KEY_D):
            raw_direction[0] += 1
        
        if is_key_down(KEY_SPACE):
            raw_direction[1] += 1
        if is_key_down(KEY_SHIFT):
            raw_direction[1] -= 1

        if np.linalg.norm(raw_direction) > 0:
            raw_direction = raw_direction / np.linalg.norm(raw_direction)

        movement_amount = speed * dt

        def camera_controller_system(camera: Camera, transform: Transform, camera_state: CameraState):
            camera_world_matrix = transform.matrices[0]
            
            dx, dy = get_mouse_delta()
            sensitivity = 0.005

            camera_state.yaw_angle += -dx * sensitivity
            camera_state.pitch_angle += -dy * sensitivity

            max_pitch_rad = np.deg2rad(89.0)
            camera_state.pitch_angle = np.clip(camera_state.pitch_angle, -max_pitch_rad, max_pitch_rad)

            q_yaw = q_from_axis_angle([0, 1, 0], camera_state.yaw_angle)
            q_pitch = q_from_axis_angle([1, 0, 0], camera_state.pitch_angle)
            final_rotation_quat = q_mult(q_pitch, q_yaw)

            new_rotation_matrix = q_to_mat4(final_rotation_quat)[0:3, 0:3]

            camera_world_matrix[0:3, 0:3] = new_rotation_matrix

            yaw = camera_state.yaw_angle
            
            horizontal_right_vec = np.array([np.cos(yaw), 0, np.sin(yaw)], dtype=np.float32)
            horizontal_forward_vec = np.array([-np.sin(yaw), 0, np.cos(yaw)], dtype=np.float32)

            translation_vector = (
                horizontal_right_vec * raw_direction[0] +
                np.array([0, 1, 0], dtype=np.float32) * raw_direction[1] +
                horizontal_forward_vec * raw_direction[2]
            ) * movement_amount

            camera_world_matrix[3, 0:3] += translation_vector
            
            transform.matrices[0] = camera_world_matrix

        query(camera_controller_system)(world)

    return outer
