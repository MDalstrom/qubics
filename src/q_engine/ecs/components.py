from dataclasses import dataclass
from functools import partial
from typing import Callable, ParamSpec, Protocol, TypeVar
import numpy as np


class Component(Protocol):
    def add(self, i: int, size: int = 1): ...

@dataclass(eq=False)
class Entity():
    archetype: "Archetype"
    index: int

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other

class Removed(Component):
    def __init__(self) -> None:
        self.flags = np.zeros(0, dtype=np.uint8)

    def add(self, i: int, size: int = 1):
        if i + size >= np.size(self.flags):
            self.flags = np.concatenate([ 
                self.flags, 
                np.zeros(size // 8 + 1 if size % 8 > 0 else 0, dtype=np.uint8)
            ])

    def __getitem__(self, e: int) -> bool:
        i = e // 8
        mask = 1 << (e % 8)
        return bool(self.flags[i] & mask)

    def __setitem__(self, e: int, value: bool):
        i = e // 8
        mask = 1 << (e % 8)
        if value:
            self.flags[i] |= mask
        else:
            self.flags[i] &= ~mask

class Count(Component):
    def __init__(self) -> None:
        self.count = 0
    
    def __iter__(self):
        return range(self.count)

    def add(self, i: int, size: int = 1):
        self.count = max(self.count, i+size)

class Archetype:
    def __init__(self, component_types: set[type[Component]]) -> None:
        self.components = {
            ct: ct() for ct in [*component_types, Removed, Count]
        }
    
    @property
    def types(self):
        return self.components.keys()

    def create_entity(self) -> Entity:
        i = self.components[Count].count
        for c in self.components.values():
            c.add(i)
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

        removals: Removed = current_archetype.components[Removed]
        removals[e.index] = True
        new_entity = new_a.create_entity()
        
        e.archetype = new_a
        e.index = new_entity.index

class DeferredEntity(int): ...

C = TypeVar('C', bound=Component)
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
        self._descriptors.append(('add', e, t))

    def set_component(self, e: DeferredEntity | Entity, t: type[C], fn: Callable[[Entity, C], None]) -> None:
        self._descriptors.append(('set', e, t, fn))
    
    @staticmethod
    def set_deferred(cb: 'CommandBuffer', e: DeferredEntity | Entity, t: type[C]) -> Callable[[Callable[[Entity, C], None]], None]:
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

            if operation == 'add':
                components[e].add(descriptor[2])
            elif operation == 'remove':
                components[e].discard(descriptor[2])
            elif operation == 'set':
                set_ops.append(descriptor)

        for entity, types in components.items():
            world.move_entity(entity, types)

        for _, e, t, fn in set_ops:
            entity = resolve(e)
            fn(entity, entity.archetype.components[t])

        return list(resolved_entities.values())

