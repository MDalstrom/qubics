from application.rendering.viewport import Viewport
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
def render(world: World, _: Entity, viewport: Viewport):
    @for_each
    def inner(_: World, __: Entity, renderable: CircleRenderable, transform: Transform):
        x, y = transform.get_interpolated_world_position(world.alpha)
        x = min(max(x, -32768), 32767)
        y = min(max(y, -32768), 32767)
        gfxdraw.filled_circle(
            viewport.surface, int(x), int(y), int(renderable.radius), renderable.color
        )
        gfxdraw.aacircle(
            viewport.surface, int(x), int(y), int(renderable.radius), renderable.color
        )

    inner(world)
