from ecs.system import SystemsGroup
from ecs.world import World
from scenarios import battle
from scenarios.types import Scenario

from .shared import create_sphere, create_box


def bake(world: World):
    # sphere = create_sphere(
    #     x=450, y=900, radius=40, color=(100, 150, 255), vx=0, vy=-200
    # )
    # world.add(sphere)
    sphere = create_sphere(
        x=450, y=500, radius=300, color=(0, 255, 000), vx=0, vy=0
    )
    world.add(sphere)
    box = create_box(
        x=450, y=930, width=150, height=150, color=(50, 200, 50), vx=0, vy=0, angle=0.1
    )
    world.add(box)
    # box = create_box(
    #     x=500, y=600, width=30, height=30, color=(100, 150, 255), vx=0, vy=0, angle=0
    # )
    # world.add(box)

scenario = Scenario(bake, SystemsGroup([], [], []), SystemsGroup([], [], []))
scenario = battle.scenario.merge(scenario)
