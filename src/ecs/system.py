from dataclasses import dataclass
from typing import Protocol, Callable, get_type_hints
import inspect
from functools import update_wrapper
from ecs.world import World


class System(Protocol):
    def __call__(self, world: World) -> None: ...


@dataclass
class SystemsGroup:
    pre: list[System]
    act: list[System]
    post: list[System]

    def merge(self, other: "SystemsGroup") -> "SystemsGroup":
        return SystemsGroup(
            pre=[*self.pre, *other.pre],
            act=[*self.act, *other.act],
            post=[*self.post, *other.post],
        )

    def __call__(self, world: World) -> None:
        for system in [*self.pre, *self.act, *self.post]:
            system(world)


def for_each(entity_fn: Callable) -> System:
    sig = inspect.signature(entity_fn)
    params = list(sig.parameters.values())[2:]  # skip world, entity
    type_hints = get_type_hints(entity_fn)
    component_types = [type_hints[p.name] for p in params]

    def system(world: World) -> None:
        for entity in world.entities:
            components = []
            for ct in component_types:
                comp = entity.get_component(ct)
                if comp is None:
                    break
                components.append(comp)
            else:
                entity_fn(world, entity, *components)

    @dataclass
    class Wrapper:
        def __init__(self, fn: Callable, system_fn: Callable):
            self._fn = fn
            self._system = system_fn
            update_wrapper(self, fn)

        def __call__(self, world: World) -> None:
            return self._system(world)

        def __str__(self) -> str:
            return str(self._fn)

    return Wrapper(entity_fn, system)
