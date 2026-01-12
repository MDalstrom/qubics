from dataclasses import dataclass
from pygame import Surface


@dataclass
class Viewport:
    surface: Surface
    resolution: tuple[int, int]
