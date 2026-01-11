from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pygame import Rect


@dataclass
class CircleCollider:
    radius: float
    kind: str
    collisions: list[int] = None
    
    def __post_init__(self):
        if self.collisions is None:
            self.collisions = []


@dataclass
class Bounds:
    rect: 'Rect'
    color: tuple[int, int, int]
