from pygame import Rect
from alt.application.background import Background
from domain import Entity
from components import Bounds


def create_background():
    entity = Entity()
    entity.add_component(Background((255, 255, 255)))
    return entity

def create_bounds():
    entity = Entity()
    entity.add_component(Bounds(Rect(50, 50, 300, 600), (0, 0, 0)))
    return entity
