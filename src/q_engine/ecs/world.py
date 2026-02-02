from dataclasses import dataclass
from q_engine.units import Boolean
from q_engine.ecs.components import component, Component
from typing import TypeVar, cast


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

class Count(Component):
    def __init__(self) -> None:
        self.count = 0

    def __iter__(self):
        return range(self.count)

    def assert_exist(self, key: int | slice):
        if isinstance(key, int):
            key = slice(key, key+1)
        self.count = max(self.count, key.stop - 1)


C = TypeVar('C', bound=Component)
class Archetype:
    components: dict[type, Component]

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

