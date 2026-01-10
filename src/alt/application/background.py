from dataclasses import dataclass

from pygame import Surface, gfxdraw
import pygame
from domain import World, Entity
from components import Bounds, Transform, Rigidbody, Acceleration, Renderable
from infrastructure.world import for_each


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

@for_each
def bounds_render_system(world: World, _: Entity, surface: Surface):
    @for_each
    def inner(_: World, entity: Entity, bounds: Bounds):
        transform = entity.get_component(Transform)
        if transform:
            x, y = transform.get_interpolated_world_position(world.alpha)
            rect = bounds.rect.copy()
            rect.x = int(x)
            rect.y = int(y)
            gfxdraw.rectangle(surface, rect, bounds.color)
        else:
            gfxdraw.rectangle(surface, bounds.rect, bounds.color)
    inner(world)


@for_each
def renderable_system(world: World, _: Entity, surface: Surface):
    @for_each
    def inner(_: World, __: Entity, renderable: Renderable, transform: Transform):
        x, y = transform.get_interpolated_world_position(world.alpha)
        if renderable.shape == 'circle':
            gfxdraw.filled_circle(surface, int(x), int(y), int(renderable.radius), renderable.color)
            gfxdraw.aacircle(surface, int(x), int(y), int(renderable.radius), renderable.color)
    
    inner(world)

