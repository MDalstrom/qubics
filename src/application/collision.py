from dataclasses import dataclass, field

from pygame import Rect


@dataclass
class CircleCollider:
    radius: float
    collisions: list[int] = field(default_factory=list)


@dataclass
class BoundsCollider:
    rect: Rect
