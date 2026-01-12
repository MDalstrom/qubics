from application.math import Vector
from application.rendering.viewport import Viewport
from ecs.system import for_each
from ecs.world import World
from ecs.entity import Entity
from pygame import Surface, draw
from application.transform import Transform
from dataclasses import dataclass


@dataclass
class LineRenderer:
    half_length: float
    color: tuple[int, int, int]
    width: int = 1


@for_each
def render(world: World, _: Entity, viewport: Viewport):
    @for_each
    def inner(_: World, __: Entity, line_renderer: LineRenderer, transform: Transform):
        matrix = transform.get_world_matrix()
        start = matrix @ Vector(-line_renderer.half_length, 0)
        end = matrix @ Vector(line_renderer.half_length, 0)

        draw.line(
            viewport.surface,
            line_renderer.color,
            (int(start.x), int(start.y)),
            (int(end.x), int(end.y)),
            line_renderer.width
        )
    
    inner(world)
