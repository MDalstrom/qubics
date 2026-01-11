from ecs.system import for_each
from ecs.world import World
from ecs.entity import Entity
from pygame import Surface, gfxdraw, Rect
from application.transform import Transform
from dataclasses import dataclass


@dataclass
class BoundsRenderable:
    size: tuple[int, int]
    color: tuple[int, int, int]


@for_each
def render(world: World, _: Entity, surface: Surface):
    @for_each
    def inner(_: World, __: Entity, bounds: BoundsRenderable, transform: Transform):
        x, y = transform.get_interpolated_world_position(world.alpha)
        rect = Rect(x, y, bounds.size[0], bounds.size[1])
        gfxdraw.rectangle(surface, rect, bounds.color)

    inner(world)
