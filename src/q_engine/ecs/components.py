import numpy as np
from dataclasses import dataclass
from functools import partial
from q_engine.ecs.types import Boolean
from typing import (
    Callable,
    TypeVar,
    cast,
    Protocol, get_type_hints,
)


T = TypeVar('T', bound=type)
class Component(Protocol):
    def __getitem__(self: T, key: int | slice) -> T: ...
    def assert_exist(self, key: int | slice): ...

def component(cls: T):
    fields = []
    
    for name, hint in get_type_hints(cls).items():
        if hasattr(hint, '__dtype__') and hasattr(hint, '__shape__'):
            fields.append((name, hint.__shape__, hint.__dtype__))

    def __init__(self):
        for name, shape, dtype in fields:
            setattr(self, name, np.zeros([1, *shape], dtype=dtype))
    setattr(cls, "__init__", __init__)

    def __getitem__(self, key: int | slice):
        if isinstance(key, int):
            key = slice(key, key + 1)
        view = cls()
        for name, _, dtype in fields:
            arr: np.ndarray = getattr(self, name)
            setattr(view, name, arr[key])
        return view
    setattr(cls, "__getitem__", __getitem__)

    def assert_exist(self, key: int | slice):
        if isinstance(key, int):
            key = slice(key, key + 1)

        for name, _, dtype in fields:
            arr: np.ndarray = getattr(self, name)

            if arr.shape[0] == 0:
                arr = np.zeros([1, *arr.shape[1:]], dtype=dtype)
                setattr(self, name, arr)

            while key.stop - 1 >= arr.shape[0]:
                arr = np.concat([arr, arr], dtype=dtype)
                setattr(self, name, arr)
    setattr(cls, "assert_exist", assert_exist)

    return cls

@dataclass(eq=False)
class Entity:
    archetype: "Archetype"
    index: int

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other


@component
class Removed(Component):
    values: Boolean

class Count():
    def __init__(self) -> None:
        self.count = 0

    def __iter__(self):
        return range(self.count)

    def assert_exist(self, entity_index: int | slice):
        if isinstance(entity_index, int):
            entity_index = slice(entity_index, entity_index+1)
        self.count = max(self.count, entity_index.stop - 1)


C = TypeVar('C', bound=object)
class Archetype:
    def __init__(self, component_types: set[type[Component]]) -> None:
        self.components = {ct: ct() for ct in [*component_types, Removed, Count]}

    @property
    def types(self):
        return self.components.keys()

    def create_entity(self) -> Entity:
        i = cast(Count, self.components[Count]).count
        for c in self.components.values():
            c.assert_exist(i)
        cast(Count, self.components[Count]).count = i + 1
        result = Entity(self, i)
        return result


class World:
    def __init__(self) -> None:
        empty_archetype = Archetype(set())
        self.archetypes = [empty_archetype]
        self.create_entity = empty_archetype.create_entity

    def move_entity(self, e: Entity, new_types: set[type[Component]]):
        current_archetype = e.archetype
        if current_archetype.types == new_types:
            return

        for a in self.archetypes:
            if a.types == new_types:
                new_a = a
                break
        else:
            new_a = Archetype(new_types)
            self.archetypes.append(new_a)

        removals: Removed = cast(Removed, current_archetype.components[Removed])

        removals.values[e.index] = True
        new_entity = new_a.create_entity()

        e.archetype = new_a
        e.index = new_entity.index


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

    def set_component(
        self, e: DeferredEntity | Entity, t: type[C], fn: Callable[[Entity, C], None]
    ) -> None:
        self._descriptors.append(("set", e, t, fn))

    @staticmethod
    def set_deferred(
        cb: "CommandBuffer", e: DeferredEntity | Entity, t: type[C]
    ) -> Callable[[Callable[[Entity, C], None]], None]:
        return partial(cb.set_component, e, t)

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

