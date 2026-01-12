from ecs.system import SystemsGroup
from ecs.world import World
from scenarios import battle
from scenarios.types import Scenario

from .shared import create_sphere, create_box


def bake(world: World):
    # sphere = create_sphere(
    #     x=200, y=800, radius=20, color=(100, 150, 255), vx=100, vy=100
    # )
    # world.add(sphere)
    #
    # sphere = create_sphere(
    #     x=100, y=800, radius=20, color=(100, 150, 255), vx=100, vy=100
    # )
    # world.add(sphere)
    #
    box = create_box(
        x=600, y=800, width=30, height=30, color=(100, 150, 255), vx=-40, vy=0, angle=43
    )
    world.add(box)
    box = create_box(
        x=300, y=800, width=30, height=30, color=(100, 150, 255), vx=40, vy=0, angle=43
    )
    world.add(box)

scenario = Scenario(bake, SystemsGroup([], [], []), SystemsGroup([], [], []))
scenario = battle.scenario.merge(scenario)
