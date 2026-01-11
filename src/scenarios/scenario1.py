from application.display import Duration
from ecs.system import SystemsGroup
from scenarios.types import Scenario
from infrastructure.config import get_config
from ecs.entity import Entity
from ecs.world import World
from .shared import create_bounds, create_background, create_sphere

config = get_config()


def bake(world: World):
    bounds = create_bounds()
    world.add(bounds)

    background = create_background()
    world.add(background)

    sphere = create_sphere(
        x=200, y=100, radius=20, color=(100, 150, 255), vx=100, vy=100
    )
    world.add(sphere)

    duration = Entity()
    duration.add_component(Duration(config["duration"]))
    world.add(duration)


scenario = Scenario(bake, SystemsGroup([], [], []), SystemsGroup([], [], []))
