from dataclasses import dataclass
from typing import Protocol
import numpy as np


class Component(Protocol):
    def add(self, i, size = 1): ...

@dataclass
class Entity():
    archetype: "Archetype"
    index: int

class Removed(Component):
    def __init__(self) -> None:
        self.flags = np.zeros(0, dtype=np.int8)

    def add(self, i, size=1):
        if i + size >= np.size(self.flags):
            self.flags = np.concat([ 
                self.flags, 
                np.zeros(size // 8 + 1 if size % 8 > 0 else 0, dtype=np.int8)
            ])

    def __getitem__(self, e: int) -> bool:
        i = e // 8
        mask = 1 << (i % 8)
        return self.flags[i] & mask

    def __setitem__(self, e: int, value: bool):
        i = e // 8
        mask = 1 << (i % 8)
        self.flags[i] = (self.flags[i] & ~mask) | (value & mask)

class Archetype:
    def __init__(self, component_types: set[type[Component]]) -> None:
        self.types = component_types
        self.entities_count = 0
        self.components = {
            component_type: component_type()
            for component_type in [*component_types, Removed]
        }

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
        self.archetypes: list[Archetype] = [empty_archetype]
        self.create_entity = empty_archetype.create_entity

    def add_component(self, e: Entity, t: set[type[Component]]):
        cur_a = e.archetype
        for a in self.archetypes:
            if a is cur_a:
                continue
            if (a.types - cur_a.types) == t:
                new_a = a
                break
        else:
            new_a = Archetype(cur_a.types.union(t))
            self.archetypes.append(new_a)

        e.archetype = new_a
        e.archetype = new_a
        removals: Removed = cur_a.components[Removed]
        removals[e.index] = True
        e.index = new_a.create_entity().index

