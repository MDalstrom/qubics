from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING
import math
import numpy as np

if TYPE_CHECKING:
    from pygame import Rect


@dataclass
class Velocity:
    vx: float
    vy: float
    angular_velocity: float = 0.0


@dataclass
class Acceleration:
    ax: float = 0.0
    ay: float = 0.0


@dataclass
class Health:
    hp: float


@dataclass
class Damage:
    value: Callable[[], float]


@dataclass
class CircleCollider:
    radius: float
    kind: str
    collisions: list[int] = None
    
    def __postinit__(self):
        self.collisions = []

@dataclass
class Renderable:
    shape: str
    color: tuple[int, int, int]
    radius: float = 0.0


@dataclass
class Parent:
    owner: 'EntityRef'
    offset_distance: float = 0.0
    offset_angle: float = 0.0


@dataclass
class Destroyed:
    """Marker component for destroyed entities"""
    value: bool = True


@dataclass
class Bounds:
    """Boundary component"""
    rect: 'Rect'
    color: tuple[int, int, int]


class Transform:
    """Transform component with hierarchical world/local coordinate support"""
    
    def __init__(self, x: float = 0.0, y: float = 0.0, angle: float = 0.0, parent: 'Transform | None' = None):
        self.local_x = x
        self.local_y = y
        self.local_angle = angle
        self.parent = parent
    
    def get_world_position(self) -> tuple[float, float]:
        if self.parent is None:
            return self.local_x, self.local_y
        
        parent_x, parent_y = self.parent.get_world_position()
        parent_angle = self.parent.get_world_angle()
        
        cos_a = math.cos(parent_angle)
        sin_a = math.sin(parent_angle)
        
        world_x = parent_x + self.local_x * cos_a - self.local_y * sin_a
        world_y = parent_y + self.local_x * sin_a + self.local_y * cos_a
        
        return world_x, world_y
    
    def get_world_angle(self) -> float:
        if self.parent is None:
            return self.local_angle
        return self.parent.get_world_angle() + self.local_angle
    
    def set_world_position(self, x: float, y: float) -> None:
        if self.parent is None:
            self.local_x = x
            self.local_y = y
            return
        
        parent_x, parent_y = self.parent.get_world_position()
        parent_angle = self.parent.get_world_angle()
        
        dx = x - parent_x
        dy = y - parent_y
        cos_a = math.cos(-parent_angle)
        sin_a = math.sin(-parent_angle)
        
        self.local_x = dx * cos_a - dy * sin_a
        self.local_y = dx * sin_a + dy * cos_a
    
    def set_world_angle(self, angle: float) -> None:
        if self.parent is None:
            self.local_angle = angle
            return
        self.local_angle = angle - self.parent.get_world_angle()
    
    def get_matrix(self) -> np.ndarray:
        """Get transformation matrix (3x3 homogeneous)"""
        cos_a = math.cos(self.local_angle)
        sin_a = math.sin(self.local_angle)
        
        matrix = np.array([
            [cos_a, -sin_a, self.local_x],
            [sin_a, cos_a, self.local_y],
            [0, 0, 1]
        ])
        
        if self.parent is not None:
            parent_matrix = self.parent.get_matrix()
            matrix = parent_matrix @ matrix
        
        return matrix


from infrastructure.world import EntityRef
