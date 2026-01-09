from domain import World
from .shared import create_bounds, create_background


def bake(world: World):
    bounds = create_bounds()
    world.add(bounds)

    background = create_background()
    world.add(background)

