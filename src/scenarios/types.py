from dataclasses import dataclass
from ecs.system import SystemsGroup


@dataclass
class Scenario:
    bake: SystemsGroup
    simulation: SystemsGroup
    rendering: SystemsGroup

    def merge(self, other: "Scenario"):
        return Scenario(
            self.bake.merge(other.bake),
            self.simulation.merge(other.simulation),
            self.rendering.merge(other.rendering),
        )
