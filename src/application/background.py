from dataclasses import dataclass
from pygame import Surface
from ecs.entity import Entity
from ecs.system import for_each
from ecs.world import World


@dataclass
class Background:
    color: tuple[int, int, int]


@for_each
def fill_background(world: World, _: Entity, surface: Surface):
    @for_each
    def inner(_: World, __: Entity, background: Background):
        surface.fill(background.color)

    inner(world)
