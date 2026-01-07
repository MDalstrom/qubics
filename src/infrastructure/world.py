from dataclasses import dataclass, field
from typing import TypeVar, cast, Callable


@dataclass
class EntityRef:
    index: int
    generation: int = 0


T = TypeVar('T')


_component_registry: dict[type, str] = {}


def register_component_type(component_type: type, key: str | None = None) -> None:
    if key is None:
        key = component_type.__name__
    _component_registry[component_type] = key


class Entity:
    
    def __init__(self):
        self._components: dict[str, object] = {}
    
    def add_component(self, component: object, key: str | None = None) -> None:
        component_type = type(component)
        if key is None:
            key = component_type.__name__
        
        self._components[key] = component
        
        if component_type not in _component_registry:
            register_component_type(component_type, key)
    
    def get_component(self, component_type: type[T]) -> T | None:
        key = _component_registry.get(component_type)
        if key and key in self._components:
            return cast(T, self._components[key])
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


def create_world() -> World:
    return World()


def for_each(*component_types: type) -> Callable[[Callable[[World, Entity], None]], Callable[[World], None]]:
    def decorator(entity_fn: Callable[[World, Entity], None]) -> Callable[[World], None]:
        def system(world: World) -> None:
            for entity in world.query(*component_types):
                entity_fn(world, entity)
        return system
    return decorator
