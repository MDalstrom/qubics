from dataclasses import dataclass

from pygame import Surface
from ecs.world import World
from ecs.entity import Entity
from ecs.system import for_each
from application.transform import Transform
from application.physics import Rigidbody, Acceleration


@dataclass
class Background:
    color: tuple[int, int, int]


@for_each
def acceleration_system(world: World, _: Entity, rigidbody: Rigidbody, acceleration: Acceleration) -> None:
    rigidbody.vx += acceleration.ax * world.timestep
    rigidbody.vy += acceleration.ay * world.timestep


@for_each
def movement_system(world: World, _: Entity, transform: Transform, rigidbody: Rigidbody) -> None:
    transform.save_previous()
    wx, wy = transform.get_world_position()
    wx += rigidbody.vx * world.timestep
    wy += rigidbody.vy * world.timestep
    transform.set_world_position(wx, wy)

@for_each
def fill_background(world: World, _: Entity, surface: Surface):
    @for_each
    def inner(_: World, __: Entity, background: Background):
        surface.fill(background.color)
    inner(world)

