from typing import TypeAlias
import ctypes as c

from generated import ecs
from qubics.bridge._lib import lib







def resolve_archetype(world: c._Pointer[ecs.World], archetype: Archetype) -> ecs.Archetype:
    c_archetype = ecs.Archetype()
    c_archetype.length = len(archetype)
    descriptors = (c.POINTER(ecs.ComponentDescriptor) * c_archetype.length)()
    for i, component in enumerate(archetype):
        descriptors[i] = resolve(world, type(component)) or register(world, component)
    c_archetype.descriptors = c.cast(descriptors, c.POINTER(c.POINTER(ecs.ComponentDescriptor)))
    return c_archetype
