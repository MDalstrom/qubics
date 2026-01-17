from functools import partial
from importlib import import_module
from os import wait
import threading
from time import sleep, time
from typing import Callable

from application import cleaner, physics
from application.duration import duration_system, Duration
from application import collisions
from application.collisions.components import CollisionMatrix
from application.transform import save_transform_state
from application.stats.systems import deal_damage

from color import Color
from infrastructure import cleanup
import rendering as metal

from ecs.entity import Entity
from ecs.system import SystemsGroup, factory
from ecs.world import World

from infrastructure.config import get_config

from scenarios.types import Scenario


_collision_layers = [("default", "default")]

def bake_collision_matrix(world: World):
    e = Entity("collisions")
    e.add_component(CollisionMatrix(_collision_layers))
    world.add(e)

@factory
def bake_duration(config=get_config()):
    duration = config['duration']

    def bake(duration: float, world: World):
        e = Entity("duration")
        e.add_component(Duration(duration))
        world.add(e)

    if duration:
        return partial(bake, duration)

def create_pool(create: Callable):
    lock = threading.Lock()
    buffers = []
    rented_count = [0]
    
    def release(buffer):
        with lock:
            buffers.append(buffer)
            rented_count[0] -= 1

    def rent():
        with lock:
            if len(buffers) == 0:
                result = create()
            else:
                result = buffers.pop(0)
            rented_count[0] += 1
            return result
    
    @cleanup.wait
    def finish():
        with lock:
            return rented_count[0] > 0
    cleanup.dependencies.append(finish)

    return rent, release

def get_base_scenario(config=get_config()) -> Scenario:
    metal_core = metal.get_scenario()
    metal_back = (
            metal.get_export(config['width'], config['height'], config['fps'], config['output'], Color(0.0, 0.0, 0.0, 0.05), create_pool)
            if config['output'] 
            else metal.get_interactive(config['width'], config['height'], Color(0.0, 0.0, 0.05))
    )
    application_scenario = Scenario(
        bake=SystemsGroup(
            [bake_duration, bake_collision_matrix],
            [],
            []
        ),
        simulation=SystemsGroup(
            [duration_system, save_transform_state],
            [*collisions.export, *physics.systems],
            [deal_damage, cleaner.system],
        ),
        rendering=SystemsGroup(
            [],
            [],
            [],
        ),
    )

    return (metal_core
        .merge(metal_back)
        .merge(application_scenario)
    )


def get_scenario(base=get_base_scenario(), config=get_config()) -> Scenario:
    module = import_module(f"scenarios.{config['scenario']}")
    scenario: Scenario = module.scenario
    return base.merge(scenario)
