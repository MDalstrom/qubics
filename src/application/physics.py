from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ecs.entity import EntityRef


@dataclass
class Rigidbody:
    vx: float
    vy: float
    angular_velocity: float = 0.0
    angular_damping: float = 0.0
    friction: float = 0.0
    restitution: float = 1.0


@dataclass
class Acceleration:
    ax: float = 0.0
    ay: float = 0.0


@dataclass
class Parent:
    owner: 'EntityRef'
    offset_distance: float = 0.0
    offset_angle: float = 0.0
