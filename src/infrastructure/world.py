import inspect
from typing import Callable, get_type_hints
from domain import World, System


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
    return system
