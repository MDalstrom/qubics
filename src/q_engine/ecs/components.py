import numpy as np
import numpy.typing as npt
from dataclasses import dataclass
from functools import partial
from typing import Callable, TypeVar, get_origin, get_args, Annotated


class ComponentMeta(type):
    def __new__(mcls, name, bases, attrs):
        is_shared = attrs.get('_is_shared', False)

        annotations = attrs.get('__annotations__', {})
        declarative_fields = {}
        for field_name, type_hint in annotations.items():
            origin = get_origin(type_hint)
            if origin is not None and origin is Annotated:
                config_tuple = get_args(type_hint)[1]
                declarative_fields[field_name] = config_tuple

        new_class = super().__new__(mcls, name, bases, attrs)
        new_class._fields = declarative_fields
        new_class._is_shared = is_shared

        if '__init__' not in attrs:
            def __init__(self):
                super(new_class, self).__init__()
                for field_name, (shape, dtype) in new_class._fields.items():
                    if new_class._is_shared:
                        setattr(self, field_name, None)
                    else:
                        instance_shape = (0,) + shape[1:]
                        setattr(self, field_name, np.zeros(instance_shape, dtype=dtype))
            new_class.__init__ = __init__

        if 'add' not in attrs:
            def add(self, entity_index, count=1):
                if new_class._is_shared:
                    return
                required_size = entity_index + count
                for field_name, (shape, dtype) in new_class._fields.items():
                    array = getattr(self, field_name)
                    if required_size > array.shape[0]:
                        to_add = required_size - array.shape[0]
                        new_items_shape = (to_add,) + array.shape[1:]
                        new_items = np.zeros(new_items_shape, dtype=dtype)
                        setattr(self, field_name, np.concatenate([array, new_items]))
            new_class.add = add

        if '__getitem__' not in attrs:
            def __getitem__(self, key):
                if new_class._is_shared:
                    return {name: getattr(self, name) for name in new_class._fields}
                if isinstance(key, int):
                    return {name: getattr(self, name)[key] for name in new_class._fields}
                elif isinstance(key, (slice, list, np.ndarray)):
                    return {name: getattr(self, name)[key] for name in new_class._fields}
                else:
                    raise TypeError(f"Component indices must be integers, slices, or lists, not {type(key).__name__}")
            new_class.__getitem__ = __getitem__

        for field_name, (shape, dtype) in new_class._fields.items():
            setattr(new_class, f'{field_name}_dtype', dtype)
            setattr(new_class, f'{field_name}_array', npt.NDArray[dtype])

        return new_class


class Component(metaclass=ComponentMeta): ...

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
