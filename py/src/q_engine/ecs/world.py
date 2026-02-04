from typing_extensions import Buffer
from q_generated.ecs.Count import Count
from q_generated.ecs.Removals import Removals
from dataclasses import dataclass
from typing import TypeVar, cast, Any, Dict, Type, Protocol


class Component(Protocol):
    def GetRootAs(buffer: Buffer, offset: int): ...

class Archetype(frozenset[Component]):
    pass

@dataclass(eq=False)
class Entity:
    chunk: "Chunk"
    index_in_chunk: int

    def __hash__(self):
        return hash((self.chunk, self.index_in_chunk))

    def __eq__(self, other):
        return isinstance(other, Entity) and self.chunk == other.chunk and self.index_in_chunk == other.index_in_chunk


C = TypeVar('C')
class Chunk:
    archetype: Archetype
    count: Count
    removals: Removals
    buffers: Dict[Type, bytearray]

    def __init__(self, archetype: Archetype, capacity: int = 16) -> None:
        self.archetype = archetype
        self.capacity = capacity

        self.buffers = {
            Count: self.count,
            Removals: self.removals
        }
   
    def next(self) -> int:
        i = self.count
        self.count += 1
        return i

    def get_component(self, component_type: type[Component]) -> Any:
        buffer = self.buffers[component_type]
        return component_type.GetRootAs(buffer, 0)


class World:
    chunks: list[Chunk]

    def __init__(self, capacity) -> None:
        empty_archetype = Archetype(set())
        self.chunks = []
        self.archetypes = [empty_archetype]
        self.capacity = capacity

    def create_entity(self, arch: Archetype) -> Entity:
        c = self._find_chunk(arch)
        i = c.next()
        print("tocheck", c)
        return Entity(c, i)

        
    def move_entity(self, e: Entity, new_arch: Archetype):
        c = self._find_chunk(new_arch)
        

    def _find_chunk(self, arch: Archetype):
        for c in self.chunks:
            if c.archetype != arch:
                continue
            if c.count >= c.capacity:
                continue
            return c

        return Chunk(arch, capacity=self.capacity)


