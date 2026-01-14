from application.math import Vector
from application.rendering.viewport import Viewport
from ecs.system import for_each
from ecs.world import World
from ecs.entity import Entity
from pygame import draw
from application.transform import Transform
from dataclasses import dataclass


@dataclass
class LineRenderer:
    color: tuple[int, int, int]
    width: int = 1


@for_each
def render(world: World, _: Entity, viewport: Viewport):
    @for_each
    def inner(_: World, __: Entity, line_renderer: LineRenderer, transform: Transform):
        matrix = transform.get_interpolated_world_matrix(world.alpha)
        start = matrix @ Vector(-1, 0)
        end = matrix @ Vector(1, 0)
        x0, y0 = start.round()
        x1, y1 = end.round()

        draw.line(
            viewport.surface,
            line_renderer.color,
            (x0, y0),
            (x1, y1),
            line_renderer.width
        )
    
    inner(world)
