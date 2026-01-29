import numpy as np
from q_engine.ecs.components import Component, World
from q_engine.ecs.systems import query
from q_engine.application.render.mesh import Transform


def q_from_axis_angle(axis, angle):
    half_angle = angle * 0.5
    sin_half = np.sin(half_angle)
    cos_half = np.cos(half_angle)
    return np.array([axis[0] * sin_half, axis[1] * sin_half, axis[2] * sin_half, cos_half], dtype=np.float32)

def q_normalize(q):
    norm = np.linalg.norm(q)
    if norm == 0:
        return q
    return q / norm

def q_mult(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
    z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
    return np.array([x, y, z, w], dtype=np.float32)

def q_to_mat4(q):
    x, y, z, w = q
    xx, yy, zz = x*x, y*y, z*z
    xy, xz, yz = x*y, x*z, y*z
    wx, wy, wz = w*x, w*y, w*z
    
    return np.array([
        [1-2*(yy+zz),   2*(xy-wz),   2*(xz+wy), 0],
        [  2*(xy+wz), 1-2*(xx+zz),   2*(yz-wx), 0],
        [  2*(xz-wy),   2*(yz+wx), 1-2*(xx+yy), 0],
        [          0,           0,           0, 1]
    ], dtype=np.float32)


class AngularVelocity(Component):
    def __init__(self):
        self.axes = np.zeros([0, 3], dtype=np.float32)
        self.speeds = np.zeros([0], dtype=np.float32)
        self.orientations = np.zeros([0, 4], dtype=np.float32)

    def add(self, i: int, size: int = 1):
        current_size = self.axes.shape[0]
        required_size = i + size
        if required_size > current_size:
            to_add = required_size - current_size
            
            self.axes = np.concatenate([self.axes, np.zeros((to_add, 3), dtype=np.float32)])
            self.speeds = np.concatenate([self.speeds, np.zeros(to_add, dtype=np.float32)])

            new_orientations = np.zeros((to_add, 4), dtype=np.float32)
            new_orientations[:, 3] = 1.0 # Identity quaternion (0,0,0,1)
            self.orientations = np.concatenate([self.orientations, new_orientations])


def rotation_system(world: World, dt: float):
    
    @query
    def _rotation_system(ang_vel: AngularVelocity, transform: Transform):
        num_entities = ang_vel.speeds.shape[0]
        
        for i in range(num_entities):
            delta_q = q_from_axis_angle(ang_vel.axes[i], ang_vel.speeds[i] * dt)
            
            new_orientation = q_mult(delta_q, ang_vel.orientations[i])
            ang_vel.orientations[i] = q_normalize(new_orientation)
            
            rotation_matrix = q_to_mat4(ang_vel.orientations[i])
            
            original_matrix_row_major = transform.matrices[i]
            position = original_matrix_row_major[3, 0:3]
            
            final_matrix_row_major = rotation_matrix
            final_matrix_row_major[3, 0:3] = position
            transform.matrices[i] = final_matrix_row_major
            
    _rotation_system(world)
