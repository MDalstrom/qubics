from typing import Protocol
from dataclasses import dataclass, field
from typing import TypeVar, cast

from pygame import Surface


T = TypeVar('T')


@dataclass
class EntityRef:
    index: int
    generation: int = 0

class Entity:
    def __init__(self):
        self._components: dict[object, object] = {}
    
    def add_component(self, component: object) -> None:
        component_type = type(component)
        self._components[component_type] = component
    
    def get_component(self, component_type: type[T]) -> T | None:
        component = self._components.get(component_type)
        if component is not None:
            return cast(T, component)
        return None
    
    def has_component(self, component_type: type) -> bool:
        return self.get_component(component_type) is not None

@dataclass
class World:
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
        return ref.generation == self._generation and 0 <= ref.index < len(self.entities)
    
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


class System(Protocol):
    def __call__(self, world: World) -> None:
        ...


class Renderer(Protocol):
    def __call__(self, context: 'RenderContext', entity: Entity) -> None:
        ...


class RenderContext:
    def __init__(self, surface: Surface, alpha: float = 1.0):
        self.surface = surface
        self.alpha = alpha
