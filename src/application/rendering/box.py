from application.math import Vector
from application.rendering.viewport import Viewport
from ecs.system import for_each
from ecs.world import World
from ecs.entity import Entity
from pygame import Surface, draw
from application.transform import Transform
from dataclasses import dataclass


@dataclass
class BoxRenderable:
    width: float
    height: float
    color: tuple[int, int, int]


@for_each
def render(world: World, _: Entity, viewport: Viewport):
    @for_each
    def inner(_: World, __: Entity, box: BoxRenderable, transform: Transform):
        matrix = transform.get_world_matrix()
        
        corners = [
            Vector(-box.width, -box.height),
            Vector(box.width, -box.height),
            Vector(box.width, box.height),
            Vector(-box.width, box.height)
        ]
        draw.polygon(viewport.surface, box.color, [(matrix @ corner).round() for corner in corners])
    
    inner(world)
