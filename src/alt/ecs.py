from concurrent.futures import ThreadPoolExecutor
from collections import deque
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Iterable, TypeVar, get_args, get_origin, Any, Protocol
import mlx.core as mx


class Component(Protocol):
    def add(self, i, size = 1): ...

@dataclass
class RenderingContext:
    device: Any
    encoder: Any
    buffer: Any

class Position:
    def __init__(self) -> None:
        self.x = mx.zeros(1, dtype=mx.float32)
        self.y = mx.zeros(1, dtype=mx.float32)

class Velocity:
    def __init__(self) -> None:
        self.x = mx.zeros(1, dtype=mx.float32)
        self.y = mx.zeros(1, dtype=mx.float32)

class Entity(int): ...

class Archetype:
    def __init__(self, component_types: list[type[Component]]) -> None:
        self.comps = component_types
        self.count = 0
        self.chunks = {
            component_type: component_type() for component_type in component_types
        }

    def create_entity(self) -> Entity:
        i = self.count
        for c in self.chunks.values():
            c.add(i)
        result = Entity(i)
        self.count = i + 1
        return result


@dataclass
class World:
    arches: list[Archetype]


T = TypeVar('T')
type Write[T] = T

def query(fn: Callable):
    @wraps(fn)
    def wrapper(world: World) -> None:
        dependencies = fn.__annotations__.values()
        param_types = []
        arches = list(world.arches)
        for dependency in dependencies:
            if get_origin(dependency) is Write:
                dependency = get_args(dependency)[0]
            param_types.append(dependency)
            i = len(arches)
            while i > 0:
                arch = arches.pop(0)
                if dependency in arch.comps:
                    arches.append(arch)
                i = i - 1
    
        for arch in arches:
            fn(*[arch.chunks[dep] for dep in param_types])
        return
    return wrapper

class SystemDesc():
    def __init__(self, reads: set[type], writes: set[type], fn: Callable) -> None:
        self.reads = reads
        self.writes = writes
        self.fn = fn

    @staticmethod
    def from_components(fn: Callable, comps: Iterable[type]):
        reads = set()
        writes = set()
        for comp in comps:
            if comp is World:
                continue
            elif get_origin(comp) is Write:
                comp = get_args(comp)[0]
                writes.add(comp)
            else:
                reads.add(comp)
        return SystemDesc(reads, writes, fn)
    
    @staticmethod
    def from_fn(fn: Callable):
        return SystemDesc.from_components(fn, fn.__annotations__.values())

    @staticmethod
    def from_wrapped(fn:Callable, source:Callable):
        return SystemDesc.from_components(fn, list(fn.__annotations__.values()) + list(source.__annotations__.values()))

    @staticmethod
    def resolve(a: 'SystemDesc', b: 'SystemDesc') -> bool: 
        return bool((a.writes & b.writes) or (a.writes & b.reads))
    

def build_batches(systems: list[SystemDesc], resolve: Callable) -> list[list[SystemDesc]]:
    edges: dict[SystemDesc, set[SystemDesc]] = {}
    indeg: dict[SystemDesc, int] = {}

    for s in systems:
        edges[s] = set()
        indeg[s] = 0

    for i, a in enumerate(systems):
        for b in systems[i + 1:]:
            if resolve(a, b):
                edges[a].add(b)
                indeg[b] += 1

    q = deque([u for u in systems if indeg[u] == 0])
    batches = []

    while q:
        batch = list(q)
        batches.append(batch)
        q.clear()

        for u in batch:
            for v in edges.get(u, ()):
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)
    
    return batches

def schedule(batches: list[list[SystemDesc]]):
    def tick(*args, **kwargs):
        for batch in batches:
            with ThreadPoolExecutor(max_workers=len(batch)) as ex:
                futures = [ex.submit(s.fn, *args, **kwargs) for s in batch]
                for f in futures:
                    f.result()
    return tick

def aggregate(systems: list[Callable]):
    def tick(*args, **kwargs):
        for system in systems:
            system(*args, **kwargs)
    return tick
