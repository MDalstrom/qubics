from dataclasses import dataclass, field
from application.math import Vector


class CollisionMatrix:
    def __init__(self, values: list[tuple[str, str]]):
        self._matrix: dict[tuple[str, str], bool] = { key: True for key in values }

    def __getitem__(self, key: tuple[str, str]) -> bool:
        layer_a, layer_b = key
        if (layer_a, layer_b) in self._matrix:
            return self._matrix[(layer_a, layer_b)]
        if (layer_b, layer_a) in self._matrix:
            return self._matrix[(layer_b, layer_a)]
        return True
    
    def __setitem__(self, key: tuple[str, str], value: bool):
        layer_a, layer_b = key
        self._matrix[(layer_a, layer_b)] = value


@dataclass
class EdgeCollider:
    length: float


@dataclass
class BoxCollider:
    width: float
    height: float


@dataclass
class CircleCollider:
    radius: float


@dataclass
class CollisionInfo:
    normal: Vector
    penetration: float


@dataclass
class Collider:
    layer: str = "default"
    collisions: list[CollisionInfo] = field(default_factory=list)

