from concurrent.futures import ThreadPoolExecutor
from collections import deque
from functools import wraps
from typing import Callable, Iterable, Protocol, TypeVar, get_args, get_origin
from q_engine.alt.ecs.components import World
from time import time

T = TypeVar('T')
type Write[T] = T

def query(fn: Callable):
    @wraps(fn)
    def wrapper(world: World) -> None:
        dependencies = fn.__annotations__.values()
        param_types = []
        arches = list(world.archetypes)
        for dependency in dependencies:
            if get_origin(dependency) is Write:
                dependency = get_args(dependency)[0]
            param_types.append(dependency)
            i = len(arches)
            while i > 0:
                arch = arches.pop(0)
                if dependency in arch.types:
                    arches.append(arch)
                i = i - 1
    
        for arch in arches:
            fn(*[arch.components[dep] for dep in param_types])
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

def schedule(batches: list[list[Callable]]):
    def tick(*args, **kwargs):
        for batch in batches:
            with ThreadPoolExecutor(max_workers=len(batch)) as ex:
                futures = [ex.submit(fn, *args, **kwargs) for fn in batch]
                for f in futures:
                    f.result()
    return tick

class System(Protocol):
    def __call__(self, world: World) -> None: ...
class SystemFactory(Protocol):
    def __call__(self, *a, **kw) -> System: ...

def aggregate(factories: list[SystemFactory]):
    def create(*fc_args, **fc_kwargs):
        systems = [fc(*fc_args, **fc_kwargs) for fc in factories]
        def tick(*tick_args, **tick_kwargs):
            for s in systems:
                s(*tick_args, **tick_kwargs)
        return tick
    return create

def assemble(
    bake: Callable, 
    simulate_fc: Callable,
    render_fc: Callable,
    dt: float
):
    world = World()
    bake(world)
    
    accumulator = 0.0
    last = None
    def tick(*args, **kwargs):
        nonlocal last
        nonlocal accumulator

        current = time()
        if last:
            accumulator += current - last
        last = current

        while accumulator > dt:
            simulate_fc(dt, *args, **kwargs)(world)
            accumulator -= dt
        
        render_fc(alpha=accumulator / dt, *args, **kwargs)(world)
    return tick

