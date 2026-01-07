from dataclasses import dataclass, field
from typing import TypeVar, cast, Callable


@dataclass
class EntityRef:
    index: int
    generation: int = 0


T = TypeVar('T')


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
    delta_time: float = field(default=0.0, init=False)
    
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


import inspect
from typing import get_type_hints

def for_each(entity_fn: Callable) -> Callable[[World], None]:
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
