from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Protocol
import numpy as np


class Component(Protocol):
    def add(self, i: int, size: int = 1): ...

@dataclass
class Entity():
    archetype: "Archetype"
    index: int

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
        i = self.entities_count
        for c in self.components.values():
            c.add(i)
        result = Entity(self, i)
        self.entities_count = i + 1
        return result

class World:
    def __init__(self) -> None:
        empty_archetype = Archetype(set())
        self.archetypes = [empty_archetype]
        self.create_entity = empty_archetype.create_entity

    def move_entity(self, e: Entity, new_types: set[type[Component]]):
        current_archetype = e.archetype
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

class DeferredEntity(int):
    @lru_cache(None)
    def playback(self, world: World) -> Entity:
        return world.create_entity()

class CommandBuffer:
    def __init__(self) -> None:
        self._ops = []
        self._entities = []

    def create_entity(self) -> DeferredEntity:
        i = len(self._entities)
        result = DeferredEntity(i)
        self._entities.append(result)
        return result

    def add_component(self, e: DeferredEntity | Entity, t: type[Component]) -> None:
        self._ops.append(('add', e, t))

    def set_component(self, e: DeferredEntity | Entity, t: type[Component], fn: Callable[[Entity, Component],]) -> None:
        self._ops.append(('set', e, t, fn))
    
    def remove_component(self, e: DeferredEntity | Entity, t: type[Component]) -> None:
        self._ops.append(("remove", e, t))

    def playback(self, world: World): 
        components: dict[Entity, set[type[Component]]] = {}

        for op, e, *args in self._ops:
            if e is DeferredEntity:
                e = e.playback(world)
            if e not in components:
                components[e] = set(e.archetype.types)

            if op == 'add':
                t, = args
                components[e].add(t)
            elif op == 'remove':
                t, = args
                components[e].remove(t)
        
        for e, types in components.items():
            world.move_entity(e, types)

        for op, e, t, fn in self._ops :
            if op != 'set':
                continue
            fn(e.playback(world), e.archetype[t])

