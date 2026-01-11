import math
import numpy as np


class Transform:
    def __init__(self, x: float = 0.0, y: float = 0.0, angle: float = 0.0, parent: 'Transform | None' = None):
        self.matrix = np.identity(3)
        self.prev_matrix = np.identity(3)
        self.parent = parent
        self.set_local_transform(x, y, angle)
        self.save_previous()
    
    def save_previous(self):
        self.prev_matrix = self.matrix.copy()

    def set_local_transform(self, x: float, y: float, angle: float):
        c = math.cos(angle)
        s = math.sin(angle)
        self.matrix = np.array([
            [c, -s, x],
            [s, c, y],
            [0, 0, 1]
        ])

    @property
    def local_x(self) -> float:
        return self.matrix[0, 2]
    
    @local_x.setter
    def local_x(self, value: float):
        self.matrix[0, 2] = value
        
    @property
    def local_y(self) -> float:
        return self.matrix[1, 2]

    @local_y.setter
    def local_y(self, value: float):
        self.matrix[1, 2] = value
        
    @property
    def local_angle(self) -> float:
        return math.atan2(self.matrix[1, 0], self.matrix[0, 0])
        
    @local_angle.setter
    def local_angle(self, value: float):
        x = self.matrix[0, 2]
        y = self.matrix[1, 2]
        self.set_local_transform(x, y, value)

    def get_world_matrix(self) -> np.ndarray:
        if self.parent is None:
            return self.matrix
        return self.parent.get_world_matrix() @ self.matrix

    def get_interpolated_world_position(self, alpha: float) -> tuple[float, float]:
        current_local = self.matrix
        prev_local = self.prev_matrix
        interp_local = prev_local * (1.0 - alpha) + current_local * alpha
        
        if self.parent is None:
            world_matrix = interp_local
        else:
            parent_matrix = self.parent.get_interpolated_world_matrix(alpha)
            world_matrix = parent_matrix @ interp_local
            
        return world_matrix[0, 2], world_matrix[1, 2]

    def get_interpolated_world_matrix(self, alpha: float) -> np.ndarray:
        current_local = self.matrix
        prev_local = self.prev_matrix
        interp_local = prev_local * (1.0 - alpha) + current_local * alpha
        
        if self.parent is None:
            return interp_local
        
        parent_matrix = self.parent.get_interpolated_world_matrix(alpha)
        return parent_matrix @ interp_local

    def get_world_position(self) -> tuple[float, float]:
        world_matrix = self.get_world_matrix()
        return world_matrix[0, 2], world_matrix[1, 2]
    
    def get_world_angle(self) -> float:
        world_matrix = self.get_world_matrix()
        return math.atan2(world_matrix[1, 0], world_matrix[0, 0])
    
    def set_world_position(self, x: float, y: float) -> None:
        if self.parent is None:
            self.matrix[0, 2] = x
            self.matrix[1, 2] = y
            return
        
        parent_matrix = self.parent.get_world_matrix()
        parent_inv = np.linalg.inv(parent_matrix)
        
        target_world_pos = np.array([x, y, 1.0])
        local_pos_homogeneous = parent_inv @ target_world_pos
        
        self.matrix[0, 2] = local_pos_homogeneous[0]
        self.matrix[1, 2] = local_pos_homogeneous[1]
    
    def set_world_angle(self, angle: float) -> None:
        current_x = self.matrix[0, 2]
        current_y = self.matrix[1, 2]
        
        if self.parent is None:
            self.set_local_transform(current_x, current_y, angle)
            return
            
        parent_angle = self.parent.get_world_angle()
        local_angle = angle - parent_angle
        self.set_local_transform(current_x, current_y, local_angle)
    
    def get_matrix(self) -> np.ndarray:
        return self.get_world_matrix()
