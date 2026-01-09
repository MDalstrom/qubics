from dataclasses import dataclass

from pygame import Surface, gfxdraw
from domain import World, Entity
from components import Bounds, Transform, Rigidbody
from infrastructure.world import for_each


@dataclass
class Background:
    color: tuple[int, int, int]


@for_each
def movement_system(world: World, _: Entity, transform: Transform, rigidbody: Rigidbody) -> None:
    wx, wy = transform.get_world_position()
    wx += rigidbody.vx * world.delta_time
    wy += rigidbody.vy * world.delta_time
    transform.set_world_position(wx, wy)

def fill_background(world: World):
    background = world.query_one(Background)
    surface = world.query_one(Surface)
    if not background: return
    if not surface: return

    surface.fill(background.color)

@for_each
def bounds_render_system(world: World, _: Entity, surface: Surface):
    @for_each
    def inner(_: World, __: Entity, bounds: Bounds):
        gfxdraw.rectangle(surface, bounds.rect, bounds.color)
    inner(world)
