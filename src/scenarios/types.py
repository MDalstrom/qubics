from dataclasses import dataclass
from typing import Protocol
from ecs.system import SystemsGroup
from ecs.world import World


class Baker(Protocol):
    def __call__(self, world: World) -> None:
        ...

@dataclass
class Scenario:
    bake: Baker
    simulation_group: SystemsGroup
    rendering_group: SystemsGroup

    def merge(self, other: 'Scenario'):
        def bake(*args, **kwargs):
            self.bake(*args, **kwargs)
            other.bake(*args, **kwargs)
        
        return Scenario(
            bake,
            self.simulation_group.merge(other.simulation_group),
            self.rendering_group.merge(other.rendering_group)
        )

