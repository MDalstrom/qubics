from ecs.system import for_each
from ecs.world import World
from ecs.entity import Entity
from pygame import Surface, gfxdraw
from application.transform import Transform
from dataclasses import dataclass


@dataclass
class CircleRenderable:
    color: tuple[int, int, int]
    radius: float = 0.0


@for_each
def render(world: World, _: Entity, surface: Surface):
    @for_each
    def inner(_: World, __: Entity, renderable: CircleRenderable, transform: Transform):
        x, y = transform.get_interpolated_world_position(world.alpha)
        gfxdraw.filled_circle(
            surface, int(x), int(y), int(renderable.radius), renderable.color
        )
        gfxdraw.aacircle(
            surface, int(x), int(y), int(renderable.radius), renderable.color
        )

    inner(world)
