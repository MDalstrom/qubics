from dataclasses import dataclass
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World


@dataclass
class Duration:
    max_time: float
    elapsed: float = 0.0


@for_each
def duration_system(world: World, _: Entity, duration: Duration):
    duration.elapsed += world.timestep
    if duration.elapsed < duration.max_time:
        return
    raise KeyboardInterrupt
