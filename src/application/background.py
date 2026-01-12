from dataclasses import dataclass
from pygame import Surface
from application.rendering.viewport import Viewport
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World


@dataclass
class Background:
    color: tuple[int, int, int]


@for_each
def fill_background(world: World, _: Entity, viewport: Viewport):
    @for_each
    def inner(_: World, __: Entity, background: Background):
        viewport.surface.fill(background.color)

    inner(world)
