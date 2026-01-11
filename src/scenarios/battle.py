from ecs.system import SystemsGroup
from ecs.world import World
from scenarios.shared import create_background, create_bounds
from scenarios.types import Scenario


def bake(world: World):
    for entity in create_bounds(450, 800, 375, 375):
        world.add(entity)
    world.add(create_background())


scenario = Scenario(bake, SystemsGroup([], [], []), SystemsGroup([], [], []))
