from dataclasses import dataclass


@dataclass
class Renderable:
    shape: str
    color: tuple[int, int, int]
    radius: float = 0.0
