from dataclasses import dataclass
from typing import Protocol
from domain import System, World


class Baker(Protocol):
    def __call__(self, world: World) -> None:
        ...

@dataclass
class Scenario:
    bake: Baker
    simulation_systems: list[System]
    rendering_systems: list[System]
