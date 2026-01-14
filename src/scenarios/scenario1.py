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
        x=450, y=700, radius=40, color=(100, 150, 255), vx=0, vy=-90
    )
    world.add(sphere)
    box = create_box(
        x=400, y=600, width=30, height=30, color=(100, 150, 255), vx=0, vy=-100, angle=32
    )
    world.add(box)
    box = create_box(
        x=500, y=600, width=30, height=30, color=(100, 150, 255), vx=0, vy=-100, angle=0
    )
    world.add(box)

scenario = Scenario(bake, SystemsGroup([], [], []), SystemsGroup([], [], []))
scenario = battle.scenario.merge(scenario)
