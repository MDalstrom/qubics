from .shared import TestComponent
from q_ecs.types import WorldMethods
from q_engine.bootstrap import get_config
from q_ecs.c_bindings import mk_world_factory


def bake(world: WorldMethods):
    world.create_entity([TestComponent])
    world.create_entity([TestComponent])
    world.create_entity([TestComponent])
    world.create_entity([TestComponent])
    world.create_entity([TestComponent])

def get_tick(config = get_config()):
    world = mk_world_factory(config.ecslib)()
    bake(world)

    def tick(stdscr):
        stdscr.addstr("st")
        ...

    return tick

