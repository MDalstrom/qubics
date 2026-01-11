from dataclasses import dataclass, field
from typing import TypeVar
from ecs.entity import Entity, EntityRef


T = TypeVar("T")


@dataclass
class World:
    timestep: float
    dt: float = 0.0
    alpha: float = 0.0
    entities: list[Entity] = field(default_factory=list)

    _generation: int = field(default=0, init=False)

    def add(self, entity: Entity) -> EntityRef:
        index = len(self.entities)
        self.entities.append(entity)
        return EntityRef(index, self._generation)

    def get_entity(self, ref: EntityRef) -> Entity | None:
        if not self.validate(ref):
            return None
        return self.entities[ref.index]

    def get_component(self, ref: EntityRef, component_type: type[T]) -> T | None:
        entity = self.get_entity(ref)
        if not entity:
            return None
        return entity.get_component(component_type)

    def validate(self, ref: EntityRef) -> bool:
        return ref.generation == self._generation and 0 <= ref.index < len(
            self.entities
        )

    def rebuild_indices(self) -> None:
        self._generation += 1

    def query_one(self, component_type: type[T]) -> T | None:
        result = None
        for entity in self.entities:
            result = entity.get_component(component_type)
            if result:
                break
        return result

    def query(self, *component_types: type) -> list[Entity]:
        result = []
        for entity in self.entities:
            if all(entity.has_component(ct) for ct in component_types):
                result.append(entity)
        return result

    def __iter__(self):
        return iter(self.entities)

    def __getitem__(self, index: int) -> Entity:
        return self.entities[index]

    def __str__(self) -> str:
        return f'{", \n".join([str(e) for e in self.entities])}'
