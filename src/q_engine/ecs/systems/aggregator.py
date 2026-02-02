from typing import Callable
from q_engine.ecs.world import World
from time import time


def assemble(bake: Callable, simulate_fc: Callable, render_fc: Callable, dt: float):
    world = World()
    bake(world)

    accumulator = 0.0
    last = None

    def tick():
        nonlocal last
        nonlocal accumulator

        current = time()
        if last:
            accumulator += current - last
        last = current

        while accumulator > dt:
            simulate_fc(dt)(world)
            accumulator -= dt

        render_fc(alpha=accumulator / dt)(world)

    return tick

def aggregate(factories: list):
    def create(*fc_args, **fc_kwargs):
        systems = [fc(*fc_args, **fc_kwargs) for fc in factories]

        def tick(*tick_args, **tick_kwargs):
            for s in systems:
                s(*tick_args, **tick_kwargs)

        return tick

    return create
