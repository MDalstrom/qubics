from application.math import Vector, get_corners
from application.rendering.viewport import Viewport
from ecs.system import for_each
from ecs.world import World
from ecs.entity import Entity
from pygame import draw
from application.transform import Transform
from dataclasses import dataclass


@dataclass
class BoxRenderable:
    color: tuple[int, int, int]


@for_each
def render(world: World, _: Entity, viewport: Viewport):
    @for_each
    def inner(_: World, __: Entity, box: BoxRenderable, transform: Transform):
        matrix = transform.get_interpolated_world_matrix(world.alpha)
        local_corners = get_corners(Vector.identity())
        world_corners = [matrix @ corner for corner in local_corners]
        rounded_corners = [corner.round() for corner in world_corners]
        draw.polygon(viewport.surface, box.color, rounded_corners)
    
    inner(world)
