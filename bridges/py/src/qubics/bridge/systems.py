from __future__ import annotations
import ctypes as c
from typing import TypeAlias, Callable
from functools import wraps

from generated.ecs import ecs, scheduler
from qubics.bridge._lib import lib


class Component(c.Structure):
    pass


Archetype: TypeAlias = list[type[Component]]


class WorldApi:
    def __init__(self, world_addr: int):
        self._p = c.cast(world_addr, c.POINTER(ecs.World))

    def create_entity(self, archetype: ecs.Archetype) -> ecs.Entity:
        return lib.entity_create(self._p, archetype)

    def remove_entity(self, entity: ecs.Entity):
        lib.entity_remove(entity)


def system(reads: Archetype = [], writes: Archetype = []):
    def decorator(fn: Callable[[WorldApi], None]):
        @wraps(fn)
        def wrapped(registry_addr: int) -> int:
            registry_p = c.cast(registry_addr, c.POINTER(ecs.Registry))

            def resolve_or_register(component: type[Component]) -> c._Pointer[ecs.ComponentDescriptor]:
                reg = registry_p.contents
                for i in range(reg.count.value):
                    if reg.descriptors[i].contents.name.decode() == component.__name__:
                        return reg.descriptors[i]
                return lib.component_register(registry_p, c.sizeof(component), component.__name__.encode())

            def make_archetype(components: Archetype) -> tuple[ecs.Archetype, object]:
                arch = ecs.Archetype()
                if not components:
                    return arch, None
                ptrs = (c.POINTER(ecs.ComponentDescriptor) * len(components))(
                    *(resolve_or_register(comp) for comp in components)
                )
                arch.length.value = len(components)
                arch.descriptors = c.cast(ptrs, c.POINTER(c.POINTER(ecs.ComponentDescriptor)))
                return arch, ptrs

            system_fn = scheduler.SystemFn(lambda world_p, ctx: fn(WorldApi(world_p)))
            desc = scheduler.SystemDescriptor()
            desc.run = system_fn
            desc.reads, reads_ptrs = make_archetype(reads)
            desc.writes, writes_ptrs = make_archetype(writes)

            wrapped._system_fn = system_fn
            wrapped._descriptor = desc
            wrapped._reads_ptrs = reads_ptrs
            wrapped._writes_ptrs = writes_ptrs

            return desc
        return wrapped
    return decorator
