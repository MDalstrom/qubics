from q_engine.ecs.systems.types import Write
from q_engine.ecs.world import World
from functools import wraps
from typing import Callable, get_args, get_origin


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
            fn(*[arch.components[param_type] for param_type in param_types])
        return

    return wrapper
