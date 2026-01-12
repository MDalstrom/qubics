from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World
import math
from application.math import Matrix, Vector


class Transform:
    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        angle: float = 0.0,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        parent: "Transform | None" = None,
    ):
        self._local_matrix = Matrix.identity(3)
        self._prev_local_matrix = Matrix.identity(3)
        self.parent = parent
        self.set_local_transform(x, y, angle, scale_x, scale_y)
        self.save_previous()

    @staticmethod
    def get_position(matrix: Matrix) -> Vector:
        return Vector(matrix[0, 2], matrix[1, 2])

    @staticmethod
    def get_scale(matrix: Matrix) -> Vector:
        sx = math.sqrt(matrix[0, 0] ** 2 + matrix[1, 0] ** 2)
        sy = math.sqrt(matrix[0, 1] ** 2 + matrix[1, 1] ** 2)
        return Vector(sx, sy)
    
    def transpose(self, point: Vector) -> Vector:
        return self.world_matrix @ point

    def save_previous(self):
        self._prev_local_matrix = self._local_matrix.copy()

    def set_local_transform(
        self,
        x: float,
        y: float,
        angle: float,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
    ):
        self._local_matrix = Matrix.transform(x, y, angle, scale_x, scale_y)

    @property
    def local_matrix(self) -> Matrix:
        return self._local_matrix

    @property
    def world_matrix(self) -> Matrix:
        if self.parent is None:
            return self._local_matrix
        return self.parent.world_matrix @ self._local_matrix

    @property
    def local_x(self) -> float:
        return self._local_matrix[0, 2]

    @local_x.setter
    def local_x(self, value: float):
        self._local_matrix[0, 2] = value

    @property
    def local_y(self) -> float:
        return self._local_matrix[1, 2]

    @local_y.setter
    def local_y(self, value: float):
        self._local_matrix[1, 2] = value

    @property
    def local_angle(self) -> float:
        return math.atan2(self._local_matrix[1, 0], self._local_matrix[0, 0])

    @local_angle.setter
    def local_angle(self, value: float):
        x = self._local_matrix[0, 2]
        y = self._local_matrix[1, 2]
        scale = self.get_local_scale()
        self.set_local_transform(x, y, value, scale.x, scale.y)

    def get_local_scale(self) -> Vector:
        matrix = self._local_matrix
        sx = math.sqrt(matrix[0, 0] ** 2 + matrix[1, 0] ** 2)
        sy = math.sqrt(matrix[0, 1] ** 2 + matrix[1, 1] ** 2)
        return Vector(sx, sy)

    def get_world_scale(self) -> Vector:
        matrix = self.world_matrix
        sx = math.sqrt(matrix[0, 0] ** 2 + matrix[1, 0] ** 2)
        sy = math.sqrt(matrix[0, 1] ** 2 + matrix[1, 1] ** 2)
        return Vector(sx, sy)

    def get_world_matrix(self) -> Matrix:
        return self.world_matrix

    def get_interpolated_world_position(self, alpha: float) -> tuple[float, float]:
        interp_local = (
            self._prev_local_matrix * (1.0 - alpha) + self._local_matrix * alpha
        )

        if self.parent is None:
            world_matrix = interp_local
        else:
            parent_matrix = self.parent.get_interpolated_world_matrix(alpha)
            world_matrix = parent_matrix @ interp_local

        return world_matrix[0, 2], world_matrix[1, 2]

    def get_interpolated_world_matrix(self, alpha: float) -> Matrix:
        interp_local = (
            self._prev_local_matrix * (1.0 - alpha) + self._local_matrix * alpha
        )

        if self.parent is None:
            return interp_local

        parent_matrix = self.parent.get_interpolated_world_matrix(alpha)
        return parent_matrix @ interp_local

    def get_world_position(self) -> tuple[float, float]:
        wm = self.world_matrix
        return wm[0, 2], wm[1, 2]

    def get_world_angle(self) -> float:
        wm = self.world_matrix
        return math.atan2(wm[1, 0], wm[0, 0])

    def set_world_position(self, x: float, y: float) -> None:
        if self.parent is None:
            self._local_matrix[0, 2] = x
            self._local_matrix[1, 2] = y
            return

        parent_inv = self.parent.world_matrix.inverse()
        local_pos = parent_inv @ Vector(x, y)

        self._local_matrix[0, 2] = local_pos.x
        self._local_matrix[1, 2] = local_pos.y

    def set_world_angle(self, angle: float) -> None:
        current_x = self._local_matrix[0, 2]
        current_y = self._local_matrix[1, 2]
        scale = self.get_local_scale()

        if self.parent is None:
            self.set_local_transform(current_x, current_y, angle, scale.x, scale.y)
            return

        parent_angle = self.parent.get_world_angle()
        local_angle = angle - parent_angle
        self.set_local_transform(current_x, current_y, local_angle, scale.x, scale.y)

    def get_matrix(self) -> Matrix:
        return self.world_matrix

@for_each
def save_transform_state(_: World, __: Entity, transform: Transform) -> None:
    transform.save_previous()
