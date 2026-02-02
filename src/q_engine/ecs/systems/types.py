from typing import Protocol, TypeVar
from q_engine.ecs.world import World


T = TypeVar("T")
type Write[T] = T
Write = Write

class BakingSystem(Protocol):
    def __call__(self, world: World) -> None: ...

class RenderingSystem(Protocol):
    def __call__(self, world: World, alpha: float) -> None: ...

class SimulationSystem(Protocol):
    def __call__(self, world: World, dt: float) -> None: ...
