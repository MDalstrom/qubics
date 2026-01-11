from dataclasses import dataclass

from pygame import Rect


@dataclass
class CircleCollider:
    radius: float
    collisions: list[int] = None
    
    def __post_init__(self):
        if self.collisions is None:
            self.collisions = []


@dataclass
class BoundsCollider:
    rect: Rect 

