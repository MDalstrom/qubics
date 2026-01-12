from typing import TypeVar, cast
from dataclasses import dataclass


T = TypeVar("T")


@dataclass
class EntityRef:
    index: int
    generation: int = 0


class Entity:
    def __init__(self, name: str | None = None):
        self.name = name
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

    def __str__(self) -> str:
        return f'Entity({self.name or id(self)})'
