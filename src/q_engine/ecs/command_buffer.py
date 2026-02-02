from typing import Callable, TypeVar
from q_engine.ecs.world import Entity, World
from q_engine.ecs.components import Component


class DeferredEntity(int): ...

C = TypeVar("C", bound=Component)
class CommandBuffer:
    def __init__(self) -> None:
        self._descriptors = []
        self._entities = []

    def create_entity(self) -> DeferredEntity:
        i = len(self._entities)
        result = DeferredEntity(i)
        self._entities.append(result)
        return result

    def add_component(self, e: DeferredEntity | Entity, t: type[Component]) -> None:
        self._descriptors.append(("add", e, t))

    def set_component(self, e: DeferredEntity | Entity, t: type[C], fn: Callable[[Entity, C], None]) -> None:
        self._descriptors.append(("set", e, t, fn))

    def remove_component(self, e: DeferredEntity | Entity, t: type[Component]) -> None:
        self._descriptors.append(("remove", e, t))

    def playback(self, world: World) -> list[Entity]:
        components: dict[Entity, set[type[Component]]] = {}

        resolved_entities = {e: world.create_entity() for e in self._entities}

        def resolve(e):
            return resolved_entities.get(e) or e

        set_ops = []
        for descriptor in self._descriptors:
            operation, e, *_ = descriptor
            e = resolve(e)
            if e not in components:
                components[e] = set(e.archetype.types)

            if operation == "add":
                components[e].add(descriptor[2])
            elif operation == "remove":
                components[e].discard(descriptor[2])
            elif operation == "set":
                set_ops.append(descriptor)

        for entity, types in components.items():
            world.move_entity(entity, types)

        for _, e, t, fn in set_ops:
            entity = resolve(e)
            fn(entity, entity.archetype.components[t])

        return list(resolved_entities.values())

